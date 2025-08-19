/* ==========================================================================
   Period Grade System - JavaScript Principal
   ========================================================================== */

// Variáveis globais do sistema
let currentUser = null;
let isLoading = false;

// Inicialização quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// Inicializar aplicação
function initializeApp() {
    // Configurar sidebar responsivo
    initializeSidebar();
    
    // Configurar tooltips do Bootstrap
    initializeTooltips();
    
    // Configurar auto-dismiss para alerts
    initializeAlerts();
    
    // Aplicar animações
    animateElements();
}

// Inicializar tooltips
function initializeTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Inicializar sidebar responsivo
function initializeSidebar() {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('show');
        });
        
        // Fechar sidebar ao clicar fora (mobile)
        document.addEventListener('click', function(event) {
            if (window.innerWidth <= 768) {
                if (!sidebar.contains(event.target) && !sidebarToggle.contains(event.target)) {
                    sidebar.classList.remove('show');
                }
            }
        });
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
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
}

// Inicializar recursos específicos da página
function initializePageSpecificFeatures() {
    const currentPage = window.location.pathname;
    
    switch(currentPage) {
        case '/':
            // Dashboard - já tem seu próprio script
            break;
        case '/alunos':
            // Página de alunos - já tem seu próprio script
            break;
        case '/modulos':
            // Página de módulos - já tem seu próprio script
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
        const icon = getIconForType(type);
        element.innerHTML = `
            <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
                <i class="bi bi-${icon} me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        element.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            const alert = element.querySelector('.alert');
            if (alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    }
}

function getIconForType(type) {
    const icons = {
        'success': 'check-circle-fill',
        'danger': 'exclamation-triangle-fill',
        'warning': 'exclamation-triangle-fill',
        'info': 'info-circle-fill'
    };
    return icons[type] || 'info-circle-fill';
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

// Funções para modais
function openAddStudentModal() {
    const modal = new bootstrap.Modal(document.getElementById('addStudentModal'));
    modal.show();
}

function openAddModuleModal() {
    const modal = new bootstrap.Modal(document.getElementById('addModuleModal'));
    modal.show();
}

// Funções de alunos (reutilizadas dos modais)
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
        showMessage('mensagemModal', 'Por favor, preencha todos os campos obrigatórios.', 'warning');
        return;
    }

    clearMessage('mensagemModal');
    const submitBtn = document.querySelector('[onclick="adicionarAluno()"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Adicionando...';
    submitBtn.disabled = true;

    const result = await makeRequest('/adicionar_aluno', {
        method: 'POST',
        body: JSON.stringify(alunoData)
    });

    if (result.error) {
        showMessage('mensagemModal', result.error, 'danger');
    } else if (result.data.error) {
        showMessage('mensagemModal', result.data.error, 'danger');
    } else {
        showMessage('mensagemModal', result.data.message, 'success');
        // Limpar formulário
        document.getElementById('nomeNovo').value = '';
        document.getElementById('numeroMatriculaNovo').value = '';
        document.getElementById('dataMatriculaNovo').value = '';
        document.getElementById('atestadosNovo').value = '0';
        document.getElementById('encaminhamentoNovo').value = '';
        document.getElementById('obsNovo').value = '';
        
        // Fechar modal após sucesso
        setTimeout(() => {
            const modal = bootstrap.Modal.getInstance(document.getElementById('addStudentModal'));
            if (modal) modal.hide();
            
            // Recarregar página se estivermos na página de alunos
            if (window.location.pathname === '/alunos') {
                location.reload();
            }
        }, 2000);
    }

    submitBtn.innerHTML = originalText;
    submitBtn.disabled = false;
}

// Função para criar módulo (modal)
async function criarModulo() {
    const nome = document.getElementById('nomeModulo').value.trim();
    
    if (!nome) {
        showMessage('mensagemModuloModal', 'Por favor, informe o nome do módulo.', 'warning');
        return;
    }

    const submitBtn = document.querySelector('[onclick="criarModulo()"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Criando...';
    submitBtn.disabled = true;

    const result = await makeRequest('/criar_modulo', {
        method: 'POST',
        body: JSON.stringify({ nome })
    });

    if (result.error) {
        showMessage('mensagemModuloModal', result.error, 'danger');
    } else if (result.data.error) {
        showMessage('mensagemModuloModal', result.data.error, 'danger');
    } else {
        showMessage('mensagemModuloModal', result.data.message, 'success');
        document.getElementById('nomeModulo').value = '';
        
        // Fechar modal após sucesso
        setTimeout(() => {
            const modal = bootstrap.Modal.getInstance(document.getElementById('addModuleModal'));
            if (modal) modal.hide();
            
            // Recarregar página se estivermos na página de módulos
            if (window.location.pathname === '/modulos') {
                if (typeof carregarModulosPage === 'function') {
                    carregarModulosPage();
                }
            }
        }, 2000);
    }

    submitBtn.innerHTML = originalText;
    submitBtn.disabled = false;
}

// Funções específicas da página de dashboard
function initializeDashboard() {
    // Funcionalidades específicas do dashboard serão adicionadas aqui
    updateDashboardStats();
}

function updateDashboardStats() {
    // Atualizar estatísticas em tempo real se necessário
    // Por enquanto, usamos os dados estáticos do backend
}

// Funções específicas da página de alunos
function initializeAlunosPage() {
    // Funcionalidades específicas da página de alunos
}

// Funções específicas da página de módulos
function initializeModulosPage() {
    // Funcionalidades específicas da página de módulos
}

// Funções auxiliares para formatação
function formatDate(dateString) {
    if (!dateString) return 'Não informado';
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR');
}

function formatDateTime(dateTimeString) {
    if (!dateTimeString) return 'Não informado';
    const date = new Date(dateTimeString);
    return date.toLocaleString('pt-BR');
}

function formatNumber(number, decimals = 1) {
    return Number(number).toFixed(decimals);
}

// Funções de navegação
function navigateTo(url) {
    window.location.href = url;
}

function goBack() {
    window.history.back();
}

// Funções de exportação e impressão
function exportData(data, filename, type = 'json') {
    let content, mimeType;
    
    switch(type) {
        case 'json':
            content = JSON.stringify(data, null, 2);
            mimeType = 'application/json';
            filename += '.json';
            break;
        case 'csv':
            content = convertToCSV(data);
            mimeType = 'text/csv';
            filename += '.csv';
            break;
        default:
            return;
    }
    
    const blob = new Blob([content], { type: mimeType });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

function convertToCSV(data) {
    if (!Array.isArray(data) || data.length === 0) return '';
    
    const headers = Object.keys(data[0]);
    const csvContent = [
        headers.join(','),
        ...data.map(row => headers.map(header => `"${row[header] || ''}"`).join(','))
    ].join('\n');
    
    return csvContent;
}

// Funções de validação
function validateEmail(email) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
}

function validatePhone(phone) {
    const regex = /^\(\d{2}\)\s\d{4,5}-\d{4}$/;
    return regex.test(phone);
}

function validateCPF(cpf) {
    cpf = cpf.replace(/[^\d]+/g,'');
    if(cpf == '') return false;
    if (cpf.length != 11 || 
        cpf == "00000000000" || 
        cpf == "11111111111" || 
        cpf == "22222222222" || 
        cpf == "33333333333" || 
        cpf == "44444444444" || 
        cpf == "55555555555" || 
        cpf == "66666666666" || 
        cpf == "77777777777" || 
        cpf == "88888888888" || 
        cpf == "99999999999")
        return false;
    
    let add = 0;
    for (let i=0; i < 9; i++)
        add += parseInt(cpf.charAt(i)) * (10 - i);
    let rev = 11 - (add % 11);
    if (rev == 10 || rev == 11)
        rev = 0;
    if (rev != parseInt(cpf.charAt(9)))
        return false;
    
    add = 0;
    for (let i = 0; i < 10; i++)
        add += parseInt(cpf.charAt(i)) * (11 - i);
    rev = 11 - (add % 11);
    if (rev == 10 || rev == 11)
        rev = 0;
    if (rev != parseInt(cpf.charAt(10)))
        return false;
    return true;
}

// Funções de máscara para inputs
function applyMasks() {
    // Aplicar máscaras de telefone, CPF, etc. se necessário
    const phoneInputs = document.querySelectorAll('input[data-mask="phone"]');
    phoneInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length <= 11) {
                value = value.replace(/(\d{2})(\d)/, '($1) $2');
                value = value.replace(/(\d{4,5})(\d{4})$/, '$1-$2');
            }
            e.target.value = value;
        });
    });
}

// Tratamento de erros globais
window.addEventListener('error', function(event) {
    console.error('Erro global capturado:', event.error);
    // Aqui você pode implementar um sistema de logs ou notificação de erros
});

// Adicionar eventos de teclado para melhor UX
document.addEventListener('keydown', function(e) {
    // ESC para fechar modais
    if (e.key === 'Escape') {
        const modals = document.querySelectorAll('.modal.show');
        modals.forEach(modal => {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) bsModal.hide();
        });
    }
    
    // Ctrl+S para salvar (prevenir comportamento padrão)
    if (e.ctrlKey && e.key === 's') {
        e.preventDefault();
        // Aqui você pode implementar lógica de auto-save se necessário
    }
});

// Funções de acessibilidade
function initializeAccessibility() {
    // Melhorar navegação por teclado
    const focusableElements = document.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    focusableElements.forEach(element => {
        element.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && element.tagName === 'BUTTON') {
                element.click();
            }
        });
    });
}

// Performance monitoring (simples)
function measurePerformance() {
    if ('performance' in window) {
        window.addEventListener('load', function() {
            const loadTime = performance.now();
            console.log(`Página carregada em ${loadTime.toFixed(2)}ms`);
        });
    }
}

// Inicializar recursos adicionais quando apropriado
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        applyMasks();
        initializeAccessibility();
        measurePerformance();
    });
} else {
    applyMasks();
    initializeAccessibility();
    measurePerformance();
}