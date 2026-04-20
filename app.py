import streamlit as st
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import docx
from pypdf import PdfReader
import io
from docx import Document

# --- PAGE CONFIG ---
st.set_page_config(page_title="Muzammil AI Quiz Studio", page_icon="🎯", layout="wide")

# Custom CSS for High Visibility and Professional Look
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
    .quiz-container b { color: #1e3c72 !important; font-size: 1.2em; }
    .quiz-container p, .quiz-container div { color: #1a1a1a !important; white-space: pre-wrap; }
    </style>
    """, unsafe_allow_html=True)

# --- MODEL LOADING ---
@st.cache_resource
def load_model_and_tokenizer():
    # LaMini model size mein chota hai isliye free deployment mein stable rehta hai
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
    doc.add_heading('🎯 Muzammil AI Quiz Studio - Professional Report', 0)
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
st.write("University Standard MCQ Generator for NUST Balochistan Campus.")

with st.sidebar:
    st.header("⚙️ Configuration")
    uploaded_file = st.file_uploader("Upload Study Material (PDF/DOCX)", type=['pdf', 'docx'])
    st.divider()
    num_versions = st.slider("Total Quiz Versions", 1, 10, 1)
    q_per_quiz = st.slider("MCQs per Quiz", 1, 10, 5)
    diff = st.selectbox("Difficulty", ["Normal", "Hard", "Expert"])

# --- GENERATION LOGIC ---
if st.button("🚀 GENERATE UNIQUE QUIZZES"):
    if uploaded_file:
        raw_text = extract_text(uploaded_file)
        context = raw_text[:900] # Model ki memory ke mutabiq best limit
        st.session_state.quizzes = []
        
        for i in range(1, num_versions + 1):
            with st.spinner(f"Creating Unique Quiz Version {i}..."):
                # SUPER STRICT PROMPT: Isse model bhatke ga nahi
                prompt = f"""Task: Create exactly {q_per_quiz} Multiple Choice Questions based on the context.
Rules:
1. Provide a Question.
2. Provide 4 options: A, B, C, D.
3. Provide the Correct Answer.
4. Do NOT repeat sentences from the context.

Example:
Question: What is the capital of Pakistan?
A) Karachi B) Lahore C) Islamabad D) Quetta
Answer: C

Context: {context}
Difficulty: {diff}

Quiz #{i}:
"""
                
                output = generator(
                    prompt, 
                    max_new_tokens=800, # Taakay poora quiz generate ho
                    do_sample=True, 
                    temperature=0.7, 
                    repetition_penalty=1.3, # Stops loops like "sampling sampling"
                    pad_token_id=tokenizer.eos_token_id
                )
                
                # Cleanup output to show only the quiz
                res = output[0]['generated_text'].split(f"Quiz #{i}:")[-1].strip()
                
                if len(res) < 30: # Check if model failed
                    res = "Error: Model could not generate a proper quiz. Please try with different text."
                
                st.session_state.quizzes.append(res)
                
                # Show in UI with forced visibility
                st.markdown(f"""
                <div class='quiz-container'>
                    <b>📝 VERSION {i}</b><br><br>
                    <p>{res}</p>
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
