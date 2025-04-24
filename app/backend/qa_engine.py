import os
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image

# Load environment variables from .env file
load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyCH9Rnf6PAmR0IpqUzcKH9WZEQBxYVY168"
#AIzaSyAnfqjCG3sDs3QcopuRXAlGXM2SuIZplS8
#AIzaSyDccyz5uH_a1vZTNGvxOeATRXyR45k21os
if not GEMINI_API_KEY:
    raise ValueError("Missing GEMINI_API_KEY in .env")

genai.configure(api_key=GEMINI_API_KEY)

# Load models
# Updated model initialization
text_model = genai.GenerativeModel("gemini-2.5-pro-exp-03-25")
vision_model = genai.GenerativeModel("gemini-2.5-pro-exp-03-25")



def answer_question(question, text_chunks, named_dfs=None, image_files=None):
    text_context = "\n\n".join([text for text, _ in text_chunks])

    # Create DataFrame description only if named_dfs exist
    if named_dfs:
        df_info = "\n".join([
            f"- `{name}` (from file '{filename}'): columns = {list(df.columns)}"
            for name, (df, filename) in named_dfs.items()
        ])
        df_section = f"""
You have access to the following DataFrames (from uploaded files):
{df_info}
"""
    else:
        df_section = ""

    prompt = f"""
You are a data analyst assistant. Your task is to answer the user's question using the provided context. 

The context contains:
- Textual information from documents or images
- {'Summarized content and structure of uploaded data files (as named DataFrames)' if named_dfs else 'No structured data was provided'}
- The user’s question at the end
{df_section}

Only use the provided context. Do not assume access to any other files or data.

When answering:
- If the answer can be found from text, provide it directly.
- If answering requires analyzing a DataFrame, write Python code to do so.
- If a plot or chart helps answer the question, use Plotly (`plotly.express`) and generate code to create the chart.
- Do **not** use libraries like `os`, `io`, or `sys`.
- Do **not** try to read files from disk or use file paths.
- Wrap all code **only** in triple backticks (` ```python `) without extra explanation unless asked.
- Don't use fig.show() or plt.show() in the code. 
- If the answer is a simple text, provide it directly without code.
- If the answer is not found in the context, say "I don't know" or "I cannot answer that based on the provided context. If a certain piece of information is missing, ask the user to provide it."

Context:
{text_context}

Question:
{question}
"""

    try:
        if image_files:
            images = [Image.open(img) for img in image_files]
            response = vision_model.generate_content([prompt] + images)
        else:
            response = text_model.generate_content(prompt)

        return response.text.strip()

    except Exception as e:
        return f"⚠️ Gemini API Error: {str(e)}"


