// Doc Translator - HTMX Utility Helpers

// Toast notification system
function showToast(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toast-container') || createToastContainer();
    const toast = document.createElement('div');
    const colors = {
        success: 'bg-green-500',
        error: 'bg-red-500',
        warning: 'bg-yellow-500',
        info: 'bg-blue-500',
    };
    toast.className = `${colors[type] || colors.info} text-white px-4 py-3 rounded-lg shadow-lg mb-2 transform transition-all duration-300 opacity-0 translate-y-2`;
    toast.textContent = message;
    container.appendChild(toast);

    requestAnimationFrame(() => {
        toast.classList.remove('opacity-0', 'translate-y-2');
    });

    setTimeout(() => {
        toast.classList.add('opacity-0', 'translate-y-2');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'fixed top-4 right-4 z-50 flex flex-col items-end';
    document.body.appendChild(container);
    return container;
}

// Loading spinner overlay
function showLoading(message = 'Loading...') {
    let overlay = document.getElementById('loading-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'loading-overlay';
        overlay.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        overlay.innerHTML = `
            <div class="bg-white dark:bg-gray-800 rounded-lg p-6 flex items-center space-x-4 shadow-xl">
                <svg class="animate-spin h-8 w-8 text-primary-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span class="text-gray-700 dark:text-gray-200 font-medium">${message}</span>
            </div>
        `;
        document.body.appendChild(overlay);
    }
    return overlay;
}

function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) overlay.remove();
}

// Confirmation dialog
function confirmAction(message, onConfirm, onCancel) {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    modal.innerHTML = `
        <div class="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-sm mx-4 shadow-xl">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Confirm</h3>
            <p class="text-gray-600 dark:text-gray-300 mb-6">${message}</p>
            <div class="flex justify-end space-x-3">
                <button id="confirm-cancel" class="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors">Cancel</button>
                <button id="confirm-ok" class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors">Confirm</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);

    modal.querySelector('#confirm-ok').addEventListener('click', () => {
        modal.remove();
        if (onConfirm) onConfirm();
    });
    modal.querySelector('#confirm-cancel').addEventListener('click', () => {
        modal.remove();
        if (onCancel) onCancel();
    });
}

// HTMX event listeners for toast notifications
document.addEventListener('htmx:beforeRequest', function(e) {
    const target = e.detail.target;
    if (target && target.dataset.loading !== 'false') {
        showLoading();
    }
});

document.addEventListener('htmx:afterRequest', function(e) {
    hideLoading();
    const response = e.detail.xhr;
    if (response.status >= 400) {
        showToast('An error occurred', 'error');
    }
});

document.addEventListener('htmx:afterSwap', function(e) {
    hideLoading();
});

// Auto-dismiss flash messages
document.addEventListener('DOMContentLoaded', function() {
    const messages = document.querySelectorAll('[data-auto-dismiss]');
    messages.forEach(msg => {
        const duration = parseInt(msg.dataset.autoDismiss) || 5000;
        setTimeout(() => {
            msg.style.transition = 'opacity 0.3s, transform 0.3s';
            msg.style.opacity = '0';
            msg.style.transform = 'translateY(-10px)';
            setTimeout(() => msg.remove(), 300);
        }, duration);
    });
});

// Progress polling helper for HTMX
function pollJobProgress(jobId, onComplete, onError) {
    const htmx = window.htmx;
    if (htmx) {
        htmx.ajax('GET', `/api/jobs/${jobId}/`, {
            target: '#job-status',
            swap: 'innerHTML',
        });
    }
}
