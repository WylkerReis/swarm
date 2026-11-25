"""Testes de regressão dos bugs encontrados na revisão do projeto."""
import importlib

from fastapi.testclient import TestClient

from app.core.tools import ask_human_tool, write_file_tool


def test_tasks_importa_sem_erro():
    # Bug 1: tasks.py fazia `from tools import ...`, e a aplicação não subia.
    importlib.import_module("app.core.crew_manager")


def test_write_file_na_pasta_atual(tmp_path, monkeypatch):
    # Bug 2: os.makedirs("") quebrava quando o agente escrevia um arquivo sem pasta.
    monkeypatch.chdir(tmp_path)
    write_file_tool.func(file_path="main.py", content="print('oi')")
    assert (tmp_path / "main.py").read_text(encoding="utf-8") == "print('oi')"


def test_ask_human_mostra_a_pergunta_uma_vez(capsys):
    # Bug 3: a pergunta aparecia duplicada no terminal.
    ask_human_tool.func(question="Qual banco de dados?")
    assert capsys.readouterr().out.count("Qual banco de dados?") == 1


def test_files_nao_le_fora_do_projeto(tmp_path, monkeypatch):
    # Bug 4 (segurança): GET /files/<caminho> lia qualquer arquivo do disco.
    secret = tmp_path / "secret.txt"
    secret.write_text("senha", encoding="utf-8")
    project = tmp_path / "projeto"
    project.mkdir()
    (project / "README.md").write_text("ok", encoding="utf-8")
    monkeypatch.chdir(project)

    from app.api.server import app
    client = TestClient(app)

    assert client.get("/files/README.md").json() == {"content": "ok"}
    response = client.get(f"/files/{secret.as_posix()}")
    assert response.status_code == 404
    assert "senha" not in response.text
