import streamlit as st
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import docx
from pypdf import PdfReader
import io
from docx import Document

# --- PAGE CONFIG ---
st.set_page_config(page_title="Muzammil AI Quiz Studio", page_icon="🎯", layout="wide")

# Professional UI Styling
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

@st.cache_resource
def load_model_and_tokenizer():
    model_id = "MBZUAI/LaMini-GPT-124M" 
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.float32, low_cpu_mem_usage=True)
    return pipeline("text-generation", model=model, tokenizer=tokenizer), tokenizer

generator, tokenizer = load_model_and_tokenizer()

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
    doc.add_heading('🎯 Muzammil AI Quiz Studio Report', 0)
    for i, q in enumerate(quizzes, 1):
        doc.add_heading(f'Quiz Version {i}', level=1)
        doc.add_paragraph(q)
        doc.add_page_break()
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

if 'quizzes' not in st.session_state: st.session_state.quizzes = []

st.title("🎯 Muzammil AI Quiz Studio")

with st.sidebar:
    st.header("⚙️ Settings")
    uploaded_file = st.file_uploader("Upload Document", type=['pdf', 'docx'])
    num_versions = st.slider("Total Quizzes", 1, 5, 1)
    q_per_quiz = st.slider("MCQs per Quiz", 1, 5, 3) # Max 5 for stability

if st.button("🚀 GENERATE MCQS"):
    if uploaded_file:
        context = extract_text(uploaded_file)[:800]
        st.session_state.quizzes = []
        
        for i in range(1, num_versions + 1):
            full_quiz = ""
            with st.status(f"Generating Quiz {i}...") as status:
                # Har sawal ke liye alag se model ko call karenge taakay woh options na bhoole
                for j in range(1, q_per_quiz + 1):
                    prompt = f"""Context: {context}
Task: Create 1 Multiple Choice Question with 4 options (A, B, C, D) and Answer.
Question {j}:"""
                    
                    output = generator(prompt, max_new_tokens=250, do_sample=True, temperature=0.7, repetition_penalty=1.2)
                    res = output[0]['generated_text'].split(f"Question {j}:")[-1].strip()
                    full_quiz += f"Question {j}: {res}\n\n"
                
                st.session_state.quizzes.append(full_quiz)
                st.markdown(f"<div class='quiz-container'><b>📝 VERSION {i}</b><p>{full_quiz}</p></div>", unsafe_allow_html=True)
                status.update(label=f"Quiz {i} Complete!", state="complete")
    else:
        st.error("Bhai, file upload karein!")

if st.session_state.quizzes:
    st.download_button("📥 DOWNLOAD WORD FILE", data=create_docx(st.session_state.quizzes), file_name="Muzammil_Quizzes.docx")
