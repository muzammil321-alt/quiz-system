import streamlit as st
import torch
from transformers import pipeline
import docx
from pypdf import PdfReader
import io
from docx import Document

# --- PAGE CONFIG ---
st.set_page_config(page_title="Muzi AI Quiz Studio", page_icon="🎯")

# --- MODEL LOADING (LIGHTWEIGHT) ---
@st.cache_resource
def load_stable_model():
    # Ye model 500MB se kam hai, crash nahi hoga
    return pipeline("text-generation", model="MBZUAI/LaMini-GPT-124M")

generator = load_stable_model()

def extract_text(file):
    if file.name.endswith('.pdf'):
        return "\n".join([p.extract_text() for p in PdfReader(file).pages if p.extract_text()])
    elif file.name.endswith('.docx'):
        return "\n".join([p.text for p in docx.Document(file).paragraphs])
    return ""

# --- UI ---
st.title("🎯 Muzi AI Quiz Studio")
uploaded_file = st.file_uploader("Upload File", type=['pdf', 'docx'])

if st.button("🚀 GENERATE MCQS"):
    if uploaded_file:
        context = extract_text(uploaded_file)[:600] # Short context for stability
        
        # PROMPT ENGINEERING: Manual structure to force the model
        prompt = f"Context: {context}\n\nQuestion: Create one MCQ with options A, B, C, D.\nAnswer:"
        
        with st.spinner("Processing..."):
            output = generator(prompt, max_length=200, do_sample=True, temperature=0.7)
            res = output[0]['generated_text'].split("Answer:")[-1]
            st.success("Generated!")
            st.write(res)
    else:
        st.error("Muzi bhai, file select karein!")
