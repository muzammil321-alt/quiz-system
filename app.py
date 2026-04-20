import streamlit as st
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import docx
from pypdf import PdfReader
import io
from docx import Document

# --- PAGE CONFIG ---
st.set_page_config(page_title="Muzammil AI Quiz Studio", page_icon="🎯", layout="wide")

# Custom CSS for Dark Blue Theme
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #1e3c72; color: white; height: 3em; font-weight: bold; }
    .stDownloadButton>button { width: 100%; border-radius: 8px; background-color: #28a745; color: white; height: 3em; font-weight: bold; }
    .quiz-container { padding: 15px; border-radius: 10px; border-left: 5px solid #1e3c72; background-color: white; margin-bottom: 20px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- MODEL LOADING (Optimized) ---
@st.cache_resource
def load_model():
    model_id = "MBZUAI/LaMini-GPT-124M" 
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id, 
        torch_dtype=torch.float32, 
        low_cpu_mem_usage=True
    )
    return pipeline("text-generation", model=model, tokenizer=tokenizer)

generator = load_model()

# --- FUNCTIONS ---
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

# --- UI SESSION STATE ---
if 'quizzes' not in st.session_state:
    st.session_state.quizzes = []

# --- MAIN DASHBOARD ---
st.title("🎯 Muzammil AI Quiz Studio")
st.write("University standard MCQ generator for NUST Balochistan Campus.")

with st.sidebar:
    st.header("⚙️ Settings")
    uploaded_file = st.file_uploader("Upload Study Material", type=['pdf', 'docx'])
    st.divider()
    num_versions = st.slider("Total Quiz Versions", 1, 10, 1)
    q_per_quiz = st.slider("MCQs per Quiz", 1, 10, 5)
    diff = st.selectbox("Difficulty", ["Normal", "Hard", "Expert"])

if st.button("🚀 GENERATE UNIQUE QUIZZES"):
    if uploaded_file:
        raw_text = extract_text(uploaded_file)
        context = raw_text[:800] # Model ki aukaat ke mutabiq context limit
        st.session_state.quizzes = []
        
        for i in range(1, num_versions + 1):
            with st.spinner(f"Creating Unique Quiz {i}..."):
                # Strict Few-Shot Prompting to avoid garbage
                prompt = f"""Task: Create {q_per_quiz} Multiple Choice Questions.
Format:
Question: [Text]
A) [Opt] B) [Opt] C) [Opt] D) [Opt]
Answer: [Letter]

Context: {context}
Level: {diff}
Quiz #{i}:"""
                
                output = generator(
                    prompt, 
                    max_new_tokens=600, 
                    do_sample=True, 
                    temperature=0.7,      # Balanced creativity
                    repetition_penalty=1.3, # Stops "Sampling Sampling" loops
                    pad_token_id=tokenizer.eos_token_id
                )
                
                # Cleanup output
                generated_text = output[0]['generated_text']
                clean_res = generated_text.split(f"Quiz #{i}:")[-1].strip()
                st.session_state.quizzes.append(clean_res)
                
                # Display in UI
                st.markdown(f"<div class='quiz-container'><b>📝 VERSION {i}</b><br>{clean_res}</div>", unsafe_allow_html=True)
    else:
        st.error("Bhai, file upload karna bhool gaye!")

# --- DOWNLOAD ---
if st.session_state.quizzes:
    st.divider()
    word_data = create_docx(st.session_state.quizzes)
    st.download_button(
        label="📥 DOWNLOAD WORD FILE (.DOCX)",
        data=word_data,
        file_name="Muzammil_AI_Quizzes.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
