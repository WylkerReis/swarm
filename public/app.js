document.addEventListener('DOMContentLoaded', () => {
    const logContainer = document.getElementById('log-container');
    const commandInput = document.getElementById('command-input');
    const sendBtn = document.getElementById('send-btn');
    const codeDisplay = document.getElementById('code-display');
    const mockupsContent = document.getElementById('mockups-content');

    const agentCards = {
        'ba': document.getElementById('agent-ba'),
        'pm': document.getElementById('agent-pm'),
        'arquiteto': document.getElementById('agent-arquiteto'),
        'ux': document.getElementById('agent-ux'),
        'dev': document.getElementById('agent-dev'),
        'qa': document.getElementById('agent-qa'),
        'doc': document.getElementById('agent-doc')
    };

    const connectSSE = () => {
        const eventSource = new EventSource('/stream');

        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.message) {
                addLogEntry(data.message);
                updateAgentStates(data.message);
            }
            
            if (data.quota) {
                updateQuotaDisplay(data.quota);
            }
        };

        eventSource.onerror = () => {
            console.error("SSE Connection failed. Reconnecting...");
            eventSource.close();
            setTimeout(connectSSE, 2000);
        };
    };

    const addLogEntry = (message) => {
        const entry = document.createElement('div');
        entry.className = 'log-entry';
        
        if (message.includes('⚠️') || message.includes('ALERTA')) entry.classList.add('warning');
        else if (message.includes('❌') || message.includes('Erro')) entry.classList.add('error');
        else if (message.includes('✅') || message.includes('Sucesso')) entry.classList.add('system');
        else if (message.includes('[') && message.includes(']')) entry.classList.add('agent');
        else entry.classList.add('system');

        entry.textContent = message;
        logContainer.appendChild(entry);
        logContainer.scrollTop = logContainer.scrollHeight;
    };

    const updateAgentStates = (message) => {
        const msg = message.toLowerCase();
        
        // Desativa todos se finalizar
        if (msg.includes('ciclo finalizado') || msg.includes('sucesso')) {
            Object.values(agentCards).forEach(card => {
                card.classList.remove('active');
                if (card.querySelector('.status')) card.querySelector('.status').textContent = 'Ocioso';
            });
            return;
        }

        // Mapeamento de palavras-chave para agentes
        const mapping = {
            'ba': ['analista', 'ba_task', 'requirements'],
            'pm': ['product manager', 'pm_task'],
            'arquiteto': ['arquiteto', 'tech lead', 'arch_task'],
            'ux': ['ux designer', 'mockup', 'ux_task'],
            'dev': ['senior developer', 'dev_task', 'escrevendo'],
            'qa': ['qa engineer', 'qa_task', 'testes'],
            'doc': ['technical writer', 'docs_task', 'documentação']
        };

        for (const [id, keys] of Object.entries(mapping)) {
            if (keys.some(k => msg.includes(k))) {
                // Remove active de outros e coloca nesse
                Object.values(agentCards).forEach(card => card.classList.remove('active'));
                agentCards[id].classList.add('active');
                if (agentCards[id].querySelector('.status')) agentCards[id].querySelector('.status').textContent = 'Trabalhando...';
                break;
            }
        }
    };

    const updateQuotaDisplay = (quota) => {
        const rpmVal = document.getElementById('rpm-val');
        const rpmFill = document.getElementById('rpm-fill');
        const rpdVal = document.getElementById('rpd-val');
        const rpdFill = document.getElementById('rpd-fill');
        const quotaMsg = document.getElementById('quota-msg');

        if (!rpmVal || !rpmFill || !rpdVal || !rpdFill) return;

        // Atualiza RPM
        const rpmPct = (quota.rpm / 15) * 100;
        rpmVal.textContent = `${quota.rpm} / 15`;
        rpmFill.style.width = `${Math.min(rpmPct, 100)}%`;
        
        // Atualiza RPD
        const rpdPct = (quota.rpd / 1500) * 100;
        rpdVal.textContent = `${quota.rpd} / 1500`;
        rpdFill.style.width = `${Math.min(rpdPct, 100)}%`;

        // Cores de Alerta
        if (rpmPct > 80 || rpdPct > 90) {
            rpmFill.style.backgroundColor = 'var(--error-color)';
            quotaMsg.textContent = "ALERTA: LIMITE PRÓXIMO!";
            quotaMsg.style.color = 'var(--error-color)';
        } else if (rpmPct > 50) {
            rpmFill.style.backgroundColor = 'var(--warning-color)';
            quotaMsg.textContent = "SISTEMA SOB CARGA";
            quotaMsg.style.color = 'var(--warning-color)';
        } else {
            rpmFill.style.backgroundColor = 'var(--primary-color)';
            quotaMsg.textContent = "SISTEMA OPERANDO NORMAL";
            quotaMsg.style.color = 'var(--success-color)';
        }
    };

    // --- Actions ---
    sendBtn.addEventListener('click', async () => {
        const prompt = commandInput.value.trim();
        if (!prompt) return;

        sendBtn.disabled = true;
        sendBtn.textContent = "PROCESSANDO...";
        
        try {
            const response = await fetch('/run', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt })
            });

            if (response.ok) {
                addLogEntry(`🚀 Missão iniciada: "${prompt}"`);
                commandInput.value = "";
            }
        } catch (err) {
            addLogEntry(`❌ Erro ao enviar comando: ${err.message}`);
        } finally {
            sendBtn.disabled = false;
            sendBtn.textContent = "INICIAR MISSÃO";
        }
    });

    // --- Tab Switching ---
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const tab = btn.getAttribute('data-tab');
            document.getElementById('mockups-content').classList.toggle('hidden', tab !== 'mockups');
            document.getElementById('code-content').classList.toggle('hidden', tab !== 'code');
        });
    });

    // --- Polling para Mockups e Arquivos ---
    // (Simulando a atualização vindo do server)
    setInterval(async () => {
        // Aqui poderíamos ter um endpoint /list-files para atualizar a UI
    }, 5000);

    // Inicializa SSE
    connectSSE();
});
