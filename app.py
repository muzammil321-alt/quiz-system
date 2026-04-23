import streamlit as st
import torch
from transformers import pipeline
import docx
from pypdf import PdfReader
import io
from docx import Document

# --- PAGE CONFIG ---
st.set_page_config(page_title="Muzammil AI Quiz Studio Pro", page_icon="🎯", layout="wide")

# Professional UI
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; background-color: #1e3c72; color: white; height: 3em; font-weight: bold; }
    .quiz-container { 
        padding: 20px; border-radius: 10px; border-left: 8px solid #1e3c72; 
        background-color: #ffffff !important; color: #1a1a1a !important; 
        margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .quiz-container b { color: #1e3c72 !important; }
    .quiz-container p { color: #1a1a1a !important; white-space: pre-wrap; }
    </style>
    """, unsafe_allow_html=True)

# --- MODEL LOADING (FIXED KEYERROR) ---
@st.cache_resource
def load_pro_model():
    # Task specify karna lazmi hai, but strictly for T5 models
    # Agar text2text-generation nahi chal raha, toh summarization use karenge jo same logic hai
    model_id = "google/flan-t5-base"
    return pipeline("summarization", model=model_id, device=-1)

generator = load_pro_model()

# --- HELPERS ---
def extract_text(file):
    if file.name.endswith('.pdf'):
        reader = PdfReader(file)
        return "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
    elif file.name.endswith('.docx'):
        doc = docx.Document(file)
        return "\n".join([p.text for p in doc.paragraphs])
    return ""

def create_docx(quizzes):
    doc = Document()
    doc.add_heading('🎯 Muzammil AI Quiz Studio Pro Report', 0)
    for i, q in enumerate(quizzes, 1):
        doc.add_heading(f'Quiz Version {i}', level=1)
        doc.add_paragraph(q)
        doc.add_page_break()
    return doc

# --- UI ---
st.title("🎯 Muzammil AI Quiz Studio PRO")
st.write("NUST Balochistan Campus - Assignment Tool")

if 'quizzes' not in st.session_state:
    st.session_state.quizzes = []

with st.sidebar:
    st.header("⚙️ Settings")
    uploaded_file = st.file_uploader("Upload Document", type=['pdf', 'docx'])
    num_versions = st.slider("Total Quizzes", 1, 20, 1)
    q_per_quiz = st.slider("MCQs per Quiz", 1, 20, 5)
    difficulty = st.selectbox("Difficulty:", ["Easy", "Standard", "Advanced"])

if st.button("🚀 GENERATE NOW"):
    if uploaded_file:
        context = extract_text(uploaded_file)[:1000]
        st.session_state.quizzes = []
        
        for i in range(1, num_versions + 1):
            full_quiz = ""
            with st.status(f"Generating Quiz {i}...") as status:
                for j in range(1, q_per_quiz + 1):
                    # Prompt designed to trigger T5 properly
                    prompt = f"Using context: {context}. Create a {difficulty} MCQ with options A, B, C, D and Answer."
                    
                    output = generator(prompt, max_length=150, min_length=30, do_sample=True)
                    res = output[0]['summary_text']
                    
                    full_quiz += f"Question {j}: {res}\n\n"
                
                st.session_state.quizzes.append(full_quiz)
                st.markdown(f"<div class='quiz-container'><b>📝 VERSION {i}</b><p>{full_quiz}</p></div>", unsafe_allow_html=True)
                status.update(label=f"Quiz {i} Done!", state="complete")
    else:
        st.error("Chaand bhai, file load karein!")

if st.session_state.quizzes:
    doc_file = create_docx(st.session_state.quizzes)
    bio = io.BytesIO()
    doc_file.save(bio)
    st.download_button("📥 DOWNLOAD WORD FILE", data=bio.getvalue(), file_name="Muzammil_Quizzes.docx")
