# MemoryMesh

### AI-Powered Persistent Memory System

MemoryMesh is an AI-powered memory system designed to store, retrieve, and manage information through natural-language conversations. It combines semantic search, memory resolution, and language models to maintain useful context over time.

**Live Demo:** [https://memorymesh-hloe.onrender.com/](https://memorymesh-hloe.onrender.com/)

**API Documentation:** [https://memorymesh-api-kolz.onrender.com/docs](https://memorymesh-api-kolz.onrender.com/docs)

**Repository:** [https://github.com/csequenc/MemoryMesh](https://github.com/csequenc/MemoryMesh)

---

## 🚀 Features

- **Natural Language Memory Ingestion** – Save information through conversational input.
- **Semantic Search** – Retrieve relevant memories using vector embeddings.
- **Memory Resolution** – Identify duplicates, conflicts, and superseded information.
- **Persistent Storage** – Store memories in a structured database.
- **Knowledge Graph** – Visualize entities and relationships between memories.
- **Memory Management** – View, update, and delete stored memories.
- **AI-Powered Responses** – Generate contextual answers using retrieved memories.

## 🛠️ Tech Stack

| Layer           | Technology              |
| --------------- | ----------------------- |
| Backend         | Python, FastAPI         |
| Frontend        | React, TypeScript, Vite |
| Database        | SQLite, SQLAlchemy      |
| Embedding Model | all-MiniLM-L6-v2        |
| Model Runtime   | ONNX Runtime            |
| LLM Integration | Groq API                |
| Deployment      | Render                  |

## 🧠 How It Works

MemoryMesh follows a memory ingestion and retrieval pipeline.

```text
User Input
    |
    v
Memory Ingestion
    |
    v
Memory Processing
    |
    v
Memory Resolution
    |
    v
Database Storage
    |
    v
Semantic Retrieval
    |
    v
LLM Context Generation
    |
    v
AI Response
```

1. **Ingestion:** The user submits information through the chat interface.
2. **Processing:** The backend processes the input and identifies memory candidates.
3. **Resolution:** New information is checked against existing memories for duplicates, conflicts, and supersession.
4. **Storage:** Resolved memories are persisted in the database.
5. **Retrieval:** Semantic search retrieves relevant active memories for a query.
6. **Response:** Retrieved memories provide context for the language model to generate a response.

## 🏗️ Project Structure

```text
MemoryMesh/
│
├── app/
│   ├── api/
│   ├── database/
│   ├── ingestion/
│   ├── llm/
│   ├── retrieval/
│   └── resolution/
│
├── frontend/
│   └── src/
│
├── dev_tests/
│
├── requirements.txt
├── README.md
└── .gitignore
```

## ⚙️ Installation & Setup

### Prerequisites

- Python
- Node.js and npm
- Groq API key

### 1. Clone the Repository

```bash
git clone https://github.com/csequenc/MemoryMesh.git
cd MemoryMesh
```

### 2. Set Up the Backend

Install the dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
```

Start the backend:

```bash
uvicorn app.api.main:app --reload
```

Backend URL:

```text
http://127.0.0.1:8000
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

### 3. Set Up the Frontend

Open a new terminal:

```bash
cd frontend
npm install
```

Create a `.env` file inside the `frontend` directory:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Start the frontend:

```bash
npm run dev
```

Open the local URL provided by Vite.

## 🔍 Semantic Retrieval

MemoryMesh uses the `all-MiniLM-L6-v2` embedding model through ONNX Runtime.

- Generates semantic embeddings for memory retrieval.
- Uses ONNX Runtime for CPU-based inference.
- Loads the model lazily to reduce startup overhead.
- Uses a pinned model revision for reproducibility.

The ONNX implementation avoids the heavier PyTorch-based Sentence Transformers runtime, making deployment more suitable for resource-constrained environments.

## 🗄️ Database Design

MemoryMesh maintains separate databases for personal workflows and the public demo.

| Database             | Purpose                          |
| -------------------- | -------------------------------- |
| `memorymesh.db`      | Personal and local CLI workflows |
| `memorymesh_demo.db` | Public demo API                  |

The public API uses the demo database exclusively, keeping public demo activity separate from the personal database.

When the demo database is empty, fictional sample memories are automatically inserted. Existing demo data is not overwritten during subsequent startups.

## 🌐 Live Deployment

The application is deployed on Render.

| Service           | URL                                                                   |
| ----------------- | --------------------------------------------------------------------- |
| Frontend          | [MemoryMesh Live Demo](https://memorymesh-hloe.onrender.com/)         |
| Backend           | [MemoryMesh API](https://memorymesh-api-kolz.onrender.com/)           |
| API Documentation | [Interactive API Docs](https://memorymesh-api-kolz.onrender.com/docs) |

### Environment Variables

**Backend**

```env
GROQ_API_KEY=your_groq_api_key
FRONTEND_ORIGIN=https://memorymesh-hloe.onrender.com
```

**Frontend**

```env
VITE_API_BASE_URL=https://memorymesh-api-kolz.onrender.com
```

The Groq API key must remain on the backend and must never be exposed in frontend code.

## 🧪 Evaluation

The project includes a scenario-based evaluation suite in `dev_tests/`.

It covers:

- Duplicate detection
- Conflict handling
- Supersession
- Unrelated information
- Unresolved information

The recorded evaluation report contains **21 passing scenarios out of 25**. These are project-defined test scenarios, not an independent benchmark or a fresh evaluation of every deployed version.

## ⚠️ Demo Notes

- The public demo uses one shared database.
- Visitors can create, update, and delete demo memories.
- Changes may be visible to other visitors.
- The demo does not provide individual visitor accounts or isolated sessions.
- Demo data may be reset if the hosting platform replaces or resets its filesystem.
- Do not enter confidential or sensitive information into the public demo.

## 🔮 Future Improvements

Potential areas for further development include:

- Improved retrieval for broad and multi-part queries.
- More comprehensive automated evaluation.
- Enhanced memory visualization.
- Additional memory-management capabilities.

## 👨‍💻 Project

**MemoryMesh** — An exploration of persistent conversational memory, semantic retrieval, and intelligent memory resolution.

---

\<p align="center">   \<strong>Building AI systems that remember.\</strong> \</p>
