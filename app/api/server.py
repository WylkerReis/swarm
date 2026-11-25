import os
import sys
import time
import json
import asyncio
import threading
import webbrowser
from queue import Queue, Empty
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.core.crew_manager import get_crew_config, create_crew_tasks
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

# Rastreamento de Cotas
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

        if "Working on" in clean_msg or "Agent task" in clean_msg:
            quota_stats["total_requests"] += 1
            quota_stats["current_rpm"] += 1

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
        elif any(x in clean_msg.upper() for x in ["ERRO", "FALHA", "WARNING", "MUDANDO PARA"]):
            friendly_msg = clean_msg

        if friendly_msg:
            self.queue.put(friendly_msg)

    def flush(self):
        self.terminal.flush()

    def isatty(self):
        return self.terminal.isatty()

    def fileno(self):
        return self.terminal.fileno()

# Redireciona stdout para capturar logs do CrewAI
sys.stdout = StreamCapture(stream_queue)

# --- Endpoints ---

@app.get("/stream")
async def stream_logs(request: Request):
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            
            now = time.time()
            if now - quota_stats["last_reset"] > 60:
                quota_stats["current_rpm"] = 0
                quota_stats["last_reset"] = now

            try:
                message = stream_queue.get_nowait()
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
            config = get_crew_config()
            crew_obj = config["crew"]
            agents = config["agents"]
            llms = config["llms"]
            
            # Tarefas
            crew_obj.tasks = create_crew_tasks(agents, user_request)
            
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
                        
                        # Fallback dinâmico
                        primary_model = llms["primary"].model
                        using_power = any(a.llm.model == primary_model for a in crew_obj.agents)
                        
                        if using_power:
                            stream_queue.put("⚠️ COTA POTENTE EXCEDIDA. MIGRANDO PARA MOTORES DE 1.500 RPD...")
                            for agent in crew_obj.agents:
                                agent.llm = llms["quota"]
                            
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

@app.get("/files/{file_path:path}")
async def get_file(file_path: str):
    root = os.path.realpath(os.getcwd())
    path = os.path.realpath(os.path.join(root, file_path))
    # Só serve arquivos dentro da pasta do projeto (bloqueia caminhos absolutos e '..').
    if os.path.commonpath([root, path]) != root or not os.path.isfile(path):
        return JSONResponse({"error": "File not found"}, status_code=404)
    with open(path, "r", encoding="utf-8") as f:
        return {"content": f.read()}

# Servir o Dashboard a partir da pasta 'public'
if os.path.exists("public"):
    app.mount("/", StaticFiles(directory="public", html=True), name="public")

def start_server(host="0.0.0.0", port=8000):
    import uvicorn
    # Inicia o navegador em paralelo
    def open_link():
        time.sleep(2)
        webbrowser.open(f"http://localhost:{port}")
    
    threading.Thread(target=open_link, daemon=True).start()
    uvicorn.run(app, host=host, port=port)
