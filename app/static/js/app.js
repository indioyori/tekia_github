/**
 * TEKIA - JavaScript principal
 * Funciones globales y utilidades
 */

// Funciones de utilidad
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('es-ES', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatDateShort(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('es-ES', {
        day: 'numeric',
        month: 'short',
        year: 'numeric'
    });
}

// Notificaciones
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
        <span>${message}</span>
    `;
    
    // Estilos básicos
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        display: flex;
        align-items: center;
        gap: 0.5rem;
        z-index: 10000;
        animation: slideIn 0.3s ease-out;
    `;
    
    // Animación
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        .notification-success { border-left: 4px solid #28a745; }
        .notification-error { border-left: 4px solid #dc3545; }
        .notification-info { border-left: 4px solid #17a2b8; }
    `;
    document.head.appendChild(style);
    
    document.body.appendChild(notification);
    
    // Eliminar después de 5 segundos
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

// Confirmación genérica
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Copiar al portapapeles
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showNotification('Copiado al portapapeles', 'success');
        return true;
    } catch (error) {
        console.error('Error copiando:', error);
        showNotification('Error al copiar', 'error');
        return false;
    }
}

// Descargar archivo
function downloadFile(content, filename, mimeType = 'text/plain') {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Renderizado simple de Markdown (para vista previa)
function simpleMarkdown(text) {
    if (!text) return '';
    
    // Encabezados
    text = text.replace(/^#\s+(.*$)/gm, '<h1>$1</h1>');
    text = text.replace(/^##\s+(.*$)/gm, '<h2>$1</h2>');
    text = text.replace(/^###\s+(.*$)/gm, '<h3>$1</h3>');
    text = text.replace(/^####\s+(.*$)/gm, '<h4>$1</h4>');
    
    // Negrita y cursiva
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
    text = text.replace(/__(.*?)__/g, '<strong>$1</strong>');
    text = text.replace(/_(.*?)_/g, '<em>$1</em>');
    
    // Tachado
    text = text.replace(/~~(.*?)~~/g, '<s>$1</s>');
    
    // Enlaces
    text = text.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
    
    // Imágenes
    text = text.replace(/!\[(.*?)\]\((.*?)\)/g, '<img src="$2" alt="$1" style="max-width: 100%; border-radius: 4px; margin: 0.5rem 0;">');
    
    // Citas
    text = text.replace(/^>\s+(.*$)/gm, '<blockquote>$1</blockquote>');
    
    // Listas
    text = text.replace(/^\-\s+(.*$)/gm, '<li>$1</li>');
    text = text.replace(/^\*\s+(.*$)/gm, '<li>$1</li>');
    text = text.replace(/^\d+\.\s+(.*$)/gm, '<li>$1</li>');
    
    // Código
    text = text.replace(/`(.*?)`/g, '<code>$1</code>');
    
    // Bloques de código
    text = text.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
    
    // Tablas
    text = text.replace(/\|\s*([^|\n]+)\s*\|\s*([^|\n]+)\s*\|/g, '<table><tr><th>$1</th><th>$2</th></tr>');
    
    // Saltos de línea
    text = text.replace(/\n\n/g, '</p><p>');
    text = text.replace(/\n/g, '<br>');
    
    return `<p>${text}</p>`;
}

// Formatear números
function formatNumber(num) {
    return new Intl.NumberFormat('es-ES').format(num);
}

// Formatear porcentajes
function formatPercent(num, decimals = 2) {
    return (num * 100).toFixed(decimals) + '%';
}

// Generar ID único
function generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

// Debounce function (para búsquedas)
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Throttle function
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Validación de formularios
function validateForm(formId, rules) {
    const form = document.getElementById(formId);
    let isValid = true;
    
    for (const [fieldName, rule] of Object.entries(rules)) {
        const field = form.querySelector(`[name="${fieldName}"]`);
        if (!field) continue;
        
        const value = field.value.trim();
        const errorElement = field.nextElementSibling;
        
        if (rule.required && !value) {
            if (errorElement && errorElement.classList.contains('error-message')) {
                errorElement.textContent = 'Este campo es obligatorio';
            }
            isValid = false;
        } else if (rule.minLength && value.length < rule.minLength) {
            if (errorElement && errorElement.classList.contains('error-message')) {
                errorElement.textContent = `Mínimo ${rule.minLength} caracteres`;
            }
            isValid = false;
        } else if (rule.maxLength && value.length > rule.maxLength) {
            if (errorElement && errorElement.classList.contains('error-message')) {
                errorElement.textContent = `Máximo ${rule.maxLength} caracteres`;
            }
            isValid = false;
        } else if (rule.pattern && !new RegExp(rule.pattern).test(value)) {
            if (errorElement && errorElement.classList.contains('error-message')) {
                errorElement.textContent = rule.message || 'Formato inválido';
            }
            isValid = false;
        } else {
            if (errorElement && errorElement.classList.contains('error-message')) {
                errorElement.textContent = '';
            }
        }
    }
    
    return isValid;
}

// Inicialización general
document.addEventListener('DOMContentLoaded', function() {
    // Añadir clases a enlaces externos
    document.querySelectorAll('a[href^="http"]').forEach(link => {
        if (!link.href.includes(window.location.hostname)) {
            link.setAttribute('target', '_blank');
            link.setAttribute('rel', 'noopener nofollow');
        }
    });
    
    // Manejar errores globales
    window.addEventListener('unhandledrejection', event => {
        console.error('Unhandled rejection:', event.reason);
        showNotification('Error inesperado. Consulta la consola.', 'error');
    });
    
    window.addEventListener('error', event => {
        console.error('Error:', event.error);
        showNotification('Error inesperado. Consulta la consola.', 'error');
    });
});

// Exportar funciones para uso en otros módulos
window.TEKIA = {
    escapeHtml,
    formatDate,
    formatDateShort,
    showNotification,
    confirmAction,
    copyToClipboard,
    downloadFile,
    simpleMarkdown,
    formatNumber,
    formatPercent,
    generateId,
    debounce,
    throttle,
    validateForm
};
