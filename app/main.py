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
import pandas as pd
import contextlib
import io
import re
import plotly.graph_objects as go
from backend.link_crawler import extract_text_from_url

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

def extract_links(text):
    # Basic regex to find URLs
    url_pattern = r'https?://[^\s]+'
    return re.findall(url_pattern, text)

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
    st.sidebar.title(f" Hey, {st.session_state.user_name}")
    
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
        
        def get_df_sample_with_columns(df, filename, max_rows=5):
            sample = df.head(max_rows).to_markdown(index=False)  # For a readable format
            return f"Sample from '{filename}':\n{sample}\n"
        named_dfs = {}  # key: df name (e.g., df1), value: (df, filename)
        df_samples_text = "" 
        if uploaded_files:
            with st.spinner("Processing documents..."):
                structured_dfs = []  # Store structured DataFrames
                for file in uploaded_files:
                    ext = file.name.split('.')[-1].lower()
                    try:
                        if ext in ["png", "jpg", "jpeg"]:
                            text = ocr_image(file)
                            links = extract_links(text)
                            for link in links:
                                link_content = extract_text_from_url(link)
                                if link_content.strip():
                                    link_chunks = [(link_content[i:i+500], f"Link: {link}") for i in range(0, len(link_content), 500)]
                                    new_text_chunks.extend(link_chunks)
                                    new_sources.append(link)
                            chunks = [(text[i:i+500], file.name) for i in range(0, len(text), 500)]
                            new_text_chunks.extend(chunks)
                            new_sources.append(file.name)

                        elif ext in ["pdf", "txt"]:
                            text = parse_file(file, ext)
                            links = extract_links(text)
                            for link in links:
                                link_content = extract_text_from_url(link)
                                if link_content.strip():
                                    link_chunks = [(link_content[i:i+500], f"Link: {link}") for i in range(0, len(link_content), 500)]
                                    new_text_chunks.extend(link_chunks)
                                    new_sources.append(link)
                            chunks = [(text[i:i+500], file.name) for i in range(0, len(text), 500)]
                            new_text_chunks.extend(chunks)
                            new_sources.append(file.name)

                        elif ext in ["csv", "xlsx", "json"]:
                            df = load_structured_file(file, ext)
                            if isinstance(df, pd.DataFrame):
                                structured_dfs.append((df, file.name))
                            else:
                                st.error(f"Failed to load {file.name}: {df}")

                        elif ext == "pptx":
                            result = parse_file(file,ext)  # returns dict with "text" and "images"
                            if isinstance(result, dict):
                                # Process text
                                text = result["text"]
                                links = extract_links(text)
                                for link in links:
                                    link_content = extract_text_from_url(link)
                                    if link_content.strip():
                                        link_chunks = [(link_content[i:i+500], f"Link: {link}") for i in range(0, len(link_content), 500)]
                                        new_text_chunks.extend(link_chunks)
                                        new_sources.append(link)
                                chunks = [(text[i:i+500], file.name) for i in range(0, len(text), 500)]
                                new_text_chunks.extend(chunks)

                                # Optionally OCR each extracted image
                                for image_path in result["images"]:
                                    image_text = ocr_image(image_path)
                                    img_chunks = [(image_text[i:i+500], f"{file.name} (image)") for i in range(0, len(image_text), 500)]
                                    new_text_chunks.extend(img_chunks)

                                new_sources.append(file.name)
                            else:
                                st.error(f"Failed to process {file.name}: {result}")
                    except Exception as e:
                        st.error(f"Error processing {file.name}: {e}")


                    except Exception as e:
                        st.error(f"Error processing {file.name}: {str(e)}")
                        continue

                named_dfs = {}  # key: df name (e.g., df1), value: (df, filename)
                df_samples_text = ""

                if structured_dfs:
                    for i, (df, filename) in enumerate(structured_dfs):
                        df_name = f"df{i+1}"
                        named_dfs[df_name] = (df, filename)

                        # Create sample preview
                        sample = df.head(5).to_markdown()
                        columns = list(df.columns)
                        df_samples_text += f"Dataset `{df_name}` from file '{filename}':\nColumns: {columns}\nSample rows:\n{sample}\n\n"



                if new_text_chunks:
                    st.session_state.chat_history = update_chat_context(
                        st.session_state.current_chat_id,
                        new_text_chunks,
                        new_sources,
                        st.session_state.chat_history
                    )
                    add_to_index(new_text_chunks)
     

        context_results = get_contextual_results(
            st.session_state.current_chat_id,
            question,
            st.session_state.chat_history
        )

        combined_text_chunks = [(df_samples_text, "structured_dfs_summary")] + context_results
        

        with st.spinner("Analyzing your question..."):
            try:
                answer = answer_question(question, combined_text_chunks, named_dfs=named_dfs)

                code_blocks = re.findall(r"```(?:python)?\s*([\s\S]*?)```", answer)

                for code in code_blocks:
                    local_vars = {}
                    exec_globals = globals().copy()

                    # Inject dataframes
                    for df_name, (df, filename) in named_dfs.items():
                        exec_globals[df_name] = df

                    # ✅ Replace print() with st.write() before running the whole block
                    code = code.replace("print(", "st.write(")

                    code = code.replace("fig.show()", "")

                    buffer = io.StringIO()
                    with contextlib.redirect_stdout(buffer):
                        try:
                            exec(code, exec_globals, local_vars)
                        except Exception as e:
                            st.error(f"Error in code execution: {e}")

                    # Show any figures
                    for idx, var in enumerate(local_vars.values()):
                        if isinstance(var, go.Figure):
                            st.plotly_chart(var, use_container_width=True, key=f"plot_{idx}")

                # ✅ Show final answer (without code block, clean if needed)
                cleaned_answer = re.sub(r"```(?:python)?\s*([\s\S]*?)```", "", answer).strip()
                if cleaned_answer:
                    st.markdown(cleaned_answer)

            except Exception as e:
                st.error(f"Sorry, I encountered an error: {str(e)}")



        # Update chat history
        current_chat.setdefault("messages", []).extend([
            {"role": "user", "content": question, "sources": new_sources},
            {"role": "assistant", "content": cleaned_answer, "sources": new_sources}
        ])
        
        save_user_data(
            st.session_state.user_email,
            st.session_state.user_name,
            st.session_state.chat_history
        )
        if st.button("Ask another question"):
            st.rerun()


if "page" not in st.session_state:
    st.session_state.page = "home"

if st.session_state.page == "home":
    show_home()
else:
    if st.session_state.current_chat_id:
        show_qa_page()
    else:
        st.warning("No active chat session. Please create a new chat.")