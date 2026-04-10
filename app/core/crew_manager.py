import os
from crewai import Crew, Process, LLM
from app.core.agents import (
    create_business_analyst, create_product_manager, create_tech_lead, 
    create_senior_developer, create_qa_engineer, create_technical_writer, create_ux_designer
)
from app.core.tasks import (
    create_ba_task, create_pm_task, create_arch_task, 
    create_dev_task, create_qa_task, create_docs_task, create_ux_task
)
from app.core.tools import write_file_tool, read_file_tool, git_commit_tool, generate_ui_mockup_tool, ask_human_tool

def get_crew_config():
    """Configura e retorna a equipe (Crew) e seus componentes básicos."""
    # Motores LLM
    llm_power_primary = LLM(model="gemini/gemini-flash-latest", temperature=0.2)
    llm_high_quota = LLM(model="gemini/gemini-1.5-flash", temperature=0.4)
    
    # Ferramentas por Agente
    tools_for_ba = [read_file_tool, ask_human_tool]
    tools_for_dev = [write_file_tool]
    tools_for_qa = [read_file_tool, write_file_tool, git_commit_tool]
    tools_for_ux = [read_file_tool, generate_ui_mockup_tool]
    
    # Instanciando Agentes
    ba = create_business_analyst(tools_for_ba, llm_high_quota)
    pm = create_product_manager(llm_high_quota)
    arquiteto = create_tech_lead(llm_high_quota)
    ux = create_ux_designer(tools_for_ux, llm_high_quota)
    dev = create_senior_developer(tools_for_dev, llm_power_primary)
    qa = create_qa_engineer(tools_for_qa, llm_power_primary)
    doc_writer = create_technical_writer(tools_for_dev, llm_high_quota)

    # Configuração da Equipe
    crew_obj = Crew(
        agents=[ba, pm, arquiteto, ux, dev, qa, doc_writer],
        process=Process.sequential, 
        verbose=True,
        memory=True,
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
    )
    
    return {
        "crew": crew_obj,
        "agents": {
            "ba": ba, "pm": pm, "arquiteto": arquiteto, "ux": ux, 
            "dev": dev, "qa": qa, "doc_writer": doc_writer
        },
        "llms": {
            "primary": llm_power_primary,
            "quota": llm_high_quota
        }
    }

def create_crew_tasks(agents_dict, user_request):
    """Cria a lista de tarefas baseada nos agentes e no pedido do usuário."""
    ba = agents_dict["ba"]
    pm = agents_dict["pm"]
    arquiteto = agents_dict["arquiteto"]
    ux = agents_dict["ux"]
    dev = agents_dict["dev"]
    qa = agents_dict["qa"]
    doc_writer = agents_dict["doc_writer"]

    ba_task = create_ba_task(ba, user_request)
    pm_task = create_pm_task(pm, ba_task)
    arch_task = create_arch_task(arquiteto, pm_task)
    ux_task = create_ux_task(ux, arch_task)
    dev_task = create_dev_task(dev, arch_task, ux_task)
    qa_task = create_qa_task(qa, dev_task)
    docs_task = create_docs_task(doc_writer, qa_task)

    return [ba_task, pm_task, arch_task, ux_task, dev_task, qa_task, docs_task]
