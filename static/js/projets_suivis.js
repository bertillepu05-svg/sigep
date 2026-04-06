    document.addEventListener('DOMContentLoaded', function() {
        // Gestion de l'arrêt de suivi en AJAX (optionnel)
        const unfollowForms = document.querySelectorAll('.unfollow-form');
        
        unfollowForms.forEach(form => {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                
                const url = this.action;
                const csrf = this.querySelector('[name=csrfmiddlewaretoken]').value;
                const card = this.closest('.project-card');
                const projetId = card.id.replace('projet-', '');
                
                fetch(url, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrf,
                        'Content-Type': 'application/x-www-form-urlencoded'
                    },
                    body: new URLSearchParams(this)
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        // Supprimer la carte avec animation
                        card.style.animation = 'fadeOut 0.3s ease';
                        setTimeout(() => {
                            card.remove();
                            showToast(data.message, 'success');
                            // Recharger la page si plus de projets
                            if (document.querySelectorAll('.project-card').length === 0) {
                                location.reload();
                            }
                        }, 300);
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
        const icon = type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle';
        const color = type === 'success' ? '#28a745' : '#dc3545';
        
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

    // Ajouter les animations
    if (!document.querySelector('#follow-animations')) {
        const style = document.createElement('style');
        style.id = 'follow-animations';
        style.textContent = `
            @keyframes slideInRight {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            @keyframes slideOutRight {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(100%); opacity: 0; }
            }
            @keyframes fadeOut {
                from { opacity: 1; transform: translateY(0); }
                to { opacity: 0; transform: translateY(10px); }
            }
        `;
        document.head.appendChild(style);
    }
