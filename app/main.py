import streamlit as st
from PIL import Image
from streamlit_lottie import st_lottie
import json


st.set_page_config(
    page_title="Team Rocket - Mando Hackathon",
    page_icon="🚀",
    layout="wide",
)


def load_lottiefile(filepath: str):
    with open(filepath, "r") as f:
        return json.load(f)

logo = Image.open("assets/mando.png")
rocket_lottie = load_lottiefile("assets/animation.json")  # Replace with your own

def show_home():
    st_lottie(rocket_lottie, speed=1, reverse=False, loop=True, quality="high", height=300)
    st.image(logo, width=150)
    st.title("🚀 Team Rocket presents: Mando AI Document Q&A")
    st.markdown("""
    Welcome to our submission for the **Mando Hackathon**.

    This intelligent system allows you to:
    - 🧠 Understand documents of multiple formats
    - 📸 Extract text from images using OCR
    - 🌐 Follow and include referenced web links
    - 🔍 Use semantic search to answer questions based on context

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

    uploaded_files = st.file_uploader("📤 Upload your files", 
        type=["pdf", "docx", "pptx", "xlsx", "csv", "png", "jpg", "jpeg", "txt", "json"],
        accept_multiple_files=True)

    question = st.text_input("❓ Ask your question:")

    if st.button("Get Answer"):
        if not uploaded_files or not question.strip():
            st.warning("⚠️ Please upload at least one document and enter a question.")
        else:
            st.info("🔄 Processing your documents and searching for answers...")

            # === PLACEHOLDER: Replace with backend logic ===
            answer = "📖 This is a placeholder answer. The real one will come from your Q&A engine."
            
            st.success("✅ Answer:")
            st.write(answer)

# --------- PAGE ROUTER ---------
if "page" not in st.session_state:
    st.session_state.page = "home"

if st.session_state.page == "home":
    show_home()
else:
    show_qa_page()
