# 💠 Camomis AI Factory

A advanced software engineering factory powered by a 7-agent CrewAI team and Gemini LLMs. Featuring a high-fidelity NASA-inspired Glassmorphism Dashboard.

## 🚀 Overview

Camomis AI Factory automates the full software development lifecycle (SDLC) using specialized AI agents that collaborate to translate user requirements into functional code, mockups, and documentation.

### 🤖 The Agent Team

- **Business Analyst**: Analyzes user requests and audits documentation.
- **Product Manager**: Extraction of business requirements and acceptance criteria.
- **Tech Lead**: Architectural design and database mapping.
- **UX Designer**: Generates visual mockups (NASA/Glassmorphism style).
- **Senior Developer**: Implements clean, SOLID-compliant code.
- **QA Engineer**: Automated testing (API + UI) and BDD validation.
- **Technical Writer**: Maintains the "living documentation" wiki.

## 🛠️ Stack

- **Backend**: Python, FastAPI, Uvicorn.
- **AI Orchestration**: CrewAI (Sequential Process).
- **LLMs**: Google Gemini (3 Flash & 1.5 Flash) with proactive fallback systems.
- **Frontend**: HTML5, Vanilla CSS (NASA Aesthetic), Javascript (SSE for real-time logs).

## ⚙️ Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/WylkerReis/Agente.git
   cd Agente
   ```

2. **Environment Variables**:
   Create a `.env` file with your Gemini API Key:
   ```env
   GEMINI_API_KEY=your_key_here
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Factory**:
   ```bash
   python server.py
   ```
   The dashboard will automatically open at `http://localhost:8000`.

## 🛰️ Dashboard Features

- **Real-time Logs**: SSE-powered terminal visualization with friendly status updates.
- **Resilient Motors**: Automatic transition between LLMs during quota exhaustion (429 errors).
- **Code Viewer**: Integrated viewer for files generated during the cycle.
- **Visual Mockups**: Real-time rendering of UI prototypes.
