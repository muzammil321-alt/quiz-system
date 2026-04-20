import streamlit as st
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import docx
from pypdf import PdfReader
import io
from docx import Document # Word file banane ke liye

# Page Config
st.set_page_config(page_title="Muzammil AI Quiz Studio", page_icon="🎯", layout="wide")

# Custom CSS for Professional Look
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; background-color: #2a5298; color: white; height: 3em; font-weight: bold; }
    .stDownloadButton>button { width: 100%; border-radius: 10px; background-color: #28a745; color: white; height: 3em; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- MODEL LOADING ---
@st.cache_resource
def load_model():
    model_id = "MBZUAI/LaMini-GPT-124M" 
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.float32, low_cpu_mem_usage=True)
    return pipeline("text-generation", model=model, tokenizer=tokenizer)

generator = load_model()

# --- HELPER: Word File Generator ---
def create_docx(quizzes):
    doc = Document()
    doc.add_heading('🎯 Muzammil AI Quiz Report', 0)
    for i, q in enumerate(quizzes, 1):
        doc.add_heading(f'Quiz Version {i}', level=1)
        doc.add_paragraph(q)
        doc.add_page_break() # Har quiz naye page se shuru hogi
    
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

# --- EXTRACTION ---
def extract_text(file):
    if file.name.endswith('.pdf'):
        reader = PdfReader(file)
        return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    elif file.name.endswith('.docx'):
        doc = docx.Document(file)
        return "\n".join([p.text for p in doc.paragraphs])
    return ""

# --- UI DASHBOARD ---
st.title("🎯 Muzammil AI Quiz Studio")

# State to store quizzes across reruns
if 'all_quizzes' not in st.session_state:
    st.session_state.all_quizzes = []

with st.sidebar:
    st.header("⚙️ Quiz Settings")
    uploaded_file = st.file_uploader("Upload PDF or DOCX", type=['pdf', 'docx'])
    num_quizzes = st.slider("Total Quiz Versions:", 1, 10, 1)
    mcqs_per_quiz = st.slider("MCQs per Quiz:", 1, 15, 5)
    difficulty = st.selectbox("Difficulty:", ["Normal", "Hard", "Expert"])

# Action
if st.button("🚀 GENERATE UNIQUE QUIZZES"):
    if uploaded_file:
        context = extract_text(uploaded_file)
        st.session_state.all_quizzes = [] # Reset old ones
        
        for i in range(1, num_quizzes + 1):
            with st.spinner(f"Generating Unique Quiz Version {i}..."):
                # Temperature 0.9 taakay uniqueness barhay
                prompt = f"Context: {context[:800]}\nTask: Create exactly {mcqs_per_quiz} UNIQUE MCQs for Quiz #{i}. Level: {difficulty}. Ensure questions are different. Format: Question, Options A-D, Answer.\nQuiz:"
                
                output = generator(prompt, max_new_tokens=600, do_sample=True, temperature=0.9)
                res = output[0]['generated_text'].split("Quiz:")[-1].strip()
                st.session_state.all_quizzes.append(res)
                
                st.markdown(f"### ✅ Quiz {i} Generated")
                st.info(res)
    else:
        st.error("Bhai, file to upload karo!")

# Download Section (Word File)
if st.session_state.all_quizzes:
    st.divider()
    docx_data = create_docx(st.session_state.all_quizzes)
    st.download_button(
        label="📥 DOWNLOAD ALL QUIZZES AS WORD FILE (.DOCX)",
        data=docx_data,
        file_name="Muzammil_AI_Quizzes.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
