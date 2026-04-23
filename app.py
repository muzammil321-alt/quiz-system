import streamlit as st
import torch
from transformers import pipeline
import docx
import io
from docx import Document

# --- PAGE CONFIG ---
st.set_page_config(page_title="Muzi AI Quiz Studio Pro", page_icon="🎯", layout="wide")

# UI Styling
st.markdown("<style>.stButton>button { width: 100%; border-radius: 8px; background-color: #1e3c72; color: white; }</style>", unsafe_allow_html=True)

# --- MODEL LOADING (ONLY ONCE) ---
@st.cache_resource
def load_stable_model():
    # Adding repetition_penalty to STOP THE LOOPING
    return pipeline("text-generation", model="MBZUAI/LaMini-GPT-124M")

generator = load_stable_model()

# --- UI ---
st.title("🎯 Muzi AI Quiz Studio PRO")
st.write("NUST Balochistan Campus - Loop-Free Edition")

with st.sidebar:
    st.header("⚙️ Configuration")
    topic = st.text_input("Enter Topic (e.g. Artificial Intelligence, Statistics)", "Data Science")
    num_versions = st.slider("Total Quizzes", 1, 5, 1) # Limit to 5 for safety
    q_per_quiz = st.slider("MCQs per Quiz", 1, 10, 3)

if st.button("🚀 GENERATE MCQS"):
    st.session_state.quizzes = []
    
    for i in range(1, num_versions + 1):
        full_quiz = ""
        with st.status(f"Generating Quiz {i}...") as status:
            for j in range(1, q_per_quiz + 1):
                # CLEAN PROMPT (No heavy context to confuse the model)
                prompt = f"Question about {topic}. Options A, B, C, D. Answer:"
                
                # REPETITION PENALTY added to stop loops
                output = generator(prompt, 
                                   max_length=100, 
                                   do_sample=True, 
                                   repetition_penalty=1.5, 
                                   temperature=0.8)
                
                res = output[0]['generated_text'].replace(prompt, "").strip()
                full_quiz += f"Q{j}: {res}\n\n"
            
            st.session_state.quizzes.append(full_quiz)
            st.info(f"VERSION {i}\n{full_quiz}")
            status.update(label=f"Quiz {i} Done!", state="complete")
