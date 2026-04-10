import os
import sys
import time
import json
import asyncio
import threading
import webbrowser
from queue import Queue, Empty
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from crewai import Crew, Process, LLM
from tools import write_file_tool, read_file_tool, git_commit_tool, generate_ui_mockup_tool, ask_human_tool
from agents import create_business_analyst, create_product_manager, create_tech_lead, create_senior_developer, create_qa_engineer, create_technical_writer, create_ux_designer
from tasks import create_ba_task, create_pm_task, create_arch_task, create_dev_task, create_qa_task, create_docs_task, create_ux_task
from dotenv import load_dotenv

# Configurações Iniciais
load_dotenv()
app = FastAPI(title="Camomis AI Factory API")

# Middleware para CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Fila global para logs (SSE)
stream_queue = Queue()

# Rastreamento de Cotas (Baseado nos limites reais do usuário)
quota_stats = {
    "total_requests": 0,
    "current_rpm": 0,
    "last_reset": time.time(),
    "max_rpd": 1500,
    "max_rpm": 15
}

class StreamCapture:
    def __init__(self, queue):
        self.queue = queue
        self.terminal = sys.stdout

    def write(self, message):
        self.terminal.write(message)
        clean_msg = message.strip()
        if not clean_msg:
            return

        # 1. Rastreamento de Cotas (Sempre conta, mesmo se filtrado do log visual)
        if "Working on" in clean_msg or "Agent task" in clean_msg:
            quota_stats["total_requests"] += 1
            quota_stats["current_rpm"] += 1

        # 2. Filtro Amigável (Decide o que vai para o Dashboard)
        friendly_msg = None
        
        if "Working on" in clean_msg:
            agent_name = clean_msg.split("Working on")[-1].strip().replace("#", "")
            friendly_msg = f"💠 [SISTEMA] {agent_name} assumiu o comando da operação..."
        
        elif "Action:" in clean_msg:
            tool_name = clean_msg.split("Action:")[-1].strip()
            friendly_msg = f"⚙️ [FERRAMENTA] Executando: {tool_name}"
            
        elif "Final Answer:" in clean_msg:
            friendly_msg = "✅ [SUCESSO] Tarefa concluída com resposta final."
            
        elif "Task output:" in clean_msg:
            friendly_msg = "📄 [RESULTADO] Gerando saída da tarefa..."

        elif "I now know the final answer" in clean_msg:
             friendly_msg = "💡 [INSIGHT] Solução identificada. Consolidando..."

        # Mantém mensagens de erro e alertas de sistema
        elif any(x in clean_msg.upper() for x in ["ERRO", "FALHA", "WARNING", "MUDANDO PARA"]):
            friendly_msg = clean_msg

        # Se houver uma versão amigável, envia para a fila do Dashboard
        if friendly_msg:
            self.queue.put(friendly_msg)

    def flush(self):
        self.terminal.flush()

    def isatty(self):
        """Permite que o Uvicorn e outras libs verifiquem se é um terminal interativo."""
        return self.terminal.isatty()

    def fileno(self):
        """Retorna o descritor de arquivo do terminal original."""
        return self.terminal.fileno()

# Redireciona stdout para capturar logs do CrewAI
sys.stdout = StreamCapture(stream_queue)

# --- Lógica de Motor Híbrido (Copiada do main.py) ---
def get_crew():
    # Usando o prefixo direto para evitar que o LiteLLM tente OpenAI por engano
    # Motor de Alta Performance (Usa o alias que aponta para as novidades do Google)
    llm_power_primary = LLM(model="gemini/gemini-flash-latest", temperature=0.2)
    # Motor de Alta Cota (ID Fixo de 1.500 requisições por dia - Resiliente)
    llm_high_quota = LLM(model="gemini/gemini-1.5-flash", temperature=0.4)
    
    # Nota: Removi a OPENAI_API_KEY fictícia para evitar chamadas fantasmas.
    # O sistema agora deve usar apenas as chaves do Gemini/Google.

    tools_for_ba = [read_file_tool, ask_human_tool]
    tools_for_dev = [write_file_tool]
    tools_for_qa = [read_file_tool, write_file_tool, git_commit_tool]
    tools_for_ux = [read_file_tool, generate_ui_mockup_tool]
    
    ba = create_business_analyst(tools_for_ba, llm_high_quota)
    pm = create_product_manager(llm_high_quota)
    arquiteto = create_tech_lead(llm_high_quota)
    ux = create_ux_designer(tools_for_ux, llm_high_quota)
    dev = create_senior_developer(tools_for_dev, llm_power_primary)
    qa = create_qa_engineer(tools_for_qa, llm_power_primary)
    doc_writer = create_technical_writer(tools_for_dev, llm_high_quota)

    return Crew(
        agents=[ba, pm, arquiteto, ux, dev, qa, doc_writer],
        process=Process.sequential, 
        verbose=True,
        memory=True,
        # Força o uso do modelo de alta cota para gerenciar a memória
        memory_config={
            "provider": "google-generativeai",
            "config": {
                "model": "gemini-flash-latest",
                "api_key": os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
            }
        },
        embedder={
            "provider": "google-generativeai",
            "config": {
                "model": "models/embedding-001",
                "task_type": "retrieval_document"
            }
        }
    ), ba, pm, arquiteto, ux, dev, qa, doc_writer, llm_power_primary, llm_high_quota

# --- Endpoints ---

@app.get("/stream")
async def stream_logs(request: Request):
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            
            # Reset de RPM a cada minuto
            now = time.time()
            if now - quota_stats["last_reset"] > 60:
                quota_stats["current_rpm"] = 0
                quota_stats["last_reset"] = now

            try:
                message = stream_queue.get_nowait()
                # Envia o log E as estatísticas de cota juntas
                payload = {
                    'message': message,
                    'quota': {
                        'rpm': quota_stats['current_rpm'],
                        'rpd': quota_stats['total_requests'],
                        'max_rpm': quota_stats['max_rpm'],
                        'max_rpd': quota_stats['max_rpd']
                    }
                }
                yield f"data: {json.dumps(payload)}\n\n"
            except Empty:
                # Envia pulso de quota mesmo sem log
                payload = {
                    'quota': {
                        'rpm': quota_stats['current_rpm'],
                        'rpd': quota_stats['total_requests']
                    }
                }
                yield f"data: {json.dumps(payload)}\n\n"
                await asyncio.sleep(1.0)
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/run")
async def run_factory(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    user_request = data.get("prompt", "")
    
    def run_crew_logic():
        try:
            crew_obj, ba, pm, arquiteto, ux, dev, qa, doc_writer, p_llm, f_llm = get_crew()
            
            # Tarefas
            ba_task = create_ba_task(ba, user_request)
            pm_task = create_pm_task(pm, ba_task)
            arch_task = create_arch_task(arquiteto, pm_task)
            ux_task = create_ux_task(ux, arch_task)
            dev_task = create_dev_task(dev, arch_task, ux_task)
            qa_task = create_qa_task(qa, dev_task)
            docs_task = create_docs_task(doc_writer, qa_task)

            crew_obj.tasks = [ba_task, pm_task, arch_task, ux_task, dev_task, qa_task, docs_task]
            
            # Execução com Hot Swap e Pausa de Segurança
            retry_count = 0
            while retry_count < 3:
                try:
                    crew_obj.kickoff()
                    stream_queue.put("✅ PROCESSO FINALIZADO COM SUCESSO!")
                    break
                except Exception as e:
                    err_msg = str(e).upper()
                    if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                        retry_count += 1
                        
                        # Verifica se ainda estamos usando o motor potente em algum agente
                        using_power = any(a.llm.model == "gemini/gemini-flash-latest" for a in crew_obj.agents)
                        
                        if using_power:
                            stream_queue.put("⚠️ COTA POTENTE EXCEDIDA. MIGRANDO PARA MOTORES DE 1.500 RPD...")
                            for agent in crew_obj.agents:
                                agent.llm = f_llm # Unifica todo o time no motor de alta cota
                            
                            stream_queue.put("⏳ AGUARDANDO 30 SEGUNDOS PARA LIBERAÇÃO DE JANELA...")
                            time.sleep(30)
                            continue
                        else:
                            stream_queue.put("❌ COTA TOTAL ESGOTADA (1.500 RPD). Tente novamente mais tarde.")
                            break
                    else:
                        stream_queue.put(f"❌ ERRO CRÍTICO: {str(e)}")
                        break
        except Exception as e:
            stream_queue.put(f"❌ FALHA NA INICIALIZAÇÃO: {str(e)}")

    background_tasks.add_task(run_crew_logic)
    return {"status": "started"}

# Servir mockups e arquivos gerados (para a aba de Code Viewer)
@app.get("/files/{file_path:path}")
async def get_file(file_path: str):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return {"content": f.read()}
    return {"error": "File not found"}

# Servir o Frontend
if os.path.exists("frontend"):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

def start_browser():
    time.sleep(2)
    webbrowser.open("http://localhost:8000")

if __name__ == "__main__":
    import uvicorn
    # Abre o navegador em uma thread separada
    threading.Thread(target=start_browser, daemon=True).start()
    uvicorn.run(app, host="0.0.0.0", port=8000)
