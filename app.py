import streamlit as st
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import docx
from pypdf import PdfReader
import io
from docx import Document

# --- PAGE CONFIG ---
st.set_page_config(page_title="Muzammil AI Quiz Studio", page_icon="🎯", layout="wide")

# Custom CSS for Professional Dark/Light UI
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #1e3c72; color: white; height: 3em; font-weight: bold; }
    .stDownloadButton>button { width: 100%; border-radius: 8px; background-color: #28a745; color: white; height: 3em; font-weight: bold; }
    
    .quiz-container { 
        padding: 20px; 
        border-radius: 10px; 
        border-left: 8px solid #1e3c72; 
        background-color: #ffffff !important; 
        color: #1a1a1a !important; 
        margin-bottom: 20px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .quiz-container b { color: #1e3c72 !important; }
    .quiz-container p, .quiz-container div { color: #1a1a1a !important; white-space: pre-wrap; font-family: sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# --- MODEL LOADING ---
@st.cache_resource
def load_model_and_tokenizer():
    model_id = "MBZUAI/LaMini-GPT-124M" 
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id, 
        torch_dtype=torch.float32, 
        low_cpu_mem_usage=True
    )
    gen_pipeline = pipeline("text-generation", model=model, tokenizer=tokenizer)
    return gen_pipeline, tokenizer

generator, tokenizer = load_model_and_tokenizer()

# --- HELPERS ---
def extract_text(file):
    if file.name.endswith('.pdf'):
        reader = PdfReader(file)
        return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    elif file.name.endswith('.docx'):
        doc = docx.Document(file)
        return "\n".join([p.text for p in doc.paragraphs])
    return ""

def create_docx(quizzes):
    doc = Document()
    doc.add_heading('🎯 Muzammil AI Quiz Studio - Report', 0)
    for i, q in enumerate(quizzes, 1):
        doc.add_heading(f'Quiz Version {i}', level=1)
        doc.add_paragraph(q)
        doc.add_page_break()
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

# --- UI ---
if 'quizzes' not in st.session_state:
    st.session_state.quizzes = []

st.title("🎯 Muzammil AI Quiz Studio")
st.write("NUST Balochistan Campus AI Project")

with st.sidebar:
    st.header("⚙️ Configuration")
    uploaded_file = st.file_uploader("Upload Document", type=['pdf', 'docx'])
    num_versions = st.slider("Total Quizzes", 1, 5, 1)
    q_per_quiz = st.slider("MCQs per Quiz", 1, 10, 3)
    diff = st.selectbox("Difficulty", ["Normal", "Hard"])

# --- GENERATION ---
if st.button("🚀 GENERATE MCQS NOW"):
    if uploaded_file:
        context = extract_text(uploaded_file)[:900]
        st.session_state.quizzes = []
        
        for i in range(1, num_versions + 1):
            with st.spinner(f"Generating Quiz {i}..."):
                # SUPER STRICT PROMPT
                prompt = f"""Below is a context. Use it to create {q_per_quiz} Multiple Choice Questions.
Each question must have:
1. The Question.
2. Four options: A), B), C), D).
3. The correct Answer.

Context: {context}

Quiz Version {i}:
1."""
                
                output = generator(
                    prompt, 
                    max_new_tokens=900, # Barha diya taakay options cut na hon
                    do_sample=True, 
                    temperature=0.6,     # Kam kiya taakay model focus rahay
                    repetition_penalty=1.4,
                    pad_token_id=tokenizer.eos_token_id
                )
                
                res = output[0]['generated_text'].split(f"Quiz Version {i}:")[-1].strip()
                # Adding back the "1." that we used to force the model
                final_res = "1. " + res 
                st.session_state.quizzes.append(final_res)
                
                st.markdown(f"""
                <div class='quiz-container'>
                    <b>📝 VERSION {i}</b><br><br>
                    <p>{final_res}</p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.error("Bhai, file upload karein!")

# --- DOWNLOAD ---
if st.session_state.quizzes:
    st.divider()
    docx_file = create_docx(st.session_state.quizzes)
    st.download_button("📥 DOWNLOAD WORD FILE", data=docx_file, file_name="Muzammil_Quizzes.docx")
