import os
import time
from dotenv import load_dotenv
from crewai import Crew, Process, LLM
from tools import write_file_tool, read_file_tool, git_commit_tool
from agents import create_business_analyst, create_product_manager, create_tech_lead, create_senior_developer, create_qa_engineer, create_technical_writer, create_ux_designer
from tasks import create_ba_task, create_pm_task, create_arch_task, create_dev_task, create_qa_task, create_docs_task, create_ux_task
from tenacity import retry, stop_after_attempt, wait_exponential

def main():
    load_dotenv()
    
    # 0. Verificação de Chaves
    if "GEMINI_API_KEY" not in os.environ and "GOOGLE_API_KEY" not in os.environ:
        print("\n❌ ERRO: Nenhuma chave de API (GEMINI_API_KEY) encontrada no arquivo .env")
        return
    
    # Truque para contornar exigência interna de chave OpenAI no sistema de Memória do CrewAI
    if "OPENAI_API_KEY" not in os.environ:
        os.environ["OPENAI_API_KEY"] = "sk-placeholder-key-for-internal-validation"

    # 1. Instanciando os Motores (LLMs)
    # Primário Potente (5 RPM / 20 RPD) para Dev e QA
    llm_power_primary = LLM(model="gemini/gemini-3-flash-preview", temperature=0.2)
    # Utilitário e Fallback de Alta Autonomia (15 RPM / 1.500 RPD)
    # Este motor será fixo para os agentes de orquestração e servirá de reserva para o Dev/QA
    llm_high_quota = LLM(model="gemini/gemini-flash-latest", temperature=0.4)

    # 2. Instanciando Ferramentas e Agentes
    tools_for_ba = [read_file_tool]
    tools_for_dev = [write_file_tool]
    tools_for_qa = [read_file_tool, write_file_tool, git_commit_tool]
    
    # Agentes de orquestração e documentação FIXOS no motor de 1.500 RPD
    ba = create_business_analyst(tools_for_ba, llm_high_quota)
    pm = create_product_manager(llm_high_quota)
    arquiteto = create_tech_lead(llm_high_quota)
    ux = create_ux_designer(tools_for_ba, llm_high_quota)
    doc_writer = create_technical_writer(tools_for_dev, llm_high_quota)
    
    # Dev e QA começam com o motor primário potente (5 RPM) e possuem fallback para o llm_high_quota
    dev = create_senior_developer(tools_for_dev, llm_power_primary)
    qa = create_qa_engineer(tools_for_qa, llm_power_primary)

    # 3. Formando a Equipe (Crew) com MEMÓRIA Persistente
    equipe_dev = Crew(
        agents=[ba, pm, arquiteto, ux, dev, qa, doc_writer],
        process=Process.sequential, 
        verbose=True,
        memory=True,
        memory_llm=llm_high_quota, # Memória fixa no motor de 1.500 RPD
        embedder={
            "provider": "google-generativeai",
            "config": {
                "model": "models/gemini-embedding-001",
                "task_type": "retrieval_document",
                "title": "Memória da Equipe"
            }
        }
    )

    # 4. Função de Execução Resiliente com Fallback Dinâmico
    def executar_ciclo(user_request):
        # ... (criação de tarefas permanece igual) ...
        ba_task = create_ba_task(ba, user_request)
        pm_task = create_pm_task(pm, ba_task)
        arch_task = create_arch_task(arquiteto, pm_task)
        ux_task = create_ux_task(ux, arch_task)
        dev_task = create_dev_task(dev, arch_task, ux_task)
        qa_task = create_qa_task(qa, dev_task)
        docs_task = create_docs_task(doc_writer, qa_task)

        equipe_dev.tasks = [ba_task, pm_task, arch_task, ux_task, dev_task, qa_task, docs_task]

        while True:
            try:
                # Função interna com retry para erros 503 (Serviço Indisponível)
                @retry(
                    stop=stop_after_attempt(3), 
                    wait=wait_exponential(multiplier=1, min=4, max=20),
                    before_sleep=lambda retry_state: print(f"⚠️ API Instável (503). Tentando novamente...")
                )
                def kickoff_com_retry():
                    return equipe_dev.kickoff()

                return kickoff_com_retry()

            except Exception as e:
                error_msg = str(e)
                # Lógica de Hot Swap em caso de erro 429 (Cota Esgotada)
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    print("\n" + "!"*50)
                    print("⚠️ LIMITE DE COTA ATINGIDO NO MOTOR POTENTE!")
                    print("🔄 MIGRANDO DEV E QA PARA MOTOR RESERVA (1.500 RPD)...")
                    print("!"*50 + "\n")
                    
                    # Troca apenas quem está no motor potente
                    for agent in equipe_dev.agents:
                        if agent.llm == llm_power_primary:
                            agent.llm = llm_high_quota
                            print(f"✅ Motor do {agent.role} atualizado para reserva.")
                    
                    time.sleep(2)
                    continue 
                else:
                    raise e

    # 5. Interface Interativa / Loop Principal
    print("\n" + "="*50)
    print("🚀 FÁBRICA DE SOFTWARE ATIVA COM FALLBACK INTELIGENTE!")
    print("Programadores: Gemini 3 Flash (Power) --> Fallback Automático")
    print("Digite 'sair' para encerrar a sessão.")
    print("="*50)
    
    while True:
        request = input("\n[VOCÊ]: ")
        
        if request.lower() in ['sair', 'exit', 'quit']:
            print("\n👋 Encerrando fábrica... Até a próxima!")
            break
            
        if not request.strip():
            continue
            
        try:
            resultado = executar_ciclo(request)
            print("\n" + "="*50)
            print("✅ CICLO FINALIZADO!")
            print("="*50)
        except Exception as e:
            print(f"\n❌ ERRO CRÍTICO NA EXECUÇÃO: {e}")

if __name__ == "__main__":
    main()
