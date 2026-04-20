import streamlit as st
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import docx
from pypdf import PdfReader
import io

# Page Config
st.set_page_config(page_title="Muzammil AI Quiz Studio", page_icon="🎯")

# --- MODEL LOADING (Optimized for Free Cloud) ---
@st.cache_resource
def load_model():
    # Bhai, TinyLlama se bhi fast aur halka model use kar rahay hain taakay crash na ho
    model_id = "MBZUAI/LaMini-GPT-124M" 
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id, 
        torch_dtype=torch.float32,
        low_cpu_mem_usage=True
    )
    return pipeline("text-generation", model=model, tokenizer=tokenizer)

generator = load_model()

# --- EXTRACTION ---
def extract_text(file):
    if file.name.endswith('.pdf'):
        reader = PdfReader(file)
        return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    elif file.name.endswith('.docx'):
        doc = docx.Document(file)
        return "\n".join([p.text for p in doc.paragraphs])
    return ""

# --- UI ---
st.title("🎯 Muzammil AI Quiz Studio")
uploaded_file = st.file_uploader("Upload Document", type=['pdf', 'docx'])

if st.button("🚀 Generate"):
    if uploaded_file:
        context = extract_text(uploaded_file)
        with st.spinner("Generating..."):
            prompt = f"Context: {context[:500]}\nTask: Create 2 MCQs with answers.\nQuiz:"
            # Max tokens kam rakhen taakay speed bani rahay
            output = generator(prompt, max_new_tokens=150, do_sample=True, temperature=0.7)
            st.success(output[0]['generated_text'].split("Quiz:")[-1])
    else:
        st.warning("Bhai file upload kardo pehle!")
