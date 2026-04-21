import streamlit as st
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
import docx
from pypdf import PdfReader
import io
from docx import Document

# --- PAGE CONFIG ---
st.set_page_config(page_title="Muzammil AI Quiz Studio Pro", page_icon="🎯", layout="wide")

# Custom CSS for Visibility (Chaand bhai, isse text hamesha saaf nazar ayega)
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; background-color: #1e3c72; color: white; height: 3em; font-weight: bold; }
    .quiz-container { 
        padding: 20px; border-radius: 10px; border-left: 8px solid #1e3c72; 
        background-color: #ffffff !important; color: #1a1a1a !important; 
        margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .quiz-container b { color: #1e3c72 !important; }
    .quiz-container p { color: #1a1a1a !important; white-space: pre-wrap; font-family: sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# --- MODEL LOADING (FLAN-T5) ---
@st.cache_resource
def load_pro_model():
    # Ye model LaMini se boht behtar hai
    model_id = "google/flan-t5-base" 
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForSeq2SeqLM.from_pretrained(
        model_id, 
        torch_dtype=torch.float32, 
        low_cpu_mem_usage=True
    )
    return pipeline("text2text-generation", model=model, tokenizer=tokenizer)

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
    doc.add_heading('🎯 Muzammil AI Quiz Studio Pro', 0)
    for i, q in enumerate(quizzes, 1):
        doc.add_heading(f'Quiz Version {i}', level=1)
        doc.add_paragraph(q)
        doc.add_page_break()
    return doc

# --- UI ---
st.title("🎯 Muzammil AI Quiz Studio PRO")
st.write("University Standard MCQ Generator - NUST Balochistan Campus")

with st.sidebar:
    st.header("⚙️ Configuration")
    uploaded_file = st.file_uploader("Upload Document", type=['pdf', 'docx'])
    st.divider()
    # Limits set to 20 as requested
    num_versions = st.slider("Total Quizzes", 1, 20, 1)
    q_per_quiz = st.slider("MCQs per Quiz", 1, 20, 5)
    difficulty = st.selectbox("Difficulty:", ["Easy", "Standard", "Advanced"])

if st.button("🚀 GENERATE PROFESSIONAL MCQS"):
    if uploaded_file:
        context_raw = extract_text(uploaded_file)
        context = context_raw[:1000] # Model ki stability ke liye
        st.session_state.quizzes = []
        
        for i in range(1, num_versions + 1):
            full_quiz = ""
            with st.status(f"Generating Quiz {i}...") as status:
                for j in range(1, q_per_quiz + 1):
                    # T5 style prompting
                    prompt = f"generate a {difficulty} multiple choice question with 4 options (A, B, C, D) and the correct answer for this topic: {context}"
                    
                    output = generator(prompt, max_length=256, do_sample=True, temperature=0.7)
                    res = output[0]['generated_text']
                    
                    full_quiz += f"Question {j}: {res}\n\n"
                
                st.session_state.quizzes.append(full_quiz)
                st.markdown(f"<div class='quiz-container'><b>📝 VERSION {i} ({difficulty})</b><p>{full_quiz}</p></div>", unsafe_allow_html=True)
                status.update(label=f"Quiz {i} Complete!", state="complete")
    else:
        st.error("Bhai, file upload karein!")

# --- DOWNLOAD ---
if 'quizzes' in st.session_state and st.session_state.quizzes:
    doc = create_docx(st.session_state.quizzes)
    bio = io.BytesIO()
    doc.save(bio)
    st.download_button("📥 DOWNLOAD WORD FILE", data=bio.getvalue(), file_name="Muzammil_Pro_Quizzes.docx")
