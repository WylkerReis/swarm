# Camomis AI Factory

Pipeline multiagente com [CrewAI](https://www.crewai.com/) e Gemini que leva um pedido em texto livre até código, testes e documentação. Sete agentes trabalham em sequência: Business Analyst, Product Manager, Tech Lead, UX Designer, Developer, QA Engineer e Technical Writer.

O foco do projeto, do ponto de vista de QA, é **avaliar a saída de um LLM de forma objetiva**: cada etapa crítica tem uma checagem automática, e uma resposta fora do formato volta para o agente com o motivo da reprovação.

## Como a saída dos agentes é avaliada

LLMs erram de forma previsível: descrevem os testes em prosa em vez de escrever Gherkin, desenham um fluxograma quando o pedido era o modelo de dados, esquecem os critérios de aceite. As checagens em [`app/core/output_checks.py`](app/core/output_checks.py) pegam esses casos sem depender de outro LLM:

| Agente | O que é verificado |
|---|---|
| Product Manager | Tem user stories no formato "Como..., quero..." e uma seção de critérios de aceite |
| Tech Lead | Tem um bloco Mermaid do tipo `erDiagram` com pelo menos uma relação entre entidades |
| QA Engineer | Tem `Feature`/`Funcionalidade` e todo cenário tem Dado, Quando e Então (português ou inglês) |

As checagens são ligadas às tasks como `guardrail` do CrewAI. Quando a saída é reprovada, o agente recebe a lista de problemas e tenta de novo.

## Bugs encontrados na revisão

Antes de escrever as checagens, revisei o código e escrevi um teste de regressão para cada bug encontrado ([`tests/test_bugs.py`](tests/test_bugs.py)):

1. **A aplicação não subia:** `tasks.py` importava `from tools import ...` em vez de `app.core.tools`.
2. **`write_file_tool` quebrava** ao criar um arquivo sem pasta (`os.makedirs("")`).
3. **`ask_human_tool` mostrava a pergunta duas vezes** no terminal.
4. **Segurança:** o endpoint `GET /files/<caminho>` lia qualquer arquivo do disco, com o servidor aberto em `0.0.0.0` e CORS liberado. Agora só lê arquivos dentro da pasta do projeto.

Limitação conhecida: no modo Dashboard, `git_commit_tool` e `ask_human_tool` respondem automaticamente, sem esperar uma pessoa. As duas ferramentas avisam isso no próprio texto.

## Testes

```bash
pip install -r requirements.txt pytest
pytest
```

Os testes não chamam a API do Gemini e rodam no GitHub Actions a cada push.

## Como rodar

Crie um arquivo `.env` com `GEMINI_API_KEY=...` e instale as dependências com `pip install -r requirements.txt`.

```bash
python main.py --ui      # Dashboard web (FastAPI) em http://localhost:8000
python main.py           # Modo terminal
python main.py --check   # Lista os modelos Gemini disponíveis para a sua chave
```

## Estrutura

- `app/core/agents.py`, `tasks.py`: definição dos 7 agentes e das tarefas de cada um
- `app/core/crew_manager.py`: monta a equipe e a ordem das tarefas
- `app/core/tools.py`: ferramentas dos agentes (ler e escrever arquivos, commit, perguntar ao usuário)
- `app/core/output_checks.py`: checagens da saída dos agentes
- `app/api/server.py`: API FastAPI com logs em tempo real (SSE) e controle de cota do Gemini
- `public/`: dashboard web
- `tests/`: testes das checagens e de regressão dos bugs
