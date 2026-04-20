import streamlit as st
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import docx
from pypdf import PdfReader
import io
from docx import Document

# --- PAGE CONFIG ---
st.set_page_config(page_title="Muzammil AI Quiz Studio", page_icon="🎯", layout="wide")

# Custom Professional CSS
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; background-color: #1e3c72; color: white; height: 3em; font-weight: bold; }
    .quiz-container { 
        padding: 20px; border-radius: 10px; border-left: 8px solid #1e3c72; 
        background-color: #ffffff !important; color: #1a1a1a !important; 
        margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .quiz-container b { color: #1e3c72 !important; font-size: 1.2em; }
    .quiz-container p { color: #1a1a1a !important; white-space: pre-wrap; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
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
st.write("University Standard Assessment Tool - NUST Balochistan Campus")

with st.sidebar:
    st.header("⚙️ Configuration")
    uploaded_file = st.file_uploader("Upload Document", type=['pdf', 'docx'])
    st.divider()
    num_versions = st.slider("Total Quizzes", 1, 5, 1)
    q_per_quiz = st.slider("MCQs per Quiz", 1, 5, 3)
    difficulty = st.selectbox("Select Difficulty:", ["Normal", "Hard", "Expert"])

if st.button("🚀 GENERATE MCQS"):
    if uploaded_file:
        context = extract_text(uploaded_file)[:800]
        st.session_state.quizzes = []
        
        for i in range(1, num_versions + 1):
            full_quiz = ""
            progress_text = f"Generating Quiz {i}..."
            with st.status(progress_text) as status:
                for j in range(1, q_per_quiz + 1):
                    # Mazeed sakht prompt (Strict Instructions)
                    prompt = f"""Context: {context}
Task: Create 1 Multiple Choice Question. 
Difficulty: {difficulty}
Required Format:
Question {j}: [Question Text]
A) [Option]
B) [Option]
C) [Option]
D) [Option]
Answer: [Correct Letter]

Question {j}:"""
                    
                    output = generator(prompt, max_new_tokens=300, do_sample=True, temperature=0.5, repetition_penalty=1.5)
                    res = output[0]['generated_text'].split(f"Question {j}:")[-1].strip()
                    
                    # Formatting check taakay text messy na ho
                    formatted_q = f"Question {j}: {res}\n\n"
                    full_quiz += formatted_q
                
                st.session_state.quizzes.append(full_quiz)
                st.markdown(f"<div class='quiz-container'><b>📝 VERSION {i} ({difficulty})</b><p>{full_quiz}</p></div>", unsafe_allow_html=True)
                status.update(label=f"Quiz {i} Ready!", state="complete")
    else:
        st.error("Bhai, file upload karein!")

if st.session_state.quizzes:
    st.divider()
    st.download_button("📥 DOWNLOAD AS WORD FILE", data=create_docx(st.session_state.quizzes), file_name="Muzammil_Quizzes.docx")
