import streamlit as st
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import docx
from pypdf import PdfReader
import io
from docx import Document

# --- PAGE CONFIG ---
st.set_page_config(page_title="Muzi AI Quiz Studio", page_icon="🎯", layout="wide")

# UI Styling
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; background-color: #1e3c72; color: white; height: 3em; font-weight: bold; }
    .quiz-container { 
        padding: 20px; border-radius: 10px; border-left: 8px solid #1e3c72; 
        background-color: #ffffff !important; color: #1a1a1a !important; 
        margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .quiz-container * { color: #1a1a1a !important; }
    </style>
    """, unsafe_allow_html=True)

# --- MODEL LOADING (PHI-1.5: Better Reasoning) ---
@st.cache_resource
def load_phi_model():
    model_id = "microsoft/phi-1_5"
    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.float32, trust_remote_code=True)
    return model, tokenizer

model, tokenizer = load_phi_model()

# --- HELPERS ---
def extract_text(file):
    if file.name.endswith('.pdf'):
        reader = PdfReader(file)
        return "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
    elif file.name.endswith('.docx'):
        doc = docx.Document(file)
        return "\n".join([p.text for p in doc.paragraphs])
    return ""

# --- UI ---
st.title("🎯 Muzi AI Quiz Studio")
st.write("NUST Balochistan Campus - Journey Start")

with st.sidebar:
    uploaded_file = st.file_uploader("Upload PDF/DOCX", type=['pdf', 'docx'])
    q_count = st.slider("MCQs per Quiz", 1, 10, 3)

if st.button("🚀 GENERATE MCQS"):
    if uploaded_file:
        context = extract_text(uploaded_file)[:700]
        full_quiz = ""
        
        with st.status("Thinking like a Professor...") as status:
            for j in range(1, q_count + 1):
                # Phi model prompt format
                prompt = f"Instruct: Based on the context: {context}. Create MCQ {j} with options A, B, C, D and Answer.\nOutput:"
                
                inputs = tokenizer(prompt, return_tensors="pt", return_attention_mask=False)
                outputs = model.generate(**inputs, max_length=300, do_sample=True, temperature=0.7)
                res = tokenizer.decode(outputs[0], skip_special_tokens=True).split("Output:")[-1].strip()
                
                full_quiz += f"{res}\n\n"
            
            st.markdown(f"<div class='quiz-container'><b>📝 GENERATED QUIZ</b><p>{full_quiz}</p></div>", unsafe_allow_html=True)
            status.update(label="Ready!", state="complete")
