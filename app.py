import streamlit as st
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import docx
from pypdf import PdfReader
import io
from docx import Document

# --- PAGE CONFIG ---
st.set_page_config(page_title="Muzammil AI Quiz Studio", page_icon="🎯", layout="wide")

# Custom CSS for Professional UI
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #1e3c72; color: white; height: 3em; font-weight: bold; }
    .stDownloadButton>button { width: 100%; border-radius: 8px; background-color: #28a745; color: white; height: 3em; font-weight: bold; }
    .quiz-container { padding: 20px; border-radius: 10px; border-left: 5px solid #1e3c72; background-color: white; margin-bottom: 20px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- MODEL LOADING (Corrected to avoid NameError) ---
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

# Load both at the start
generator, tokenizer = load_model_and_tokenizer()

# --- HELPER FUNCTIONS ---
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

# --- SESSION STATE ---
if 'quizzes' not in st.session_state:
    st.session_state.quizzes = []

# --- UI LAYOUT ---
st.title("🎯 Muzammil AI Quiz Studio")
st.write("Professional MCQ Generator for NUST Balochistan Campus.")

with st.sidebar:
    st.header("⚙️ Configuration")
    uploaded_file = st.file_uploader("Upload Document (PDF/DOCX)", type=['pdf', 'docx'])
    st.divider()
    num_versions = st.slider("Total Quiz Versions", 1, 10, 1)
    q_per_quiz = st.slider("MCQs per Quiz", 1, 10, 5)
    diff = st.selectbox("Difficulty", ["Normal", "Hard", "Expert"])

# --- GENERATION ---
if st.button("🚀 GENERATE UNIQUE QUIZZES"):
    if uploaded_file:
        raw_text = extract_text(uploaded_file)
        context = raw_text[:800] # Limit for model stability
        st.session_state.quizzes = []
        
        for i in range(1, num_versions + 1):
            with st.spinner(f"Creating Unique Quiz Version {i}..."):
                # Strict structure for clean output
                prompt = f"""Task: Create a Multiple Choice Quiz.
Format:
Question: [Text]
A) [Opt] B) [Opt] C) [Opt] D) [Opt]
Answer: [Letter]

Context: {context}
Difficulty: {diff}
Quiz #{i} ({q_per_quiz} MCQs):"""
                
                output = generator(
                    prompt, 
                    max_new_tokens=600, 
                    do_sample=True, 
                    temperature=0.7, 
                    repetition_penalty=1.3,
                    pad_token_id=tokenizer.eos_token_id # Corrected variable access
                )
                
                res = output[0]['generated_text'].split(f"Quiz #{i}")[-1].strip()
                # Cleaning additional tags if any
                clean_res = res.replace(":", "", 1).strip()
                st.session_state.quizzes.append(clean_res)
                
                # Show in UI
                st.markdown(f"""
                <div class='quiz-container'>
                    <b style='color:#1e3c72; font-size:1.2em;'>📝 QUIZ VERSION {i}</b><br><br>
                    {clean_res.replace('\\n', '<br>')}
                </div>
                """, unsafe_allow_html=True)
    else:
        st.error("Bhai, pehle document upload karein!")

# --- DOWNLOAD ---
if st.session_state.quizzes:
    st.divider()
    word_file = create_docx(st.session_state.quizzes)
    st.download_button(
        label="📥 DOWNLOAD ALL QUIZZES (WORD FILE)",
        data=word_file,
        file_name="Muzammil_AI_Quizzes.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
