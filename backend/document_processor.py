import fitz  # PyMuPDF
import nltk
from nltk.tokenize import sent_tokenize
from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import google.generativeai as genai
from typing import List, Tuple
import os
from dotenv import load_dotenv
import time
from database import check_api_usage, update_api_usage
from paddleocr import PaddleOCR
import cv2
import numpy as np
import logging
import re
from gemini_monitoring import rouge_score, meteor_score_gauge
from rouge import Rouge
from nltk.translate.meteor_score import meteor_score

logger = logging.getLogger(__name__)

load_dotenv()

nltk.download('punkt')

GEMINI_API_KEY_1 = os.getenv("GEMINI_API_KEY_1")
genai.configure(api_key=GEMINI_API_KEY_1)
model_1 = genai.GenerativeModel('gemini-1.5-pro')

GEMINI_API_KEY_2 = os.getenv("GEMINI_API_KEY_2")
genai.configure(api_key=GEMINI_API_KEY_2)
model_2 = genai.GenerativeModel('gemini-1.5-pro')

tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
embedding_model = AutoModel.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')

# Initialize PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=False)  # Set use_gpu=True if you have GPU

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF file including text from images."""
    doc = fitz.open(pdf_path)
    text = ""
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Extract regular text
        text += page.get_text()
        
        # Extract text from images
        image_list = page.get_images(full=True)
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            
            # Convert image bytes to numpy array
            nparr = np.frombuffer(image_bytes, np.uint8)
            img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Perform OCR on the image
            try:
                result = ocr.ocr(img_np, cls=True)
                if result and len(result) > 0:
                    for line in result[0]:
                        text += line[1][0] + "\n"  
            except Exception as e:
                logger.error(f"Error processing image on page {page_num + 1}: {str(e)}")
                continue
    
    doc.close()
    return text

def chunk_text(text: str, chunk_size: int = 500) -> List[str]:
    """Split text into chunks based on sentences."""
    sentences = sent_tokenize(text)
    chunks = []
    current_chunk = []
    current_size = 0
    
    for sentence in sentences:
        sentence_size = len(sentence.split())
        if current_size + sentence_size > chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = [sentence]
            current_size = sentence_size
        else:
            current_chunk.append(sentence)
            current_size += sentence_size
    
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks

def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for text chunks using MiniLM model."""
    embeddings = []
    with torch.no_grad():
        for text in texts:
            inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
            outputs = embedding_model(**inputs)
            # Use mean pooling
            attention_mask = inputs["attention_mask"]
            token_embeddings = outputs.last_hidden_state
            input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
            embedding = torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)
            embeddings.append(embedding[0].numpy().tolist())
    return embeddings

def get_similar_chunks(query: str, document_chunks: List[str], document_embeddings: List[List[float]], top_k: int = 5) -> List[str]:
    """Find most similar chunks to the query using cosine similarity."""
    query_embedding = generate_embeddings([query])[0]
    similarities = cosine_similarity([query_embedding], document_embeddings)[0]
    top_indices = np.argsort(similarities)[-top_k:][::-1]
    return [document_chunks[i] for i in top_indices]

def generate_summary(text: str, user_id: str) -> Tuple[bool, str]:
    """Generate summary using Gemini with rate limiting."""
    can_proceed, message = check_api_usage(user_id)
    if not can_proceed:
        return False, message
    
    prompt = f"""Bạn là một trợ lý AI chuyên về các văn bản pháp luật và pháp lý như là bộ luật, hợp đồng, nội quy, thể lệ, điều khoản và điều kiện sử dụng... Hãy tóm tắt **ngữ cảnh được cung cấp** bên dưới một cách chính xác nhất có thể.

    Cung cấp một bản tóm tắt tổng quan giúp người đọc nắm được các thông tin quan trọng của văn bản pháp lý, pháp luật dưới đây. Bản tóm tắt phải ngắn gọn và cung cấp đầy đủ các thông tin cơ bản của tài liệu pháp lý/pháp luật. Không dùng lời mở đầu. 

    Văn bản pháp lý/pháp luật:
    {text}
    """
    response = model_2.generate_content(prompt)
    
    # Update metrics with the original text as reference
    try:
        rouge_scorer = Rouge()
        rouge_scores = rouge_scorer.get_scores(response.text, text)[0]
        rouge_l = rouge_scores['rouge-l']['f']
        meteor = meteor_score([text.split()], response.text.split())
        
        rouge_score.set(rouge_l)
        meteor_score_gauge.set(meteor)
    except Exception as e:
        print(f"Error calculating metrics: {e}")
    
    return True, response.text

def extract_clauses(text:str, user_id: str) -> Tuple[bool, List[str]]:
    """Generate summaries for each paragraph with rate limiting."""
    # summaries = []
    # for chunk in chunks:
    #     can_proceed, message = check_api_usage(user_id)
    #     if not can_proceed:
    #         return False, summaries, message
        
    #     success, summary = generate_summary(chunk, user_id)
    #     if not success:
    #         return False, summaries, summary
    #     summaries.append(summary)
    
    # return True, summaries, ""

    can_proceed, message = check_api_usage(user_id)
    if not can_proceed:
        return False, message
    
    prompt = f"""Bạn là một trợ lý AI chuyên về các văn bản pháp luật và pháp lý như là bộ luật, hợp đồng, nội quy, thể lệ, điều khoản và điều kiện sử dụng... Hãy tóm tắt **ngữ cảnh được cung cấp** bên dưới một cách chính xác nhất có thể.

    Cung cấp tóm tắt trong các gạch đầu dòng được lồng trong tiêu đề theo dạng XML cho từng phần. Ví dụ:

    <Cac_ben_lien_quan>
    - Bên cho thuê lại: [Tên]
    // Thêm thông tin chi tiết khi cần
    </Cac_ben_lien_quan>

    Nếu bất kỳ thông tin nào không được nêu rõ trong tài liệu, hãy ghi chú là "Không nêu rõ". Không sử dụng lời mở đầu trong phản hồi.

    Văn bản pháp lý:
    {text}
    """
    response = model_1.generate_content(prompt)
    pattern = r'</\w+>'
    tags = re.findall(pattern, response.text)
    tags.append("```xml")
    tags.append("```")
    pattern = '|'.join(map(re.escape, tags))
    clauses = re.split(pattern, response.text)
    clause_list = list()
    clause_type = list()
    for i in range(len(clauses)):
        pattern = ['\n', '<', '>']
        pattern = '|'.join(pattern)
        clauses[i] = re.split(pattern, clauses[i])
        clauses[i] = [clause for clause in clauses[i] if clause != '']
        if clauses[i]: 
            clause_type.append(clauses[i][0])
            clause_dict = dict()
            clause_dict["title"] = clauses[i][0].replace('_',' ')
            clause_dict["content"] = '\n'.join(clauses[i][1:])
            #clause_dict = {clauses[i][0].replace('_',' '): clauses[i][1:]}
            clause_list.append(clause_dict)

    can_proceed, message = check_api_usage(user_id)
    if not can_proceed:
        return False, message
    clause_type = '\n'.join(clause_type)

    prompt_2 = f"""Bạn là một trợ lý AI chuyên về xử lý ngôn ngữ tiếng Việt. Hãy **thêm dấu cho các từ tiếng Việt** bên dưới.

    Các từ đã thêm dấu được lồng trong tiêu đề theo dạng XML. Ví dụ:

    <Cac_ben_lien_quan>
    Các bên liên quan 
    </Cac_ben_lien_quan>

    Không sử dụng lời mở đầu trong phản hồi.

    Danh sách các từ không có dấu cần được thêm dấu:
    {clause_type}
    """
    response_2 = model_1.generate_content(prompt_2)
   
    pattern = r'</\w+>'
    tags = re.findall(pattern, response_2.text)
    tags.append("```xml")
    tags.append("```")
    tags.append('\n')
    pattern = r'<\w+>'
    tags_2 = re.findall(pattern, response_2.text)
    
    pattern = '|'.join(map(re.escape, tags + tags_2))
    clause_type = re.split(pattern, response_2.text)
    clause_type = [ct for ct in clause_type if ct != '']

    for d, ct in zip(clause_list, clause_type):
        d["title"] = ct 
    #clause_list = [{k: list(d.values())[0]} for k, d in zip(clause_type, clause_list)]

    update_api_usage(user_id)
    return True, clause_list

def generate_chat_response(query: str, context_chunks: List[str], user_id: str) -> Tuple[bool, str]:
    """Generate chat response using Gemini with context and rate limiting."""
    can_proceed, message = check_api_usage(user_id)
    if not can_proceed:
        return False, message
    
    context = "\n".join(context_chunks)
    prompt = f"""
    Bạn là một trợ lý AI chuyên về pháp luật Việt Nam. Chỉ sử dụng **ngữ cảnh được cung cấp** bên dưới để trả lời câu hỏi của người dùng một cách chính xác nhất có thể.

    --- NGỮ CẢNH (trích từ văn bản pháp luật) ---
    {context}
    ---------------------------------------------

    Trả lời câu hỏi bên dưới **dựa hoàn toàn vào ngữ cảnh trên**. Nếu câu hỏi không được đề cập rõ ràng trong ngữ cảnh, hãy nêu rõ rằng nội dung đó không có trong tài liệu.

    Nếu câu hỏi đề cập đến quy định pháp luật liên quan nhưng không có trong ngữ cảnh, bạn có thể gợi ý người dùng tra cứu trên cổng thông tin pháp luật chính thức: https://thuvienphapluat.vn/

    --- CÂU HỎI ---
    {query}

    --- HƯỚNG DẪN ---
    - **Tuyệt đối không bịa đặt** quy định hoặc thông tin pháp luật.
    - Nếu câu trả lời có thể được tìm thấy trong ngữ cảnh, hãy trích dẫn hoặc diễn giải lại một cách chính xác.
    - Nếu nội dung nằm ngoài phạm vi của ngữ cảnh, hãy nêu rõ điều đó.
    - Chỉ đề cập đến https://thuvienphapluat.vn nếu cần gợi ý tra cứu thêm.

    **Chỉ trả lời bằng tiếng Việt**. Ghi câu trả lời bên dưới:
    """


    response = model_2.generate_content(prompt)
    update_api_usage(user_id)
    return True, response.text 