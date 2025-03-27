import streamlit as st
import requests
import json
from datetime import datetime, timedelta
import os
from PyPDF2 import PdfReader
import io
import base64

# API endpoints
API_URL = "http://localhost:8000"

def login(username: str, password: str):
    response = requests.post(
        f"{API_URL}/token",
        data={"username": username, "password": password}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def signup(username: str, email: str, password: str):
    response = requests.post(
        f"{API_URL}/signup",
        params={"username": username, "email": email, "password": password}
    )
    return response.status_code == 200, response.json().get("message", "Unknown error")

def check_session_expiration():
    """Check if the current session is expired."""
    if "token" not in st.session_state or not st.session_state.token:
        return False
    
    if "login_time" not in st.session_state:
        st.session_state.login_time = datetime.now()
        return True
    
    # Check if session is expired (24 hours)
    session_duration = datetime.now() - st.session_state.login_time
    if session_duration > timedelta(hours=24):
        st.session_state.token = None
        st.session_state.login_time = None
        return False
    
    return True

def upload_file(file, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    files = {"file": file}
    response = requests.post(
        f"{API_URL}/upload",
        headers=headers,
        files=files
    )
    return response.status_code == 200, response.json().get("message", "Unknown error")

def get_documents(token: str):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{API_URL}/documents",
        headers=headers
    )
    if response.status_code == 200:
        return response.json()
    return []

def get_document(filename: str, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{API_URL}/document/{filename}",
        headers=headers
    )
    if response.status_code == 200:
        return response.json()
    return None

def get_summary(filename: str, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{API_URL}/summarize/{filename}",
        headers=headers
    )
    if response.status_code == 200:
        return True, response.json()["summary"]
    return False, response.json().get("detail", "Unknown error")

def get_paragraph_summaries(filename: str, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{API_URL}/paragraph-summaries/{filename}",
        headers=headers
    )
    if response.status_code == 200:
        return True, response.json()["summaries"]
    return False, response.json().get("detail", "Unknown error")

def chat_with_document(filename: str, query: str, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{API_URL}/chat/{filename}",
        headers=headers,
        json={"query": query}
    )
    if response.status_code == 200:
        return True, response.json()["response"]
    return False, response.json().get("detail", "Unknown error")

def display_pdf(file_path: str):
    """Display PDF file in Streamlit."""
    try:
        with open(file_path, "rb") as pdf_file:
            base64_pdf = base64.b64encode(pdf_file.read()).decode('utf-8')
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error displaying PDF: {str(e)}")
        st.text("Displaying text content instead:")
        try:
            pdf_reader = PdfReader(file_path)
            for page in pdf_reader.pages:
                st.text(page.extract_text())
        except Exception as e:
            st.error(f"Error extracting text: {str(e)}")

def display_logo():
    """Display the ReadLaw logo."""
    st.markdown("""
        <style>
        .logo {
            font-size: 2.5rem;
            font-weight: bold;
            color: #1E3A8A;
            text-decoration: none;
            font-family: 'Georgia', serif;
        }
        .logo:hover {
            color: #2563EB;
        }
        </style>
        <a href="/" class="logo">ReadLaw</a>
    """, unsafe_allow_html=True)

def main():
    st.set_page_config(layout="wide", page_title="ReadLaw - Legal Document Summarizer")
    
    # Initialize session state
    if "token" not in st.session_state:
        st.session_state.token = None
    if "current_page" not in st.session_state:
        st.session_state.current_page = "main"
    if "api_error" not in st.session_state:
        st.session_state.api_error = None
    if "auth_tab" not in st.session_state:
        st.session_state.auth_tab = "Login"
    if "login_time" not in st.session_state:
        st.session_state.login_time = None
    
    # Check session expiration
    if not check_session_expiration():
        st.session_state.current_page = "main"
    
    # Header with logo and logout button
    if st.session_state.token:
        # Create a container for the header
        st.markdown("""
            <style>
            .header-container {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 1rem 2rem;
                background-color: white;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }
            </style>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="header-container">', unsafe_allow_html=True)
        
        # Logo on the left
        display_logo()
        
        # Logout button on the right
        if st.button("Logout", key="logout_button"):
            st.session_state.token = None
            st.session_state.login_time = None
            st.session_state.current_page = "main"
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Main content
    if st.session_state.current_page == "main":
        if not st.session_state.token:
            st.markdown("""
                <style>
                .auth-container {
                    max-width: 400px;
                    margin: 0 auto;
                    padding: 2rem;
                    background-color: white;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }
                .auth-title {
                    text-align: center;
                    color: #1E3A8A;
                    margin-bottom: 2rem;
                }
                .stTabs [data-baseweb="tab-list"] {
                    gap: 2rem;
                }
                .stTabs [data-baseweb="tab"] {
                    color: #1E3A8A;
                    font-weight: bold;
                }
                .stTabs [aria-selected="true"] {
                    color: #2563EB !important;
                }
                </style>
            """, unsafe_allow_html=True)
            
            st.markdown('<div class="auth-container">', unsafe_allow_html=True)
            st.markdown('<h2 class="auth-title">Welcome to ReadLaw</h2>', unsafe_allow_html=True)
            
            login_tab, signup_tab = st.tabs(["Login", "Sign Up"])
            
            with login_tab:
                with st.form("login_form"):
                    username = st.text_input("Username")
                    password = st.text_input("Password", type="password")
                    submit = st.form_submit_button("Login")
                    
                    if submit:
                        token = login(username, password)
                        if token:
                            st.session_state.token = token
                            st.session_state.login_time = datetime.now()
                            st.rerun()
                        else:
                            st.error("Invalid username or password")
            
            with signup_tab:
                with st.form("signup_form"):
                    new_username = st.text_input("Username")
                    email = st.text_input("Email")
                    new_password = st.text_input("New Password", type="password")
                    signup_submit = st.form_submit_button("Sign Up")
                    
                    if signup_submit:
                        success, message = signup(new_username, email, new_password)
                        if success:
                            st.success(message)
                            st.session_state.auth_tab = "Login"
                            st.rerun()
                        else:
                            st.error(message)
            
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.title("Legal Document Summarizer")
            
            # File upload section
            st.header("Upload PDF Document")
            uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
            if uploaded_file:
                if st.button("Upload"):
                    success, message = upload_file(uploaded_file, st.session_state.token)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
            
            # Documents list section
            st.header("Your Documents")
            documents = get_documents(st.session_state.token)
            
            # Create a grid of document cards
            cols = st.columns(4)
            for idx, doc in enumerate(documents):
                with cols[idx % 4]:
                    if st.button(f"📄 {doc['filename']}", key=f"doc_{idx}"):
                        st.session_state.current_page = "document"
                        st.session_state.current_doc = doc['filename']
                        st.rerun()
    
    elif st.session_state.current_page == "document":
        st.title("Document Viewer")
        
        # Get document data
        doc = get_document(st.session_state.current_doc, st.session_state.token)
        if not doc:
            st.error("Document not found")
            st.session_state.current_page = "main"
            st.rerun()
            return
        
        # Create two columns for the layout
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Original Document")
            # Display PDF
            pdf_path = os.path.join("backend", "uploads", st.session_state.current_doc)
            if os.path.exists(pdf_path):
                display_pdf(pdf_path)
            else:
                st.error("PDF file not found")
                st.text("Displaying text content:")
                for chunk in doc["chunks"]:
                    st.text(chunk)
        
        with col2:
            # Create tabs for different views
            tab1, tab2, tab3 = st.tabs(["Overall Summary", "Paragraph Summaries", "Chat"])
            
            with tab1:
                st.subheader("Overall Summary")
                success, result = get_summary(st.session_state.current_doc, st.session_state.token)
                if success:
                    st.write(result)
                else:
                    st.error(result)
                    if "Daily API limit reached" in result:
                        st.session_state.api_error = result
            
            with tab2:
                st.subheader("Paragraph Summaries")
                success, summaries = get_paragraph_summaries(st.session_state.current_doc, st.session_state.token)
                if success:
                    for idx, summary in enumerate(summaries):
                        with st.expander(f"Paragraph {idx + 1}"):
                            st.write(summary)
                else:
                    st.error(summaries)
                    if "Daily API limit reached" in summaries:
                        st.session_state.api_error = summaries
            
            with tab3:
                st.subheader("Chat with Document")
                if st.session_state.api_error and "Daily API limit reached" in st.session_state.api_error:
                    st.error(st.session_state.api_error)
                    st.info("The chat feature is temporarily disabled. Please try again tomorrow.")
                else:
                    query = st.text_input("Ask a question about the document")
                    if st.button("Ask"):
                        if query:
                            success, response = chat_with_document(st.session_state.current_doc, query, st.session_state.token)
                            if success:
                                st.write(response)
                            else:
                                st.error(response)
                                if "Daily API limit reached" in response:
                                    st.session_state.api_error = response
        
        # Back button
        if st.button("Back to Documents"):
            st.session_state.current_page = "main"
            st.rerun()

if __name__ == "__main__":
    main() 