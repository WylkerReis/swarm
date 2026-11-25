"""Avaliação da saída dos agentes: exemplos aprovados e reprovados para cada checagem."""
from types import SimpleNamespace

from app.core.output_checks import (
    architecture_problems, as_guardrail, gherkin_problems, product_problems,
)

GHERKIN_OK = """
Funcionalidade: Login
  Cenário: Login com senha válida
    Dado que estou na tela de login
    Quando informo usuário e senha válidos
    Então vejo o painel inicial

  Scenario: Locked user
    Given a locked user
    When they log in
    Then an error is shown
"""


def test_gherkin_aprovado_em_portugues_e_ingles():
    assert gherkin_problems(GHERKIN_OK) == []


def test_gherkin_reprova_cenario_sem_entao():
    text = "Feature: Login\n  Scenario: Sem verificação\n    Given x\n    When y\n"
    assert gherkin_problems(text) == ["'Scenario: Sem verificação' sem Then/Então"]


def test_gherkin_reprova_texto_livre():
    # O caso mais comum de LLM: descreve os testes em prosa em vez de escrever Gherkin.
    problems = gherkin_problems("Vamos testar o login com usuário válido e inválido.")
    assert problems == ["sem Feature/Funcionalidade", "nenhum cenário"]


ARCH_OK = """
Stack: FastAPI + PostgreSQL

```mermaid
erDiagram
    CLIENTE ||--o{ PEDIDO : faz
    PEDIDO }|..|{ PRODUTO : contem
```
"""


def test_arquitetura_aprovada():
    assert architecture_problems(ARCH_OK) == []


def test_arquitetura_reprova_sem_mermaid():
    assert architecture_problems("Tabelas: cliente, pedido") == ["sem bloco ```mermaid"]


def test_arquitetura_reprova_diagrama_errado():
    text = "```mermaid\nflowchart TD\n  A --> B\n```"
    assert architecture_problems(text) == ["o diagrama Mermaid não é um erDiagram"]


def test_arquitetura_reprova_entidades_soltas():
    text = "```mermaid\nerDiagram\n  CLIENTE {\n    int id\n  }\n```"
    assert architecture_problems(text) == ["erDiagram sem nenhuma relação entre entidades"]


def test_produto_aprovado():
    text = "Como cliente, quero recuperar a senha para voltar a acessar.\n\nCritérios de aceite:\n- ..."
    assert product_problems(text) == []


def test_produto_reprova_sem_criterios():
    assert product_problems("As a user I want to log in") == ["sem critérios de aceite"]


def test_guardrail_devolve_motivo_para_o_agente():
    guardrail = as_guardrail(architecture_problems)
    ok, feedback = guardrail(SimpleNamespace(raw="sem diagrama"))
    assert not ok
    assert "sem bloco ```mermaid" in feedback

    output = SimpleNamespace(raw=ARCH_OK)
    assert guardrail(output) == (True, output)


def test_tasks_usam_as_checagens_como_guardrail():
    from crewai import Task
    from app.core.tasks import create_arch_task, create_pm_task, create_qa_task

    anterior = Task(description="etapa anterior", expected_output="texto")
    tasks = {
        "pm": create_pm_task(None, anterior),
        "arquitetura": create_arch_task(None, anterior),
        "qa": create_qa_task(None, anterior),
    }
    for nome, task in tasks.items():
        assert task.guardrail is not None, f"task de {nome} sem guardrail"
