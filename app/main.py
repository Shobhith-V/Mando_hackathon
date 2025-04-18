import streamlit as st
from PIL import Image
from streamlit_lottie import st_lottie
import json

from backend.document_parser import parse_file
from backend.ocr_engine import ocr_image
from backend.semantic_search import add_to_index, search
from backend.qa_engine import answer_question  

# --------- CONFIG ---------
st.set_page_config(
    page_title="Team Rocket - Mando Hackathon",
    page_icon="🚀",
    layout="wide",
)

# --------- LOAD ASSETS ---------
def load_lottiefile(filepath: str):
    with open(filepath, "r") as f:
        return json.load(f)

logo = Image.open("app/assets/mando.png")
rocket_lottie = load_lottiefile("app/assets/animation.json")  # Your lottie file

# --------- HOME PAGE ---------
def show_home():
    st_lottie(rocket_lottie, speed=1, reverse=False, loop=True, quality="high", height=300)
    st.image(logo, width=150)
    st.title("🚀 Team Rocket presents: Mando AI Document Q&A")
    st.markdown("""
    Welcome to our submission for the **Mando Hackathon**.

    This system allows you to:
    - 🧠 Understand multiple file types
    - 📸 Extract text from images via OCR
    - 🌐 Follow and include content from external web links
    - 🔍 Use semantic search to accurately answer questions

    ---
    """)
    st.markdown("### 👉 Ready to try it out?")
    if st.button("✨ Get Started"):
        st.session_state.page = "qa"

# --------- QA PAGE ---------
def show_qa_page():
    st.image(logo, width=120)
    st.title("📚 Mando AI Document Q&A Assistant")
    st.markdown("Upload documents and ask questions – let AI find the answers for you!")

    uploaded_files = st.file_uploader("📤 Upload files (PDF, DOCX, CSV, Images, etc.)", 
        type=["pdf", "docx", "pptx", "xlsx", "csv", "png", "jpg", "jpeg", "txt", "json"],
        accept_multiple_files=True)

    question = st.text_input("❓ Ask your question here:")

    if st.button("Get Answer"):
        if not uploaded_files or not question.strip():
            st.warning("⚠️ Please upload at least one document and enter a question.")
            return

        st.info("🔄 Processing documents...")

        text_chunks = []
        image_files = []

        for file in uploaded_files:
            filetype = file.name.split(".")[-1].lower()

            if filetype in ["png", "jpg", "jpeg"]:
                image_files.append(file)  # For vision-based answering
                text = ocr_image(file)
            else:
                text = parse_file(file, filetype)

            # Simple chunking for embedding
            chunks = [(text[i:i+500], file.name) for i in range(0, len(text), 500)]
            text_chunks.extend(chunks)

        add_to_index(text_chunks)
        results = search(question)

        answer = answer_question(question, results, image_files)

        st.success("✅ Answer:")
        st.write(answer)

if "page" not in st.session_state:
    st.session_state.page = "home"

if st.session_state.page == "home":
    show_home()
else:
    show_qa_page()
