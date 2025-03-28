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

# Load environment variables
load_dotenv()

# Download required NLTK data
nltk.download('punkt')

# Initialize Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# Initialize MiniLM model for embeddings
tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
embedding_model = AutoModel.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF file."""
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
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
    
    prompt = f"Please provide a concise summary of the following legal document:\n\n{text}"
    response = model.generate_content(prompt)
    update_api_usage(user_id)
    return True, response.text

def generate_paragraph_summaries(chunks: List[str], user_id: str) -> Tuple[bool, List[str], str]:
    """Generate summaries for each paragraph with rate limiting."""
    summaries = []
    for chunk in chunks:
        can_proceed, message = check_api_usage(user_id)
        if not can_proceed:
            return False, summaries, message
        
        success, summary = generate_summary(chunk, user_id)
        if not success:
            return False, summaries, summary
        summaries.append(summary)
    
    return True, summaries, ""

def generate_chat_response(query: str, context_chunks: List[str], user_id: str) -> Tuple[bool, str]:
    """Generate chat response using Gemini with context and rate limiting."""
    can_proceed, message = check_api_usage(user_id)
    if not can_proceed:
        return False, message
    
    context = "\n".join(context_chunks)
    prompt = f"Based on the following context from a legal document, please answer the question:\n\nContext:\n{context}\n\nQuestion: {query}"
    response = model.generate_content(prompt)
    update_api_usage(user_id)
    return True, response.text 