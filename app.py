import streamlit as st
import torch
from transformers import pipeline
import docx
from pypdf import PdfReader
import io
from docx import Document

# --- PAGE CONFIG ---
st.set_page_config(page_title="Muzi AI Quiz Studio Pro", page_icon="🎯", layout="wide")

# --- MODEL LOADING (STABLE) ---
@st.cache_resource
def load_stable_model():
    # 'text2text-generation' is better for following instructions than 'text-generation'
    return pipeline("text2text-generation", model="MBZUAI/LaMini-Flan-T5-248M")

generator = load_stable_model()

def extract_text(file):
    if file.name.endswith('.pdf'):
        return "\n".join([p.extract_text() for p in PdfReader(file).pages if p.extract_text()])
    elif file.name.endswith('.docx'):
        return "\n".join([p.text for p in docx.Document(file).paragraphs])
    return ""

# --- UI ---
st.title("🎯 Muzi AI Quiz Studio PRO")
st.write("NUST Balochistan Campus - File-to-Quiz Logic")

with st.sidebar:
    st.header("⚙️ Configuration")
    uploaded_file = st.file_uploader("Upload Document", type=['pdf', 'docx'])
    num_versions = st.slider("Total Quizzes", 1, 5, 1)
    q_per_quiz = st.slider("MCQs per Quiz", 1, 10, 3)

if st.button("🚀 GENERATE FROM FILE"):
    if uploaded_file:
        raw_text = extract_text(uploaded_file)
        # SIRF PEHLA TUKRA (CHUNK) LENA HAI TAAKAY MODEL CONFUSE NA HO
        context = raw_text[:500] 
        st.session_state.quizzes = []
        
        for i in range(1, num_versions + 1):
            full_quiz = ""
            with st.status(f"Reading File & Generating Quiz {i}...") as status:
                for j in range(1, q_per_quiz + 1):
                    # Instruction-based prompt
                    prompt = f"Based on this text: {context}\nGenerate a multiple choice question with options A, B, C, D and the correct answer."
                    
                    output = generator(prompt, 
                                     max_length=150, 
                                     repetition_penalty=2.5, # Loop ko sakhti se rokne ke liye
                                     do_sample=True, 
                                     temperature=0.7)
                    
                    res = output[0]['generated_text']
                    full_quiz += f"Question {j}: {res}\n\n"
                
                st.session_state.quizzes.append(full_quiz)
                st.info(f"VERSION {i}\n{full_quiz}")
                status.update(label=f"Quiz {i} Ready!", state="complete")
    else:
        st.error("Muzi bhai, pehle file toh upload karein!")

# WORD DOWNLOAD
if 'quizzes' in st.session_state and st.session_state.quizzes:
    doc = Document()
    for q in st.session_state.quizzes:
        doc.add_paragraph(q)
    bio = io.BytesIO()
    doc.save(bio)
    st.download_button("📥 DOWNLOAD WORD FILE", data=bio.getvalue(), file_name="Muzi_Quizzes.docx")
