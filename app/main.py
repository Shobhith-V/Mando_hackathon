import streamlit as st
import json
import datetime
from PIL import Image
from streamlit_lottie import st_lottie
from backend.document_parser import parse_file
from backend.ocr_engine import ocr_image
from backend.semantic_search import add_to_index, search, clear_index
from backend.qa_engine import answer_question
from backend.context_manager import (
    save_user_data,
    load_user_data,
    migrate_chat_history,
    update_chat_context,
    get_contextual_results
)

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

# Initialize session state
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "user_name" not in st.session_state:
    st.session_state.user_name = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = {}
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

# --------- HOME PAGE ---------
def show_home():
    st_lottie(rocket_lottie, speed=1, reverse=False, loop=True, quality="high", height=300)
    st.image(logo, width=150)
    st.title("🚀 Team Rocket presents: Mando AI Document Q&A")

    st.markdown("### 👉 Enter your details to get started:")
    email = st.text_input("📧 Email (for saving personalized history)")
    name = st.text_input("👤 Name (used for display)")

    if st.button("✨ Get Started"):
        if email.strip() and name.strip():
            st.session_state.user_email = email.strip()
            user_data = load_user_data(st.session_state.user_email)
            
            st.session_state.user_name = name.strip()
            st.session_state.chat_history = migrate_chat_history(
                user_data.get("chat_history", {})
            )
            
            if not st.session_state.chat_history:
                new_id = f"chat_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
                st.session_state.chat_history[new_id] = {
                    "title": "New Chat",
                    "messages": [],
                    "context": {"text_chunks": [], "sources": []}
                }
                st.session_state.current_chat_id = new_id
            else:
                st.session_state.current_chat_id = next(
                    iter(st.session_state.chat_history), 
                    None
                )
                
            st.session_state.page = "qa"
        else:
            st.warning("⚠️ Please enter both name and email.")

# --------- SIDEBAR ---------
def show_sidebar():
    st.sidebar.title(f"👋 Hey, {st.session_state.user_name}")
    
    if st.sidebar.button("➕ New Chat"):
        new_id = f"chat_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        st.session_state.chat_history[new_id] = {
            "title": "New Chat",
            "messages": [],
            "context": {"text_chunks": [], "sources": []}
        }
        st.session_state.current_chat_id = new_id
        clear_index()

    for cid, chat in st.session_state.chat_history.items():
        title = chat.get("title", "New Chat")
        btn_label = f"💬 {title}"
        
        # Safe timestamp handling
        timestamp_part = cid.split('_')[1] if '_' in cid else None
        time_info = "Unknown creation time"
        
        if timestamp_part and len(timestamp_part) == 14:
            try:
                dt = datetime.datetime.strptime(timestamp_part, '%Y%m%d%H%M%S')
                time_info = dt.strftime('%b %d, %H:%M')
            except ValueError:
                pass

        if st.sidebar.button(
            btn_label,
            key=f"chat_button_{cid}",
            help=f"Created: {time_info}"
        ):
            st.session_state.current_chat_id = cid

    if st.sidebar.button("🗑 Delete Current Chat"):
        if st.session_state.current_chat_id:
            del st.session_state.chat_history[st.session_state.current_chat_id]
            if st.session_state.chat_history:
                st.session_state.current_chat_id = next(
                    iter(st.session_state.chat_history), 
                    None
                )
            else:
                st.session_state.current_chat_id = None
            clear_index()
# --------- QA PAGE ---------
def show_qa_page():
    show_sidebar()
    st.image(logo, width=120)
    st.title("📚 Mando AI Document Q&A Assistant")
    
    chat_container = st.container()
    
    # Get or create current chat
    current_chat = st.session_state.chat_history.setdefault(
        st.session_state.current_chat_id,
        {
            "title": "New Chat",
            "messages": [],
            "context": {
                "text_chunks": [],
                "sources": []
            }
        }
    )
    messages = current_chat.get("messages", [])

    # Re-index when switching chats
    if st.session_state.get('last_indexed_chat_id') != st.session_state.current_chat_id:
        clear_index()
        context_chunks = current_chat.get("context", {}).get("text_chunks", [])
        if context_chunks:
            add_to_index(context_chunks)
        st.session_state.last_indexed_chat_id = st.session_state.current_chat_id

    # Display chat history
    with chat_container:
        for msg in messages:
            role = msg.get("role", "user")
            with st.chat_message(role):
                content = msg.get("content", "")
                sources = msg.get("sources", [])
                st.markdown(content)
                if sources:
                    st.caption(f"Sources: {', '.join(sources)}")

    # Handle file upload and question input
    with st.form(key='chat_form', clear_on_submit=True):
        uploaded_files = st.file_uploader(
            "📤 Attach files (optional)",
            type=["pdf","docx","pptx","xlsx","csv","png","jpg","jpeg","txt","json"],
            accept_multiple_files=True
        )
        question = st.text_input("❓ Your message:")
        submitted = st.form_submit_button("Send")

    if submitted and question.strip():
        new_text_chunks = []
        new_sources = []
        
             # Set chat title from first question
        if len(current_chat["messages"]) == 0:
            clean_question = ' '.join(question.strip().split())
            shortened_title = (clean_question[:50] + "...") if len(clean_question) > 50 else clean_question
            current_chat["title"] = shortened_title or "Untitled Chat"
            
            # Immediately save after setting title
            save_user_data(
                st.session_state.user_email,
                st.session_state.user_name,
                st.session_state.chat_history
            )
        
        if uploaded_files:
            with st.spinner("Processing documents..."):
                for file in uploaded_files:
                    ext = file.name.split('.')[-1].lower()
                    try:
                        if ext in ["png","jpg","jpeg"]:
                            text = ocr_image(file)
                        else:
                            text = parse_file(file, ext)
                    except Exception as e:
                        st.error(f"Error processing {file.name}: {str(e)}")
                        continue
                    
                    chunks = [(text[i:i+500], file.name) for i in range(0, len(text), 500)]
                    new_text_chunks.extend(chunks)
                    new_sources.append(file.name)
                
                if new_text_chunks:
                    st.session_state.chat_history = update_chat_context(
                        st.session_state.current_chat_id,
                        new_text_chunks,
                        new_sources,
                        st.session_state.chat_history
                    )
                    add_to_index(new_text_chunks)

        # Get relevant context and generate answer
        context_results = get_contextual_results(
            st.session_state.current_chat_id,
            question,
            st.session_state.chat_history
        )
        
        with st.spinner("Analyzing your question..."):
            try:
                answer = answer_question(question, context_results)
            except Exception as e:
                answer = f"Sorry, I encountered an error: {str(e)}"

        # Update chat history
        current_chat.setdefault("messages", []).extend([
            {"role": "user", "content": question, "sources": new_sources},
            {"role": "assistant", "content": answer, "sources": new_sources}
        ])
        
        save_user_data(
            st.session_state.user_email,
            st.session_state.user_name,
            st.session_state.chat_history
        )
        st.rerun()

# --------- PAGE ROUTER ---------
if "page" not in st.session_state:
    st.session_state.page = "home"

if st.session_state.page == "home":
    show_home()
else:
    if st.session_state.current_chat_id:
        show_qa_page()
    else:
        st.warning("No active chat session. Please create a new chat.")