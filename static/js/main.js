/* ==========================================================================
   Sistema de Gestão de Alunos - JavaScript Principal
   ========================================================================== */

// Variáveis globais
let alunoIdAtual, moduleIdAtual;
let isLoading = false;

// Inicialização quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// Inicializar aplicação
function initializeApp() {
    // Configurar tooltips do Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Configurar animações
    animateElements();
    
    // Configurar formulários
    setupFormValidation();
    
    // Carregar dados iniciais
    if (document.getElementById('tab-view-modules')) {
        carregarModulos();
    }
}

// Animações de entrada
function animateElements() {
    const elements = document.querySelectorAll('.card, .alert, .list-group-item');
    elements.forEach((el, index) => {
        setTimeout(() => {
            el.classList.add('fade-in');
        }, index * 100);
    });
}

// Configurar validação de formulários
function setupFormValidation() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            event.preventDefault();
            event.stopPropagation();
            form.classList.add('was-validated');
        });
    });
}

// Função para exibir abas com animação
function showTab(tabId) {
    const tabs = document.querySelectorAll('.tab-pane');
    const navLinks = document.querySelectorAll('.nav-link');
    
    // Remover classes ativas
    tabs.forEach(tab => {
        tab.classList.remove('active', 'show');
    });
    navLinks.forEach(link => {
        link.classList.remove('active');
    });
    
    // Ativar aba selecionada
    const selectedTab = document.getElementById(tabId);
    const selectedNavLink = document.querySelector(`[onclick="showTab('${tabId}')"]`);
    
    if (selectedTab) {
        selectedTab.classList.add('active', 'show', 'fade-in');
    }
    if (selectedNavLink) {
        selectedNavLink.classList.add('active');
    }
    
    // Carregar dados específicos da aba
    switch(tabId) {
        case 'tab-view-modules':
            carregarModulos();
            break;
    }
}

// Utilitários de UI
function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <div class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Carregando...</span>
                </div>
                <p class="mt-2 text-muted">Carregando dados...</p>
            </div>
        `;
    }
}

function showMessage(elementId, message, type = 'success') {
    const element = document.getElementById(elementId);
    if (element) {
        const alertClass = `alert-${type}`;
        element.innerHTML = `
            <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
                <i class="bi bi-${getIconForType(type)} me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        element.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

function getIconForType(type) {
    const icons = {
        'success': 'check-circle',
        'danger': 'exclamation-triangle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

function clearMessage(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = '';
    }
}

// Funções de API
async function makeRequest(url, options = {}) {
    if (isLoading) return;
    isLoading = true;
    
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        const data = await response.json();
        return { data, status: response.status };
    } catch (error) {
        console.error('Erro na requisição:', error);
        return { error: 'Erro de conexão. Tente novamente.' };
    } finally {
        isLoading = false;
    }
}

// Funções de alunos
async function adicionarAluno() {
    const alunoData = {
        nome: document.getElementById('nomeNovo').value.trim(),
        numero_matricula: document.getElementById('numeroMatriculaNovo').value.trim(),
        data_matricula: document.getElementById('dataMatriculaNovo').value,
        atestados: parseInt(document.getElementById('atestadosNovo').value) || 0,
        encaminhamento: document.getElementById('encaminhamentoNovo').value.trim(),
        obs: document.getElementById('obsNovo').value.trim()
    };

    // Validação básica
    if (!alunoData.nome || !alunoData.numero_matricula || !alunoData.data_matricula) {
        showMessage('mensagem', 'Por favor, preencha todos os campos obrigatórios.', 'warning');
        return;
    }

    clearMessage('mensagem');
    const submitBtn = document.querySelector('[onclick="adicionarAluno()"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Adicionando...';
    submitBtn.disabled = true;

    const result = await makeRequest('/adicionar_aluno', {
        method: 'POST',
        body: JSON.stringify(alunoData)
    });

    if (result.error) {
        showMessage('mensagem', result.error, 'danger');
    } else if (result.data.error) {
        showMessage('mensagem', result.data.error, 'danger');
    } else {
        showMessage('mensagem', result.data.message, 'success');
        // Limpar formulário
        document.getElementById('nomeNovo').value = '';
        document.getElementById('numeroMatriculaNovo').value = '';
        document.getElementById('dataMatriculaNovo').value = '';
        document.getElementById('atestadosNovo').value = '';
        document.getElementById('encaminhamentoNovo').value = '';
        document.getElementById('obsNovo').value = '';
    }

    submitBtn.innerHTML = originalText;
    submitBtn.disabled = false;
}

async function editarAluno() {
    const numeroMatricula = document.getElementById('numeroMatriculaEditar').value.trim();
    
    if (!numeroMatricula) {
        showMessage('mensagemEditar', 'Por favor, informe o número da matrícula.', 'warning');
        return;
    }

    const alunoData = {
        nome: document.getElementById('nomeEditar').value.trim(),
        data_matricula: document.getElementById('dataMatriculaEditar').value,
        atestados: parseInt(document.getElementById('atestadosEditar').value) || 0,
        encaminhamento: document.getElementById('encaminhamentoEditar').value.trim(),
        obs: document.getElementById('obsEditar').value.trim()
    };

    const result = await makeRequest(`/editar_aluno/${numeroMatricula}`, {
        method: 'PUT',
        body: JSON.stringify(alunoData)
    });

    if (result.error) {
        showMessage('mensagemEditar', result.error, 'danger');
    } else if (result.data.error) {
        showMessage('mensagemEditar', result.data.error, 'danger');
    } else {
        showMessage('mensagemEditar', result.data.message, 'success');
    }
}

async function excluirAluno() {
    const numeroMatricula = document.getElementById('numeroMatriculaExcluir').value.trim();
    
    if (!numeroMatricula) {
        showMessage('mensagemExcluir', 'Por favor, informe o número da matrícula.', 'warning');
        return;
    }

    // Confirmação
    if (!confirm('Tem certeza que deseja excluir este aluno? Esta ação não pode ser desfeita.')) {
        return;
    }

    const result = await makeRequest(`/excluir_aluno/${numeroMatricula}`, {
        method: 'DELETE'
    });

    if (result.error) {
        showMessage('mensagemExcluir', result.error, 'danger');
    } else if (result.data.error) {
        showMessage('mensagemExcluir', result.data.error, 'danger');
    } else {
        showMessage('mensagemExcluir', result.data.message, 'success');
        document.getElementById('numeroMatriculaExcluir').value = '';
    }
}

async function pesquisarAluno() {
    const numeroMatricula = document.getElementById('numeroMatriculaPesquisa').value.trim();
    const nome = document.getElementById('nomePesquisa').value.trim();

    if (!numeroMatricula && !nome) {
        showMessage('resultadoPesquisa', 'Por favor, informe o número da matrícula ou o nome para pesquisar.', 'warning');
        return;
    }

    showLoading('resultadoPesquisa');
    
    const url = `/pesquisar_aluno?numero_matricula=${encodeURIComponent(numeroMatricula)}&nome=${encodeURIComponent(nome)}`;
    const result = await makeRequest(url);

    const resultadoDiv = document.getElementById('resultadoPesquisa');
    const listaAlunos = document.getElementById('listaAlunos');
    
    if (listaAlunos) {
        listaAlunos.innerHTML = '';
    }

    if (result.error) {
        showMessage('resultadoPesquisa', result.error, 'danger');
    } else if (result.data.error) {
        showMessage('resultadoPesquisa', result.data.error, 'info');
    } else if (Array.isArray(result.data)) {
        if (result.data.length === 1) {
            const aluno = result.data[0];
            resultadoDiv.innerHTML = `
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="bi bi-person-fill me-2"></i>Dados do Aluno</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6">
                                <p><strong>Nome:</strong> ${aluno.nome}</p>
                                <p><strong>Matrícula:</strong> ${aluno.numero_matricula}</p>
                                <p><strong>Data Matrícula:</strong> ${formatDate(aluno.data_matricula)}</p>
                            </div>
                            <div class="col-md-6">
                                <p><strong>Atestados:</strong> <span class="badge bg-info">${aluno.atestados}</span></p>
                                <p><strong>Encaminhamento:</strong> ${aluno.encaminhamento || 'Não informado'}</p>
                                <p><strong>Observações:</strong> ${aluno.obs || 'Nenhuma observação'}</p>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        } else if (result.data.length > 1) {
            let html = '<div class="list-group">';
            result.data.forEach(aluno => {
                html += `
                    <div class="list-group-item list-group-item-action">
                        <div class="d-flex w-100 justify-content-between">
                            <h6 class="mb-1">${aluno.nome}</h6>
                            <small class="text-muted">Matrícula: ${aluno.numero_matricula}</small>
                        </div>
                        <a href="/detalhes_aluno/${aluno.id}" class="btn btn-outline-primary btn-sm mt-2" target="_blank">
                            <i class="bi bi-eye me-1"></i>Ver Detalhes
                        </a>
                    </div>
                `;
            });
            html += '</div>';
            resultadoDiv.innerHTML = html;
        }
    }
}

// Funções de módulos
async function criarModulo() {
    const nome = document.getElementById('nomeModulo').value.trim();
    
    if (!nome) {
        showMessage('mensagemModulo', 'Por favor, informe o nome do módulo.', 'warning');
        return;
    }

    const result = await makeRequest('/criar_modulo', {
        method: 'POST',
        body: JSON.stringify({ nome })
    });

    if (result.error) {
        showMessage('mensagemModulo', result.error, 'danger');
    } else if (result.data.error) {
        showMessage('mensagemModulo', result.data.error, 'danger');
    } else {
        showMessage('mensagemModulo', result.data.message, 'success');
        document.getElementById('nomeModulo').value = '';
        carregarModulos();
    }
}

async function excluirModulo() {
    const nome = document.getElementById('moduleNameExcluir').value.trim();
    
    if (!nome) {
        showMessage('mensagemExcluirModulo', 'Por favor, informe o nome do módulo.', 'warning');
        return;
    }

    if (!confirm('Tem certeza que deseja excluir este módulo? Esta ação não pode ser desfeita.')) {
        return;
    }

    const result = await makeRequest('/excluir_modulo', {
        method: 'POST',
        body: JSON.stringify({ nome })
    });

    if (result.error) {
        showMessage('mensagemExcluirModulo', result.error, 'danger');
    } else if (result.data.error) {
        showMessage('mensagemExcluirModulo', result.data.error, 'danger');
    } else {
        showMessage('mensagemExcluirModulo', result.data.message, 'success');
        document.getElementById('moduleNameExcluir').value = '';
        carregarModulos();
    }
}

async function carregarModulos() {
    const moduleList = document.getElementById('moduleList');
    if (!moduleList) return;

    showLoading('moduleList');

    const result = await makeRequest('/listar_modulos');

    if (result.error) {
        moduleList.innerHTML = `
            <div class="alert alert-danger">
                <i class="bi bi-exclamation-triangle me-2"></i>
                ${result.error}
            </div>
        `;
        return;
    }

    if (result.data.length === 0) {
        moduleList.innerHTML = `
            <div class="alert alert-info">
                <i class="bi bi-info-circle me-2"></i>
                Nenhum módulo cadastrado ainda.
            </div>
        `;
        return;
    }

    let html = '<div class="row">';
    result.data.forEach((modulo, index) => {
        html += `
            <div class="col-md-6 col-lg-4 mb-3">
                <div class="card h-100">
                    <div class="card-body">
                        <h6 class="card-title">
                            <i class="bi bi-folder me-2"></i>
                            ${modulo.nome}
                        </h6>
                        <p class="card-text text-muted">ID: ${modulo.id}</p>
                        <button onclick="verAlunosDoModulo(${modulo.id})" class="btn btn-primary btn-sm">
                            <i class="bi bi-people me-1"></i>Ver Alunos
                        </button>
                    </div>
                </div>
            </div>
        `;
    });
    html += '</div>';
    
    moduleList.innerHTML = html;
    
    // Animar cards
    setTimeout(() => {
        const cards = moduleList.querySelectorAll('.card');
        cards.forEach((card, index) => {
            setTimeout(() => {
                card.classList.add('fade-in');
            }, index * 100);
        });
    }, 100);
}

async function verAlunosDoModulo(moduleId) {
    const studentListContainer = document.getElementById('studentListContainer');
    const studentList = document.getElementById('studentList');
    
    if (!studentList) return;

    showLoading('studentList');
    
    const result = await makeRequest(`/ver_alunos_modulo/${moduleId}`);

    if (result.error) {
        studentList.innerHTML = `
            <div class="alert alert-danger">
                <i class="bi bi-exclamation-triangle me-2"></i>
                ${result.error}
            </div>
        `;
        return;
    }

    if (result.data.error) {
        studentList.innerHTML = `
            <div class="alert alert-info">
                <i class="bi bi-info-circle me-2"></i>
                ${result.data.error}
            </div>
        `;
    } else {
        let html = '<div class="table-responsive"><table class="table table-hover"><thead><tr>';
        html += '<th>Nome</th><th>Matrícula</th><th>Faltas</th><th>Nota Final</th><th>Ações</th></tr></thead><tbody>';
        
        result.data.forEach(aluno => {
            const statusClass = aluno.nota_final >= 7 ? 'success' : aluno.nota_final >= 5 ? 'warning' : 'danger';
            html += `
                <tr>
                    <td><strong>${aluno.nome}</strong></td>
                    <td>${aluno.numero_matricula}</td>
                    <td><span class="badge bg-secondary">${aluno.faltas}</span></td>
                    <td><span class="badge bg-${statusClass}">${aluno.nota_final}</span></td>
                    <td>
                        <button onclick="carregarDetalhesAluno(${aluno.id}, ${moduleId})" class="btn btn-outline-primary btn-sm">
                            <i class="bi bi-eye me-1"></i>Detalhes
                        </button>
                    </td>
                </tr>
            `;
        });
        html += '</tbody></table></div>';
        studentList.innerHTML = html;
    }

    if (studentListContainer) {
        studentListContainer.style.display = 'block';
        studentListContainer.scrollIntoView({ behavior: 'smooth' });
    }
}

// Funções de detalhes do aluno
async function carregarDetalhesAluno(alunoId, moduleId) {
    alunoIdAtual = alunoId;
    moduleIdAtual = moduleId;

    const result = await makeRequest(`/obter_dados_modulo_aluno/${alunoId}/${moduleId}`);

    if (result.error) {
        alert('Erro ao carregar dados: ' + result.error);
        return;
    }

    if (result.data.error) {
        alert(result.data.error);
        return;
    }

    const data = result.data;
    
    // Atualizar informações na interface
    const detalhes = {
        'detalhesNome': data.nome,
        'detalhesMatricula': data.numero_matricula,
        'detalhesFaltas': data.faltas,
        'detalhesNotaTutor': data.nota_tutor,
        'detalhesNotaAvaliacaoRegular': data.nota_avaliacao_regular,
        'detalhesNotaRecuperacao': data.nota_recuperacao,
        'detalhesNotaFinal': data.nota_final
    };

    Object.entries(detalhes).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    });

    // Mostrar container de detalhes
    const container = document.getElementById('studentDetailsContainer');
    if (container) {
        container.style.display = 'block';
        container.scrollIntoView({ behavior: 'smooth' });
        showStudentTab('view-info');
    }
}

function showStudentTab(tabId) {
    const tabs = document.querySelectorAll('.student-tab-content');
    tabs.forEach(tab => tab.style.display = 'none');
    
    const selectedTab = document.getElementById(tabId);
    if (selectedTab) {
        selectedTab.style.display = 'block';
    }
}

async function salvarEdicao() {
    const dados = {};

    // Obter valores dos campos
    const campos = [
        'editFaltas',
        'editNotaTutor',
        'editNotaAvaliacaoRegular',
        'editNotaRecuperacao',
        'editNotaFinal'
    ];

    campos.forEach(campo => {
        const element = document.getElementById(campo);
        if (element && element.value.trim() !== '') {
            const key = campo.replace('edit', '').replace(/([A-Z])/g, '_$1').toLowerCase();
            dados[key] = parseFloat(element.value) || 0;
        }
    });

    if (Object.keys(dados).length === 0) {
        alert('Por favor, preencha pelo menos um campo para atualizar.');
        return;
    }

    const result = await makeRequest(`/editar_informacoes_modulo/${alunoIdAtual}/${moduleIdAtual}`, {
        method: 'PUT',
        body: JSON.stringify(dados)
    });

    if (result.error) {
        alert('Erro ao salvar: ' + result.error);
    } else if (result.data.error) {
        alert(result.data.error);
    } else {
        alert(result.data.message);
        // Recarregar detalhes
        await carregarDetalhesAluno(alunoIdAtual, moduleIdAtual);
        showStudentTab('view-info');
        // Limpar campos de edição
        campos.forEach(campo => {
            const element = document.getElementById(campo);
            if (element) element.value = '';
        });
    }
}

// Utilitários
function formatDate(dateString) {
    if (!dateString) return 'Não informado';
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR');
}

// Adicionar eventos de teclado para melhor UX
document.addEventListener('keydown', function(e) {
    // ESC para fechar modais/detalhes
    if (e.key === 'Escape') {
        const container = document.getElementById('studentDetailsContainer');
        if (container && container.style.display === 'block') {
            container.style.display = 'none';
        }
    }
});
