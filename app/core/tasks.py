from crewai import Task
from tools import write_file_tool, read_file_tool, git_commit_tool, ask_human_tool

def create_ba_task(agent, user_request):
    return Task(
        description=f"Leia a solicitação: '{user_request}'. 1) Caso o software não seja novo, use sua ferramenta de leitura de arquivos para analisar o documento de requisitos original escrito pelo Technical Writer. 2) Se o novo pedido conflitar diametralmente com os requisitos antigos mapeados, chame a ferramenta de interação humana, apresente o conflito explicitamente e pergunte ao usuário qual saída o projeto deve tomar. 3) Só avance quando construir um briefing blindado.",
        expected_output="Um briefing novo contendo um compilado impecável dos requisitos originais do Technical Writer amalgamados à nova decisão tomada presencialmente na discussão pelo usuário humano.",
        agent=agent,
        tools=[ask_human_tool] # Lembrando que read_file_tool foi associado globalmente pelo main.py
    )

def create_pm_task(agent, ba_task):
    return Task(
        description="Analise o briefing estruturado pelo Business Analyst. Descreva as features essenciais em user stories e liste os critérios de aceite.",
        expected_output="Documento Markdown detalhando as user stories, requisitos funcionais e técnicos.",
        agent=agent,
        context=[ba_task]
    )

def create_arch_task(agent, pm_task):
    return Task(
        description="Baseado na documentação do PM, escolha a stack, defina modelos de dados e estrutura de pastas. Projete e crie explicitamente um Mapa Visual Diagramado (utilizando sintaxe como Mermaid.js ou UML textual) contendo todos os relacionamentos e entidades do Banco de Dados que será utilizado no software.",
        expected_output="Documento arquitetural com stack definida, estrutura de árvore das pastas e um Mapa Visual explícito ilustrando a estruturação do Banco de Dados para compor a documentação final.",
        agent=agent,
        context=[pm_task]
    )

def create_ux_task(agent, arch_task):
    return Task(
        description="Analise os requisitos e a arquitetura. 1) Desenhe o escopo conceitual da interface. 2) Use OBRIGATORIAMENTE a ferramenta 'generate_ui_mockup_tool' para gerar um protótipo visual (mockup) de alta fidelidade seguindo a estética Camomis (Dark Mode, Glassmorphism). 3) Solicite aprovação do humano para esse visual antes de prosseguir.",
        expected_output="Um protótipo visual gerado e uma especificação textual de componentes. O projeto só avança com a aprovação explícita do visual pelo usuário.",
        agent=agent,
        human_input=True,
        context=[arch_task]
    )

def create_dev_task(agent, arch_task, ux_task):
    return Task(
        description="""Implemente o código baseando-se na arquitetura e no Design System.\n\nRegra rígida: Verifique ativamente se os novos requisitos das suas implementações NÃO conflitam com os requisitos mapeados pela frente de produto. Usando sua ferramenta de escrita, molde o código-fonte de produção nos arquivos locais.""",
        expected_output="Uma confirmação listando os arquivos e o código criado, afirmando sem sombra de dúvidas que a implementação feita não feriu regras ou gerou conflitos de negócio.",
        agent=agent,
        tools=[write_file_tool],
        context=[arch_task, ux_task]
    )

def create_qa_task(agent, dev_task):
    return Task(
        description="""Incorpore o Shift-Left testing: comece a planejar validações nos pilares do projeto.\n\n1) Audite a base local, garantindo com precisão absoluta que os incrementos do dev não conflitaram com os requisitos já mapeados pelo Technical Writer.\n2) Produza e escreva uma documentação forte contendo um Plano de Testes estruturado em BDD utilizando sintaxe Gherkin.\n3) Construa testes automatizados completos (incluindo validações firmes de API REST/GraphQL se existirem).\n4) Ao fim, aprove com sua ferramenta Git Commit. Em caso de quebra, aborte com interação humana.""",
        expected_output="Garantia irrefutável de ausência de conflitos de negócio. Um plano BDD em Gherkin e uma suíte de testes (com testes de API) pronta e commitada. Qualquer erro reporta para o supervisor humano.",
        agent=agent,
        tools=[read_file_tool, write_file_tool, git_commit_tool], # Ganhando write_file_tool para criar arquivos de teste
        human_input=True, # Magicamente pausa a Crew para revisão humana do QA!
        context=[dev_task]
    )

def create_docs_task(agent, qa_task):
    return Task(
        description="""Centralize o conhecimento. Produza uma documentação rica contendo ABSOLUTAMENTE TODOS os requisitos do sistema descobertos/mapeados até esse momento. \n\nVocê também é responsável por consolidar e atualizar todo e qualquer README ou documento técnico do projeto logo após os testes passarem e o software sofrer deploy/commit.""",
        expected_output="O arquivo oficial formatado do projeto cobrindo requisitos mapeados, endpoints (se existirem), arquitetura e um guia sempre atualizado para desenvolvedores executarem os testes Gherkin/BDD.",
        agent=agent,
        tools=[write_file_tool],
        context=[qa_task]
    )
