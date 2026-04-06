// static/js/modif_profil.js

// Attendre que le DOM soit chargé
document.addEventListener('DOMContentLoaded', function() {
    console.log('modif_profil.js : Initialisé');
    
    // Initialiser les tooltips Bootstrap si disponibles
    if (typeof bootstrap !== 'undefined') {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // Validation des champs du formulaire
    const form = document.getElementById('editProfileForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            if (!validateForm()) {
                e.preventDefault();
                showToast('Veuillez corriger les erreurs dans le formulaire', 'error');
            } else {
                // Le formulaire sera soumis normalement
                showToast('Modifications enregistrées avec succès !', 'success');
            }
        });
    }
    
    // Validation en temps réel des champs
    const inputs = document.querySelectorAll('input[required]');
    inputs.forEach(input => {
        input.addEventListener('blur', function() {
            validateField(this);
        });
    });
});

// ============================================
// FONCTIONS DE PRÉVISUALISATION D'IMAGE
// ============================================

/**
 * Prévisualiser l'image avant upload
 */
function previewImage(event) {
    const file = event.target.files[0];
    const output = document.getElementById('profilePhoto');
    
    if (file) {
        // Vérifier la taille du fichier (max 2 Mo)
        if (file.size > 2 * 1024 * 1024) {
            showToast('La taille de l\'image ne doit pas dépasser 2 Mo', 'error');
            event.target.value = '';
            return;
        }
        
        // Vérifier le type de fichier
        const allowedTypes = ['image/jpeg', 'image/png', 'image/jpg'];
        if (!allowedTypes.includes(file.type)) {
            showToast('Format accepté : JPG, PNG uniquement', 'error');
            event.target.value = '';
            return;
        }
        
        const reader = new FileReader();
        reader.onload = function(e) {
            if (output) {
                output.src = e.target.result;
                // Ajouter un effet d'apparition
                output.style.animation = 'fadeIn 0.5s ease';
                setTimeout(() => {
                    output.style.animation = '';
                }, 500);
            }
        }
        reader.readAsDataURL(file);
    }
}

// ============================================
// FONCTIONS DE VALIDATION
// ============================================

/**
 * Valider un champ individuel
 */
function validateField(field) {
    const value = field.value.trim();
    const isValid = value !== '';
    
    if (field.required && !isValid) {
        field.classList.add('is-invalid');
        return false;
    } else {
        field.classList.remove('is-invalid');
        
        // Validation spécifique pour l'email
        if (field.type === 'email' && value) {
            const emailRegex = /^[^\s@]+@([^\s@]+\.)+[^\s@]+$/;
            if (!emailRegex.test(value)) {
                field.classList.add('is-invalid');
                return false;
            }
        }
        
        // Validation pour le téléphone
        if (field.name === 'telephone' && value) {
            const phoneRegex = /^[\+]?[0-9]{8,15}$/;
            if (!phoneRegex.test(value.replace(/\s/g, ''))) {
                field.classList.add('is-invalid');
                return false;
            }
        }
        
        return true;
    }
}

/**
 * Valider tout le formulaire
 */
function validateForm() {
    let isValid = true;
    const requiredFields = document.querySelectorAll('#editProfileForm input[required]');
    
    requiredFields.forEach(field => {
        if (!validateField(field)) {
            isValid = false;
        }
    });
    
    // Validation des mots de passe
    const oldPassword = document.querySelector('input[name="old_password"]');
    const newPassword1 = document.querySelector('input[name="new_password1"]');
    const newPassword2 = document.querySelector('input[name="new_password2"]');
    
    if (newPassword1 && newPassword1.value) {
        // Vérifier la longueur
        if (newPassword1.value.length < 8) {
            showToast('Le nouveau mot de passe doit contenir au moins 8 caractères', 'error');
            isValid = false;
        }
        
        // Vérifier la correspondance
        if (newPassword2 && newPassword1.value !== newPassword2.value) {
            showToast('Les mots de passe ne correspondent pas', 'error');
            isValid = false;
        }
        
        // Vérifier que l'ancien mot de passe est rempli
        if (!oldPassword || !oldPassword.value) {
            showToast('Veuillez entrer votre mot de passe actuel', 'error');
            isValid = false;
        }
    }
    
    return isValid;
}

// ============================================
// FONCTIONS DE TOAST (NOTIFICATIONS)
// ============================================

/**
 * Afficher un toast de notification
 */
function showToast(message, type = 'success') {
    // Supprimer les toasts existants
    const existingToasts = document.querySelectorAll('.custom-toast');
    existingToasts.forEach(toast => toast.remove());
    
    const toast = document.createElement('div');
    toast.className = 'custom-toast';
    
    const icon = type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle';
    const color = type === 'success' ? '#28a745' : '#dc3545';
    
    toast.innerHTML = `
        <i class="fas ${icon}" style="color: ${color}; margin-right: 10px;"></i>
        <span>${message}</span>
    `;
    
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: white;
        padding: 15px 25px;
        border-radius: 10px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.2);
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
            if (toast && toast.parentNode) {
                toast.remove();
            }
        }, 300);
    }, 3000);
}

/**
 * Afficher un toast de sauvegarde (pour formulaire AJAX)
 */
function showSaveToast() {
    showToast('Modifications enregistrées avec succès !', 'success');
}

// ============================================
// FONCTIONS DE MODAL (SUPPRESSION DE COMPTE)
// ============================================

/**
 * Confirmer la suppression du compte
 */
function confirmDelete() {
    if (typeof bootstrap !== 'undefined') {
        const modalElement = document.getElementById('deleteModal');
        if (modalElement) {
            const modal = new bootstrap.Modal(modalElement);
            modal.show();
        } else {
            // Fallback si l'élément n'existe pas
            const userConfirmed = confirm('⚠️ Supprimer votre compte ?\n\nCette action est irréversible. Toutes vos données seront perdues.');
            if (userConfirmed) {
                window.location.href = '/supprimer-compte/';
            }
        }
    } else {
        // Fallback si Bootstrap n'est pas chargé
        const userConfirmed = confirm('⚠️ Supprimer votre compte ?\n\nCette action est irréversible. Toutes vos données seront perdues.');
        if (userConfirmed) {
            window.location.href = '/supprimer-compte/';
        }
    }
}

/**
 * Fermer la modal de suppression (si utilisée)
 */
function closeDeleteModal() {
    const modal = document.getElementById('deleteModal');
    if (modal && typeof bootstrap !== 'undefined') {
        const modalInstance = bootstrap.Modal.getInstance(modal);
        if (modalInstance) {
            modalInstance.hide();
        }
    }
}

// ============================================
// FONCTIONS D'ANIMATION
// ============================================

/**
 * Ajouter les styles d'animation
 */
function addAnimationStyles() {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideInRight {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        @keyframes slideOutRight {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }
        
        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: scale(0.95);
            }
            to {
                opacity: 1;
                transform: scale(1);
            }
        }
        
        .is-invalid {
            border-color: #dc3545 !important;
            background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 12 12' width='12' height='12' fill='none' stroke='%23dc3545'%3e%3ccircle cx='6' cy='6' r='4.5'/%3e%3cpath stroke-linecap='round' d='M5.8 3.6h.4L6 6.5z'/%3e%3ccircle cx='6' cy='8.2' r='.6' fill='%23dc3545' stroke='none'/%3e%3c/svg%3e");
            background-repeat: no-repeat;
            background-position: right calc(0.375em + 0.1875rem) center;
            background-size: calc(0.75em + 0.375rem) calc(0.75em + 0.375rem);
        }
        
        .is-valid {
            border-color: #28a745 !important;
            background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 8 8'%3e%3cpath fill='%2328a745' d='M2.3 6.73L.6 4.53c-.4-1.04.46-1.4 1.1-.8l1.1 1.4 3.4-3.8c.6-.63 1.6-.27 1.2.7l-4 4.6c-.43.5-.8.4-1.1.1z'/%3e%3c/svg%3e");
            background-repeat: no-repeat;
            background-position: right calc(0.375em + 0.1875rem) center;
            background-size: calc(0.75em + 0.375rem) calc(0.75em + 0.375rem);
        }
        
        .form-control.is-valid, .form-select.is-valid {
            border-color: #28a745;
        }
    `;
    document.head.appendChild(style);
}

// Ajouter les styles d'animation au chargement
document.addEventListener('DOMContentLoaded', function() {
    addAnimationStyles();
});

// ============================================
// GESTION DES CHAMPS DYNAMIQUES (ENTREPRISE)
// ============================================

/**
 * Activer/Désactiver les champs d'entreprise pour le représentant
 */
function toggleEntrepriseFields(active) {
    const entrepriseFields = document.querySelectorAll('[name^="entreprise_"]');
    entrepriseFields.forEach(field => {
        field.disabled = !active;
        if (active) {
            field.classList.remove('bg-light');
        } else {
            field.classList.add('bg-light');
        }
    });
}

// ============================================
// EXPORTATION DES FONCTIONS (si nécessaire)
// ============================================

// Exposer les fonctions globalement pour les templates
window.previewImage = previewImage;
window.showSaveToast = showSaveToast;
window.confirmDelete = confirmDelete;
window.closeDeleteModal = closeDeleteModal;
window.validateField = validateField;