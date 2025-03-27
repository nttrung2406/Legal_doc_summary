# Legal Document Summarizer

A Streamlit application for summarizing legal documents using AI. The application allows users to upload PDF documents, view them, and get AI-generated summaries and insights.

## Features

- User authentication (signup/login)
- PDF document upload and storage
- Document viewing with original text display
- AI-powered document summarization
- Paragraph-by-paragraph summaries
- Interactive chat with document content

## Prerequisites

- Python 3.8 or higher
- MongoDB Atlas account (for database)
- Google AI Studio API key (for Gemini)

## Setup

1. Clone the repository:
```bash
git clone https://github.com/nttrung2406/Legal_doc_summary.git
cd legal-doc-summary
```

2. Install backend dependencies:
```bash
cd backend
pip install -r requirements.txt
```

3. Install frontend dependencies:
```bash
cd ../frontend
pip install -r requirements.txt
```

4. Create an `uploads` directory in the backend folder:
```bash
cd ../backend
mkdir uploads
```

## Running the Application

### Option 1: Using Start Scripts (Recommended)

#### For Windows:
```bash
start.bat
```

#### For Linux/Mac:
```bash
chmod +x start.sh
./start.sh
```

This will start both the backend and frontend servers simultaneously with auto-reload enabled.

### Option 2: Manual Start

1. Start the backend server:
```bash
cd backend
uvicorn main:app --reload --port 8000
```

2. In a new terminal, start the Streamlit frontend:
```bash
cd frontend
streamlit run app.py --server.port 8501
```

3. Open your browser and navigate to `http://localhost:8501`

## Usage

1. Sign up for a new account or log in with existing credentials
2. Upload PDF documents using the file uploader
3. View your uploaded documents in the grid view
4. Click on a document to view it and access its features:
   - Overall summary
   - Paragraph-by-paragraph summaries
   - Interactive chat with the document

## Architecture

- Backend: FastAPI with MongoDB database
- Frontend: Streamlit
- AI Models:
  - MiniLM for text embeddings
  - Google Gemini for text generation
- Document Processing:
  - PyMuPDF for PDF text extraction
  - NLTK for text chunking

## Security

- JWT-based authentication
- Password hashing
- Secure file handling
- MongoDB Atlas security features

## Contributing

Feel free to submit issues and enhancement requests!
