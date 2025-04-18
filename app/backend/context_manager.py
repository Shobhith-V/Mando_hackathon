import json
import os
import datetime

DATA_DIR = "app/local"
DEFAULT_CHAT = {
    "title": "New Chat",
    "messages": [],
    "context": {
        "text_chunks": [],
        "sources": []
    }
}

def save_user_data(email, name, chat_history):
    if not email:
        return
    
    os.makedirs(DATA_DIR, exist_ok=True)
    filepath = os.path.join(DATA_DIR, f"{email}.json")
    
    data = {
        "version": "1.2",
        "name": name,
        "email": email,
        "chat_history": chat_history,
        "last_updated": str(datetime.datetime.now())
    }
    
    try:
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving user data: {str(e)}")

def load_user_data(email):
    if not email:
        return {}
    
    filepath = os.path.join(DATA_DIR, f"{email}.json")
    if not os.path.exists(filepath):
        return {}
    
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading user data: {str(e)}")
        return {}

def migrate_chat_history(chat_history):
    migrated = {}
    for cid, chat in chat_history.items():
        if not isinstance(chat, dict):
            # Legacy format migration
            new_id = f"chat_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
            migrated[new_id] = DEFAULT_CHAT.copy()
            migrated[new_id]["messages"] = chat
            # Use first message as title if available
            if len(chat) > 0 and chat[0].get("role") == "user":
                first_question = chat[0].get("content", "New Chat")
                migrated[new_id]["title"] = first_question[:50] + "..." if len(first_question) > 50 else first_question
            else:
                migrated[new_id]["title"] = "Previous Chat"
        else:
            # Preserve existing titles when fixing IDs
            if '_' not in cid or len(cid.split('_')[1]) != 14:
                new_id = f"chat_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
                migrated[new_id] = {
                    "title": chat.get("title", "New Chat"),  # Use original title if exists
                    "messages": chat.get("messages", []),
                    "context": chat.get("context", DEFAULT_CHAT["context"].copy())
                }
            else:
                migrated[cid] = {
                    "title": chat.get("title", "New Chat"),  # Preserve original title
                    "messages": chat.get("messages", []),
                    "context": chat.get("context", DEFAULT_CHAT["context"].copy())
                }
    return migrated

def update_chat_context(chat_id, text_chunks, sources, chat_history):
    if chat_id not in chat_history:
        return chat_history
    
    chat = chat_history[chat_id]
    chat["context"] = chat.get("context", DEFAULT_CHAT["context"].copy())
    chat["context"]["text_chunks"].extend(text_chunks)
    chat["context"]["sources"].extend(sources)
    return chat_history

def get_contextual_results(chat_id, query, chat_history, top_k=5):
    from backend.semantic_search import model
    import numpy as np
    
    chat = chat_history.get(chat_id, DEFAULT_CHAT.copy())
    context = chat.get("context", DEFAULT_CHAT["context"].copy())
    text_chunks = context.get("text_chunks", [])
    
    if not text_chunks:
        return []
    
    try:
        embeddings = model.encode([chunk[0] for chunk in text_chunks])
        query_embedding = model.encode([query])
        scores = np.dot(embeddings, query_embedding[0])
        top_indices = scores.argsort()[-top_k:][::-1]
        return [text_chunks[i] for i in top_indices]
    except Exception as e:
        print(f"Error in semantic search: {str(e)}")
        return []