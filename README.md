# Mando_hackathon
# 📄 Mando AI Document Q&A Assistant

An intelligent, interactive Streamlit web app that enables users to upload documents and receive context-aware answers powered by an LLM. The app supports PDFs, images, CSVs, Excel files, text documents, JSON files, and URLs—extracting insights through semantic search, OCR, and executable code snippets.

---

## 🚀 Features

- 🔍 **Natural Language Q&A**: Ask questions about your uploaded files.
- 📊 **Structured Data Support**: Analyze and visualize data from `.csv`, `.xlsx`, and `.json`.
- 🧠 **Code-Driven Insights**: Executes LLM-generated Python code for deeper data analysis.
- 🖼️ **OCR for Images and PDFs**: Extracts text from scanned images and image-based PDFs.
- 🔗 **Web Link Crawling**: Detects and extracts content from links found in uploaded documents.
- 💬 **Chat Interface**: Maintains per-session Q&A chat history 
- 📈 **Plotly Visualizations**: Dynamic interactive charts from your data.

---

## 🧱 File Types Supported

| File Type | Use Case |
|-----------|----------|
| `.pdf`    | Text & scanned PDF with fallback OCR |
| `.txt`    | Plain text documents |
| `.csv`    | Structured data with semantic Q&A |
| `.xlsx`   | Excel files with multiple sheets supported |
| `.json`   | Structured data and nested objects |
| `.jpg`, `.jpeg`, `.png` | OCR-based image text extraction |
| Hyperlinks | Crawled and indexed into search context |

---

## 📦 Setup Instructions

The app has also been deployed on streamlit community, to access it directly from there https://teamrocket.streamlit.app/ use the following app, it will ask you for email and name for it to load the chat history and then you can view the app, load documents and ask questions. 

or you can follow the given instructions
### 1. Clone the Repo

```bash
git clone https://github.com/your-username/mando-ai-doc-qna.git
cd mando-ai-doc-qna

pip install -r requirements.txt

can use streamlit run app/main.py to run the code 


