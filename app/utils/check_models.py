import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

if not api_key:
    print("ERRO: Chave de API não encontrada no .env")
else:
    genai.configure(api_key=api_key)
    try:
        print("--- Modelos Disponíveis para sua API Key ---")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"Nome: {m.name}")
    except Exception as e:
        print(f"Erro ao listar modelos: {e}")
