"""Checagens determinísticas da saída dos agentes.

Cada função recebe o texto que um agente produziu e devolve a lista de problemas
encontrados (lista vazia = aprovado). São usadas como guardrail das tasks do CrewAI,
então uma saída reprovada volta para o agente com o motivo, e também nos testes.
"""
import re

_FLAGS = re.MULTILINE | re.IGNORECASE
_FEATURE = re.compile(r"^\s*(Feature|Funcionalidade|Característica)\s*:", _FLAGS)
_SCENARIO = re.compile(r"^\s*(Scenario Outline|Scenario|Esquema do Cenário|Cenário|Cenario)\s*:", _FLAGS)
_STEPS = {
    "Given/Dado": re.compile(r"^\s*(Given|Dado|Dada|Dados|Dadas)\b", _FLAGS),
    "When/Quando": re.compile(r"^\s*(When|Quando)\b", _FLAGS),
    "Then/Então": re.compile(r"^\s*(Then|Então|Entao)\b", _FLAGS),
}
_MERMAID = re.compile(r"```mermaid\s*\n(.*?)```", re.DOTALL)
# Relação no erDiagram do Mermaid, ex.: CLIENTE ||--o{ PEDIDO : faz
_ER_RELATION = re.compile(r"[|}][|o](--|\.\.)[|o][|{]")
_USER_STORY = re.compile(r"\b(Como|As an?)\b.+\b(quero|I want)\b", re.IGNORECASE)
_ACCEPTANCE = re.compile(r"crit[ée]rios? de aceit(e|ação)|acceptance criteria", re.IGNORECASE)


def gherkin_problems(text: str) -> list[str]:
    """Plano de testes do QA: precisa de Feature e de cenários com Dado/Quando/Então."""
    problems = []
    if not _FEATURE.search(text):
        problems.append("sem Feature/Funcionalidade")
    starts = [m.start() for m in _SCENARIO.finditer(text)]
    if not starts:
        return problems + ["nenhum cenário"]
    for i, start in enumerate(starts):
        block = text[start:starts[i + 1] if i + 1 < len(starts) else len(text)]
        name = block.splitlines()[0].strip()
        missing = [step for step, rx in _STEPS.items() if not rx.search(block)]
        if missing:
            problems.append(f"'{name}' sem {', '.join(missing)}")
    return problems


def architecture_problems(text: str) -> list[str]:
    """Documento do Tech Lead: precisa de um erDiagram Mermaid com relações."""
    match = _MERMAID.search(text)
    if not match:
        return ["sem bloco ```mermaid"]
    body = match.group(1)
    if not re.match(r"\s*erDiagram\b", body):
        return ["o diagrama Mermaid não é um erDiagram"]
    if not _ER_RELATION.search(body):
        return ["erDiagram sem nenhuma relação entre entidades"]
    return []


def product_problems(text: str) -> list[str]:
    """Documento do PM: precisa de user stories e de critérios de aceite."""
    problems = []
    if not _USER_STORY.search(text):
        problems.append("sem user story no formato 'Como..., quero...'")
    if not _ACCEPTANCE.search(text):
        problems.append("sem critérios de aceite")
    return problems


def as_guardrail(check):
    """Adapta uma checagem para o parâmetro `guardrail` de uma Task do CrewAI."""
    def guardrail(output):
        problems = check(output.raw)
        if problems:
            return False, "Saída reprovada. Corrija: " + "; ".join(problems)
        return True, output
    return guardrail
