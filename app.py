import streamlit as st
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import docx
from pypdf import PdfReader
import io

# Page Config
st.set_page_config(page_title="Muzammil AI Quiz Studio", page_icon="🎯", layout="wide")

# Custom CSS for Professional Look
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #2a5298; color: white; }
    .stProgress > div > div > div > div { background-color: #2a5298; }
    </style>
    """, unsafe_allow_html=True)

# --- MODEL LOADING (Cached for Speed) ---
@st.cache_resource
def load_model():
    model_id = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    # Streamlit Cloud ke liye mazeed optimize kiya hai
    model = AutoModelForCausalLM.from_pretrained(
        model_id, 
        torch_dtype=torch.float32, # CPU ke liye float32 zyada stable hai
        low_cpu_mem_usage=True
    )
    return pipeline("text-generation", model=model, tokenizer=tokenizer)
generator = load_model()

# --- HELPER FUNCTIONS ---
def extract_text(file):
    if file.name.endswith('.pdf'):
        reader = PdfReader(file)
        return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    elif file.name.endswith('.docx'):
        doc = docx.Document(file)
        return "\n".join([p.text for p in doc.paragraphs])
    return ""

# --- UI LAYOUT ---
st.title("🎯 Muzammil AI Quiz Studio")
st.subheader("Generate Professional MCQs from Documents")

with st.sidebar:
    st.header("⚙️ Configuration")
    uploaded_file = st.file_uploader("Upload PDF or DOCX", type=['pdf', 'docx'])
    num_quizzes = st.slider("Total Quizzes", 1, 10, 1)
    mcqs_per_quiz = st.slider("MCQs per Quiz", 1, 10, 3)
    difficulty = st.selectbox("Difficulty Level", ["Normal", "Hard", "Expert"])

if st.button("🚀 Generate MCQs"):
    if uploaded_file is not None:
        context = extract_text(uploaded_file)
        
        for i in range(1, num_quizzes + 1):
            with st.status(f"Generating Quiz Version {i}...", expanded=True) as status:
                prompt = f"<|system|>\nYou are an MCQ generator. Be concise. Only output questions and answers.<|user|>\nContext: {context[:1000]}\nTask: Quiz #{i}, {mcqs_per_quiz} MCQs, {difficulty} level.<|assistant|>\nQuiz #{i}:"
                
                output = generator(prompt, max_new_tokens=500, do_sample=True, temperature=0.8)
                res = output[0]['generated_text'].split("<|assistant|>")[-1].strip()
                
                st.markdown(f"### 📝 Quiz Version {i}")
                st.info(res)
                status.update(label=f"Quiz {i} Complete!", state="complete", expanded=False)
    else:
        st.error("Bhai, file to upload karo!")
