// Global variables
let statusUpdateInterval;
let kpiUpdateInterval;

// Tab switching functionality
function showTab(tabName) {
    // Hide all tabs
    const tabs = document.querySelectorAll('.tab-content');
    tabs.forEach(tab => tab.classList.remove('active'));

    // Remove active class from all buttons
    const buttons = document.querySelectorAll('.tab-button');
    buttons.forEach(button => button.classList.remove('active'));

    // Show selected tab
    document.getElementById(tabName).classList.add('active');

    // Add active class to clicked button
    event.target.classList.add('active');

    // If KPIs tab is selected, refresh KPIs
    if (tabName === 'kpis') {
        refreshKPIs();
    }
}

// Alert functions
function showAlert(message, type = 'success') {
    const alertContainer = document.getElementById('alert-container');
    const alertClass = type === 'success' ? 'alert-success' : 'alert-error';

    alertContainer.innerHTML = `
        <div class="alert ${alertClass}">
            ${message}
        </div>
    `;

    // Auto-hide after 5 seconds
    setTimeout(() => {
        alertContainer.innerHTML = '';
    }, 5000);
}

// Agent control functions
async function startAgent() {
    const formData = {
        username: document.getElementById('username').value,
        password: document.getElementById('password').value,
        target_account: document.getElementById('target_account').value,
        api_key: document.getElementById('api_key').value,
        verification_code: document.getElementById('verification_code').value || null
    };

    // Validate required fields
    if (!formData.username || !formData.password || !formData.target_account || !formData.api_key) {
        showAlert('Por favor, completa todos los campos requeridos.', 'error');
        return;
    }

    try {
        const response = await fetch('/api/start-agent', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        const result = await response.json();

        if (response.ok) {
            showAlert('¡Agente iniciado exitosamente!', 'success');
            updateStatus();
            startStatusUpdates();
        } else {
            showAlert(`Error: ${result.detail}`, 'error');
        }
    } catch (error) {
        showAlert(`Error de conexión: ${error.message}`, 'error');
    }
}

async function stopAgent() {
    try {
        const response = await fetch('/api/stop-agent', {
            method: 'POST'
        });

        const result = await response.json();

        if (response.ok) {
            showAlert('Señal de detención enviada al agente.', 'success');
            updateStatus();
        } else {
            showAlert(`Error: ${result.detail}`, 'error');
        }
    } catch (error) {
        showAlert(`Error de conexión: ${error.message}`, 'error');
    }
}

// Status update functions
async function updateStatus() {
    try {
        const response = await fetch('/api/status');
        const status = await response.json();

        const statusElement = document.getElementById('agent-status');
        const statusTextElement = document.getElementById('status-text');

        if (status.running) {
            statusElement.textContent = 'Ejecutándose';
            statusElement.style.color = '#27ae60';
            statusTextElement.textContent = 'El agente está activo y procesando mensajes...';
        } else {
            statusElement.textContent = 'Detenido';
            statusElement.style.color = '#e74c3c';
            statusTextElement.textContent = 'El agente está detenido. Configúralo y presiona "Iniciar Agente".';
        }
    } catch (error) {
        console.error('Error updating status:', error);
    }
}

function startStatusUpdates() {
    // Update status every 5 seconds
    statusUpdateInterval = setInterval(updateStatus, 5000);
}

function stopStatusUpdates() {
    if (statusUpdateInterval) {
        clearInterval(statusUpdateInterval);
    }
}

// KPI functions
async function refreshKPIs() {
    try {
        const response = await fetch('/api/kpis');
        const kpis = await response.json();

        // Update KPI cards
        document.getElementById('total-messages').textContent = kpis.total_messages_sent;
        document.getElementById('total-replies').textContent = kpis.total_replies;
        document.getElementById('response-rate').textContent = `${kpis.response_rate}%`;
        document.getElementById('total-qualified').textContent = kpis.total_qualified;
        document.getElementById('qualification-rate').textContent = `${kpis.qualification_rate}%`;

        // Add visual feedback
        const cards = document.querySelectorAll('.kpi-card');
        cards.forEach(card => {
            card.style.transform = 'scale(1.05)';
            setTimeout(() => {
                card.style.transform = 'scale(1)';
            }, 200);
        });

    } catch (error) {
        console.error('Error refreshing KPIs:', error);
        showAlert('Error al cargar los KPIs. Verifica que el servidor esté ejecutándose.', 'error');
    }
}

function startKPIUpdates() {
    // Update KPIs every 30 seconds when on KPIs tab
    kpiUpdateInterval = setInterval(() => {
        if (document.getElementById('kpis').classList.contains('active')) {
            refreshKPIs();
        }
    }, 30000);
}

// Initialize the app
document.addEventListener('DOMContentLoaded', function() {
    // Initial status check
    updateStatus();

    // Start KPI updates
    startKPIUpdates();

    // Add loading animation to buttons when clicked
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            const originalText = this.innerHTML;
            this.innerHTML = '<span class="loading"></span> Procesando...';
            this.disabled = true;

            // Re-enable after 3 seconds
            setTimeout(() => {
                this.innerHTML = originalText;
                this.disabled = false;
            }, 3000);
        });
    });
});
