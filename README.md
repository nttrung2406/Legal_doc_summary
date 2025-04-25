# ReadLaw - Legal Document Summarizer

A web application that helps users analyze and understand legal documents using AI-powered summarization and chat capabilities.

## Features

- User authentication (signup/login)
- PDF document upload and viewing
- AI-powered document summarization
- Paragraph-by-paragraph summaries
- Interactive chat with document content

## Prerequisites

- Python 3.8+
- Node.js 16+
- MongoDB
- Google Gemini API key
- Prometheus, Grafana
- Earlang, RabbitMQ

## Workflow

![image](https://github.com/user-attachments/assets/67aec777-8a14-47af-be34-8f1468b0da05)


## Setup

1. Clone the repository:
```bash
git clone https://github.com/nttrung2406/Legal_doc_summary.git
cd legal-doc-summary
```

2. Set up the backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Create a `.env` file in the backend directory with the following variables:
```
MONGO_URI=your_mongodb_uri
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
MAX_REQUESTS_PER_DAY=50
REQUEST_COOLDOWN=10
GEMINI_API_KEY=your_gemini_api_key
```

4. Set up the frontend:
```bash
cd frontend-react
npm install
```

5. Start the backend server:
```bash
cd backend
uvicorn main:app --reload
```

6. Start the frontend development server:
```bash
cd frontend-react
npm run dev
```

The application will be available at:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000

## API Documentation

Once the backend server is running, you can access the API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Usage

1. Create an account or log in
2. Upload a PDF document
3. View the document and its AI-generated summary
4. Get paragraph-by-paragraph summaries
5. Chat with the document to ask specific questions

## Contributing

Feel free to submit issues and enhancement requests!
