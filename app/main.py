import streamlit as st
import json
import os
import datetime
from PIL import Image
from streamlit_lottie import st_lottie
from backend.document_parser import parse_file
from backend.ocr_engine import ocr_image
from backend.semantic_search import add_to_index, search
from backend.qa_engine import answer_question
from backend.context_manager import save_context, get_contextual_results

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
rocket_lottie = load_lottiefile("app/assets/animation.json")

# --------- HISTORY MANAGEMENT ---------
data_dir = "app/local"
os.makedirs(data_dir, exist_ok=True)

def save_history():
    if st.session_state.user_email:
        filepath = os.path.join(data_dir, f"{st.session_state.user_email}.json")
        data = {
            "name": st.session_state.user_name,
            "email": st.session_state.user_email,
            "global_history": st.session_state.global_history,
            "chat_history": st.session_state.chat_history
        }
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

def load_history(email):
    filepath = os.path.join(data_dir, f"{email}.json")
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            data = json.load(f)
            st.session_state.user_name = data.get("name")
            st.session_state.user_email = data.get("email")
            st.session_state.global_history = data.get("global_history", [])
            st.session_state.chat_history = data.get("chat_history", {})
            st.session_state.current_chat_id = next(iter(st.session_state.chat_history), None)

if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "user_name" not in st.session_state:
    st.session_state.user_name = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = {}
if "global_history" not in st.session_state:
    st.session_state.global_history = []
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

# --------- HOME PAGE ---------
def show_home():
    st_lottie(rocket_lottie, speed=1, reverse=False, loop=True, quality="high", height=300)
    st.image(logo, width=150)
    st.title("🚀 Team Rocket presents: Mando AI Document Q&A")

    st.markdown("""Welcome to our submission for the **Mando Hackathon**.
    This system allows you to:
    - 🧠 Understand multiple file types
    - 📸 Extract text from images via OCR
    - 🌐 Include content from external web links
    - 🔍 Use semantic search to answer questions precisely
    ---""")

    st.markdown("### 👉 Enter your details to get started:")
    email = st.text_input("📧 Email (for saving personalized history)")
    name = st.text_input("👤 Name (used for display)")

    if st.button("✨ Get Started"):
        if email.strip() and name.strip():
            st.session_state.user_email = email.strip()
            load_history(st.session_state.user_email)
            st.session_state.user_name = name.strip()
            if not st.session_state.chat_history:
                st.session_state.current_chat_id = f"chat_1"
                st.session_state.chat_history[st.session_state.current_chat_id] = []
            st.session_state.page = "qa"
        else:
            st.warning("⚠️ Please enter both name and email.")

# --------- SIDEBAR ---------
def show_sidebar():
    st.sidebar.title(f"👋 Hey, {st.session_state.user_name}")
    if st.sidebar.button("➕ New Chat", key="new_chat_button"):
        new_id = f"chat_{len(st.session_state.chat_history)+1}"
        st.session_state.chat_history[new_id] = []
        st.session_state.current_chat_id = new_id

    for cid in st.session_state.chat_history.keys():
        if st.sidebar.button(f"🗂 {cid}", key=f"chat_button_{cid}"):
            st.session_state.current_chat_id = cid

    if st.sidebar.button("🗑 Delete Current Chat", key="delete_chat_button"):
        del st.session_state.chat_history[st.session_state.current_chat_id]
        st.session_state.current_chat_id = next(iter(st.session_state.chat_history), None)

    st.sidebar.markdown("---")
    st.sidebar.subheader("🕓 Global Activity")
    for entry in st.session_state.global_history[-5:][::-1]:
        st.sidebar.markdown(f"- {entry['question'][:40]}...")

# --------- QA PAGE ---------
# --------- QA PAGE ---------
def show_qa_page():
    show_sidebar()
    st.image(logo, width=120)
    st.title("📚 Mando AI Document Q&A Assistant")
    st.markdown("Upload documents and ask questions – like a conversation with the AI.")

    # Initialize greeting flag
    if 'greeting_shown' not in st.session_state:
        st.session_state.greeting_shown = False

    # Load chat history
    chat_history = []
    if st.session_state.current_chat_id:
        chat_history = st.session_state.chat_history.get(st.session_state.current_chat_id, [])

    # Show chat messages using Streamlit's native components
    chat_container = st.container()
    
    with chat_container:
        # Show greeting if first time
        if not st.session_state.greeting_shown and chat_history:
            with st.chat_message("assistant"):
                st.markdown(f"Hey {st.session_state.user_name}, I see your past work here. Let's continue!")
            st.session_state.greeting_shown = True
            
        # Display chat history
        for chat in chat_history:
            with st.chat_message("user"):
                st.markdown(chat["question"])
            with st.chat_message("assistant"):
                st.markdown(chat["answer"])
                if chat["sources"]:
                    st.caption(f"Sources: {', '.join(chat['sources'])}")

    # Input form at bottom
    with st.form(key='chat_form', clear_on_submit=True):
        uploaded_files = st.file_uploader(
            "📤 Attach files (optional)",
            type=["pdf","docx","pptx","xlsx","csv","png","jpg","jpeg","txt","json"],
            accept_multiple_files=True
        )
        question = st.text_input("❓ Your message:")
        submitted = st.form_submit_button("Send")

    if submitted and question.strip():
        # Initialize variables
        text_chunks = []
        image_files = []
        sources = []
        results = []

        # Process uploaded files
        if uploaded_files:
            st.info("🔄 Processing attachments...")
            for file in uploaded_files:
                ext = file.name.split('.')[-1].lower()
                sources.append(file.name)
                if ext in ["png","jpg","jpeg"]:
                    image_files.append(file)
                    text = ocr_image(file)
                else:
                    text = parse_file(file, ext)
                chunks = [(text[i:i+500], file.name) for i in range(0, len(text), 500)]
                text_chunks.extend(chunks)
            
            add_to_index(text_chunks)
            results = search(question)
            save_context(text_chunks, image_files, sources, results)
            
            # Store for future context
            st.session_state.last_sources = sources
            st.session_state.last_images = image_files
        else:
            # Get context from previous uploads
            results = get_contextual_results(question)
            sources = st.session_state.get("last_sources", [])
            image_files = st.session_state.get("last_images", [])

        # Generate AI answer
        with st.spinner("Analyzing your question..."):
            answer = answer_question(question, results, image_files)

        # Create new entry
        new_entry = {
            "question": question,
            "answer": answer,
            "sources": sources,
            "timestamp": str(datetime.datetime.now())
        }

        # Update UI immediately
        with chat_container:
            with st.chat_message("user"):
                st.markdown(question)
            with st.chat_message("assistant"):
                st.markdown(answer)
                if sources:
                    st.caption(f"Sources: {', '.join(sources)}")

        # Update session state
        if st.session_state.current_chat_id:
            st.session_state.chat_history[st.session_state.current_chat_id].append(new_entry)
            st.session_state.global_history.append(new_entry)
            save_history()
# --------- PAGE ROUTER ---------
if "page" not in st.session_state:
    st.session_state.page = "home"

if st.session_state.page == "home":
    show_home()
else:
    show_qa_page()
