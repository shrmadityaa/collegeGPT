# capstone_collegegpt
This is the one and only file for the project named: collegeGPT


CollegeGPT is a fully local RAG (Retrieval-Augmented Generation) based academic assistant that answers questions from uploaded college syllabus PDFs.

The system:
- extracts text from syllabus PDFs
- preprocesses and chunks content semantically
- generates embeddings locally
- stores embeddings in FAISS vector database
- retrieves relevant chunks
- generates contextual answers using a local LLM via Ollama

No paid APIs are used.

---

# 🚀 Features

- 📄 PDF syllabus ingestion
- 🧠 Semantic chunking
- 🔍 Vector similarity search using FAISS
- 🤖 Local LLM integration with Ollama
- 💬 Interactive chatbot UI using Streamlit
- 🔒 Fully local and privacy-friendly
- ⚡ No OpenAI or paid APIs required

---

# 🏗️ Tech Stack

- Python
- Streamlit
- FAISS
- Sentence Transformers
- Ollama
- Phi-3 Mini
- PyMuPDF

---

# 📂 Project Structure

```plaintext
collegeGPT/
│
├── app.py
├── ingest.py
├── requirements.txt
│
├── data/
│   ├── raw_pdfs/
│   ├── extracted_text/
│   └── processed_chunks/
│
├── vectorstore/
│   ├── collegegpt.index
│   └── chunks.pkl
│
├── src/
│   ├── extractor/
│   ├── parser/
│   ├── chunker/
│   ├── embed_store.py
│   ├── retrieve.py
│   └── rag_chat.py
│
└── tests/
```

---

# ⚙️ Installation Setup

## 1. Clone Repository

```bash
git clone <your-repo-link>
cd collegeGPT
```

---

## 2. Create Virtual Environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Mac/Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# 🦙 Install Ollama

Download and install Ollama:

https://ollama.com

---

# 📥 Download Local LLM

Run:

```bash
ollama pull phi3:mini
```

Verify installation:

```bash
ollama list
```

Expected:

```plaintext
phi3:mini
```

---

# 📄 Add PDF

Place syllabus PDF inside:

```plaintext
data/raw_pdfs/
```

Example:

```plaintext
data/raw_pdfs/syllabus.pdf
```

---

# 🧠 Generate Embeddings

Run:

```bash
python -m src.embed_store
```

This will:
- extract chunks
- generate embeddings
- create FAISS vector database

Generated files:

```plaintext
vectorstore/collegegpt.index
vectorstore/chunks.pkl
```

---

# 💬 Run Chatbot

## Terminal Version

```bash
python -m src.rag_chat
```

---

# 🌐 Run Frontend

```bash
streamlit run app.py
```

Expected:

```plaintext
http://localhost:8501
```

---

# 🧪 Example Questions

- What is pumping lemma?
- Explain Turing machine.
- What are the course objectives of Theory of Computation?
- Which course teaches machine learning?
- Credits of Ethical Hacking?

---

# 📌 Current Capabilities

✅ PDF ingestion  
✅ Semantic syllabus parsing  
✅ Semantic chunking  
✅ Local embeddings  
✅ FAISS vector database  
✅ Semantic retrieval  
✅ Local LLM answering  
✅ Streamlit frontend  

---

# 🔮 Future Improvements

- Multi-PDF support
- Automatic ingestion after upload
- Chat memory
- Hybrid search (BM25 + embeddings)
- Citation highlighting
- Better UI/UX
- Authentication system
- Admin dashboard

---

# 👥 Team Notes

Important:
- Ollama must be running before using the chatbot.
- First query may take longer due to model loading.
- Embeddings must be regenerated when new PDFs are added.

---

# 📜 License

This project is for academic and educational purposes.
