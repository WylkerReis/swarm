# 💠 Camomis AI Factory

A professionalized software engineering factory powered by a 7-agent CrewAI team and Gemini LLMs. Featuring a high-fidelity NASA-inspired Glassmorphism Dashboard.

## 🚀 Overview

Camomis AI Factory automates the full software development lifecycle (SDLC) using specialized AI agents.

## ⚙️ How to Run

Since the project is now modularized, use the unified entry point **`main.py`**:

### 🌐 Web Dashboard (Recommended)
This launches the FastAPI server and opens your browser automatically.
```bash
.\venv\Scripts\python.exe main.py --ui
```

### 💻 Terminal Factory (CLI)
Run the loop directly in your terminal.
```bash
.\venv\Scripts\python.exe main.py
```

### 🔍 Diagnostic Mode
Check which Gemini models are available for your API Key.
```bash
.\venv\Scripts\python.exe main.py --check
```

---

## 🛠️ Project Structure (Modular)

- **`app/core/`**: The "brain" of the factory (Agents, Tasks, Tools, and Crew Manager).
- **`app/api/`**: The FastAPI server logic.
- **`app/utils/`**: Maintenance and diagnostic scripts.
- **`public/`**: Frontend assets (HTML, CSS, JS).
- **`main.py`**: Unified entry point for all operations.

## 🛰️ Setup

1. **Environment**:
   Ensure you have a `.env` file with your `GEMINI_API_KEY`.
2. **Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
