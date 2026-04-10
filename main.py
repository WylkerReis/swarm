import os
import argparse
import sys
from dotenv import load_dotenv

# Garantir que a pasta 'app' seja tratada como pacote se rodar de fora
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.crew_manager import get_crew_config, create_crew_tasks
from app.api.server import start_server

def run_cli():
    """Executa a Fábrica de Software via Terminal (CLI)."""
    load_dotenv()
    
    print("\n" + "="*50)
    print("🚀 CAMOMIS AI FACTORY - MODO TERMINAL")
    print("="*50)
    
    config = get_crew_config()
    crew_obj = config["crew"]
    agents = config["agents"]
    
    while True:
        request = input("\n[VOCÊ] Descreva a feature ou sistema: ")
        
        if request.lower() in ['sair', 'exit', 'quit']:
            print("\n👋 Encerrando fábrica... Até a próxima!")
            break
            
        if not request.strip():
            continue
            
        try:
            crew_obj.tasks = create_crew_tasks(agents, request)
            resultado = crew_obj.kickoff()
            print("\n" + "="*50)
            print("✅ CICLO FINALIZADO!")
            print("="*50)
        except Exception as e:
            print(f"\n❌ ERRO CRÍTICO NA EXECUÇÃO: {e}")

def run_check_models():
    """Executa o utilitário de checagem de modelos Gemini."""
    import google.generativeai as genai
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    
    if not api_key:
        print("❌ ERRO: Chave de API não encontrada no .env")
        return

    genai.configure(api_key=api_key)
    try:
        print("\n--- Modelos Disponíveis para sua API Key ---")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"✅ {m.name}")
    except Exception as e:
        print(f"❌ Erro ao listar modelos: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Camomis AI Factory - Unified Interface")
    parser.add_argument("--ui", action="store_true", help="Inicia o Dashboard Web")
    parser.add_argument("--check", action="store_true", help="Verifica modelos disponíveis no Gemini")
    
    args = parser.parse_args()

    if args.ui:
        print("🚀 Iniciando Dashboard Web...")
        start_server()
    elif args.check:
        run_check_models()
    else:
        run_cli()
