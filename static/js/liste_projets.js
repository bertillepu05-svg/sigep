document.addEventListener('DOMContentLoaded', function() {
    // Gestion du suivi en AJAX (optionnel)
    const followButtons = document.querySelectorAll('.btn-follow');
    
    followButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const form = this.closest('form');
            const url = form.action;
            const csrf = form.querySelector('[name=csrfmiddlewaretoken]').value;
            
            fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrf,
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: new URLSearchParams(form)
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Mettre à jour l'icône
                    const icon = this.querySelector('i');
                    if (data.suivi) {
                        this.classList.add('following');
                        icon.classList.remove('far');
                        icon.classList.add('fas');
                        showToast(data.message, 'success');
                    } else {
                        this.classList.remove('following');
                        icon.classList.remove('fas');
                        icon.classList.add('far');
                        showToast(data.message, 'info');
                    }
                } else {
                    showToast(data.message || 'Erreur', 'error');
                }
            })
            .catch(error => {
                console.error('Erreur:', error);
                showToast('Une erreur est survenue', 'error');
            });
        });
    });
});

function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = 'toast-notification';
    const icon = type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle';
    const color = type === 'success' ? '#28a745' : type === 'error' ? '#dc3545' : '#17a2b8';
    
    toast.innerHTML = `
        <i class="fas ${icon}" style="color: ${color}; margin-right: 10px;"></i>
        <span>${message}</span>
    `;
    
    toast.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: white;
        padding: 12px 20px;
        border-radius: 10px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        border-left: 4px solid ${color};
        z-index: 10000;
        display: flex;
        align-items: center;
        font-weight: 500;
        animation: slideInRight 0.3s ease;
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 3000);
}

// Ajouter les animations si pas déjà présentes
if (!document.querySelector('#toast-animations')) {
    const style = document.createElement('style');
    style.id = 'toast-animations';
    style.textContent = `
        @keyframes slideInRight {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        @keyframes slideOutRight {
            from { transform: translateX(0); opacity: 1; }
            to { transform: translateX(100%); opacity: 0; }
        }
    `;
    document.head.appendChild(style);
}