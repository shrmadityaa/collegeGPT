````markdown
# 🎓 CollegeGPT

CollegeGPT is a fully local RAG (Retrieval-Augmented Generation) based academic assistant that answers questions from uploaded college syllabus PDFs and academic documents.

The system extracts information from PDFs, processes them into semantic chunks, stores them in a vector database, retrieves relevant information using semantic search, and generates grounded responses using a local LLM.

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
- 📚 Metadata-aware academic retrieval
- 🏗️ Hybrid semantic + structured retrieval

---

# 🏗️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core backend |
| Streamlit | Frontend UI |
| FAISS | Vector database |
| Sentence Transformers | Embedding generation |
| Ollama | Local LLM serving |
| Phi-3 Mini | Local language model |
| PyMuPDF | PDF text extraction |

---

# 📂 Project Structure

```plaintext
collegeGPT/
│
├── app.py
├── ingest.py
├── requirements.txt
├── README.md
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
│   │   └── text_extraction.py
│   │
│   ├── parser/
│   │   ├── detailed_syllabus_parser.py
│   │   ├── metadata_parser.py
│   │   ├── regex_patterns.py
│   │   ├── syllabus_parser.py
│   │   └── table_parser.py
│   │
│   ├── chunker/
│   │   └── chunker.py
│   │
│   ├── embed_store.py
│   ├── retrieve.py
│   └── rag_chat.py
│
└── tests/
````

---

# 🧠 System Architecture

CollegeGPT follows a Retrieval-Augmented Generation (RAG) architecture.

```plaintext
                User Question
                       │
                       ▼
              Query Embedding
                       │
                       ▼
              FAISS Vector Search
                       │
                       ▼
            Relevant Text Chunks
                       │
                       ▼
              Prompt Construction
                       │
                       ▼
             Local LLM (Phi-3)
                       │
                       ▼
                 Final Answer
```

The system combines:

* semantic retrieval
* structured metadata retrieval
* local LLM generation

to provide grounded academic responses.

---

# 🔄 Document Processing Pipeline

```plaintext
PDF Document
      │
      ▼
Text Extraction (PyMuPDF)
      │
      ▼
Cleaning & Preprocessing
      │
      ▼
Semantic Chunking
      │
      ▼
Embedding Generation
      │
      ▼
FAISS Vector Storage
```

This pipeline enables efficient semantic retrieval during question answering.

---

# ⚙️ Installation Setup

## 1. Clone Repository

```bash
git clone <your-repository-link>
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

[https://ollama.com](https://ollama.com)

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

# 📄 Add PDF Documents

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

This process:

* parses PDFs
* creates semantic chunks
* creates metadata chunks
* generates embeddings
* stores embeddings in FAISS

Generated files:

```plaintext
vectorstore/collegegpt.index
vectorstore/chunks.pkl
```

---

# 💬 Run Chatbot (Terminal)

```bash
python -m src.rag_chat
```

---

# 🌐 Run Streamlit Frontend

```bash
streamlit run app.py
```

Expected:

```plaintext
http://localhost:8501
```

---

# 🏗️ Internal Modules

| Module      | Responsibility                      |
| ----------- | ----------------------------------- |
| extractor   | Extracts raw text from PDFs         |
| parser      | Detects courses, sections, metadata |
| chunker     | Creates semantic chunks             |
| embed_store | Generates embeddings & FAISS index  |
| retrieve    | Retrieves relevant chunks           |
| rag_chat    | Connects retriever with LLM         |
| app.py      | Streamlit frontend                  |

---

# ⚡ Retrieval Workflow

```plaintext
User Query
    │
    ▼
SentenceTransformer Embedding
    │
    ▼
FAISS Similarity Search
    │
    ▼
Top-K Relevant Chunks
    │
    ▼
Prompt Builder
    │
    ▼
Phi-3 Mini via Ollama
    │
    ▼
Generated Answer
```

---

# 📊 Example Metadata Chunk

The system generates structured metadata chunks for reliable academic retrieval.

Example:

```plaintext
Operating Systems (UCS303)
is taught in Third Semester.
The LTP structure is 3-0-2.
The course carries 4.0 credits.
```

These chunks improve:

* semester queries
* credits queries
* course lookup
* elective retrieval

---

# 🧩 Current RAG Features

## ✅ Implemented

* PDF text extraction
* Semantic chunking
* Metadata chunk generation
* Vector similarity search
* Local embedding generation
* Local LLM inference
* Streamlit frontend
* Hybrid structured + semantic retrieval

---

## 🚧 In Progress

* Query routing
* Metadata database optimization
* Better chunk hierarchy
* Hybrid keyword + semantic retrieval
* Automatic ingestion after upload

---

## 🔮 Planned

* Multi-document support
* Conversation memory
* Citation highlighting
* Authentication system
* Admin dashboard
* Better UI/UX

---

# 🎯 Design Goals

The project aims to build a fully local academic assistant that:

* avoids paid APIs
* supports semantic document search
* provides grounded academic answers
* scales to multiple academic PDFs
* remains lightweight for student laptops

Primary focus areas:

* reliability
* retrieval quality
* modular architecture
* privacy-friendly deployment

---

# 🔒 Why Local RAG?

CollegeGPT uses a fully local pipeline:

* local embeddings
* local vector database
* local LLM inference

Benefits:

* no API costs
* privacy-friendly
* offline capability
* educational understanding of RAG systems
* full control over architecture

---

# 🧪 Evaluation & Testing Strategy

The system is evaluated using multiple categories of prompts.

| Category               | Purpose                 |
| ---------------------- | ----------------------- |
| Metadata Questions     | Semester, credits, LTP  |
| Conceptual Questions   | Topic explanations      |
| Course Questions       | Objectives, CLOs, books |
| Retrieval Stress Tests | Semantic robustness     |
| Adversarial Tests      | Hallucination detection |

This evaluation-driven development approach helps improve:

* retrieval accuracy
* hallucination resistance
* metadata grounding
* response reliability

---

# 🧪 Example Questions

## Metadata Queries

* What are the credits of Ethical Hacking?
* Which semester contains DBMS?
* What is the LTP structure of Operating Systems?
* List courses in fifth semester.

---

## Conceptual Queries

* What is pumping lemma?
* Explain Turing machine.
* What are regular languages?
* Explain context free grammar.

---

## Course Queries

* What are the course objectives of Theory of Computation?
* What books are recommended for Operating Systems?
* What topics are taught in DBMS?

---

# 👥 Team Notes

Important:

* Ollama must be running before using the chatbot.
* First query may take longer due to model loading.
* Embeddings must be regenerated when new PDFs are added.
* Use the same Python version for compatibility.

---

# 📌 Future Vision

CollegeGPT aims to evolve into:

* a university-wide academic assistant
* multi-document intelligent retrieval system
* semester planner
* course recommendation assistant
* academic knowledge search engine

---

# 📜 License

This project is for academic and educational purposes.

```
```
