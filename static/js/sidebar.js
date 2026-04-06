// Attendre que le DOM soit complètement chargé
document.addEventListener('DOMContentLoaded', function() {
    console.log("Sidebar JS chargé !"); // Pour vérifier que le JS s'exécute
    
    // ===== GESTION DU MENU MOBILE =====
    const menuToggle = document.getElementById('menuToggle');
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    const sidebarClose = document.getElementById('sidebarClose');
    const mainContent = document.getElementById('mainContent');
    
    // Vérifier que les éléments existent
    if (menuToggle && sidebar && sidebarOverlay) {
        console.log("Éléments trouvés, initialisation...");
        
        // Ouvrir le menu
        menuToggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            sidebar.classList.add('open');
            sidebarOverlay.classList.add('active');
            mainContent?.classList.add('shifted');
            document.body.style.overflow = 'hidden'; // Empêcher le scroll
        });
        
        // Fermer par l'overlay
        sidebarOverlay.addEventListener('click', function() {
            closeSidebar();
        });
        
        // Fermer par le bouton X
        if (sidebarClose) {
            sidebarClose.addEventListener('click', function() {
                closeSidebar();
            });
        }
        
        function closeSidebar() {
            sidebar.classList.remove('open');
            sidebarOverlay.classList.remove('active');
            mainContent?.classList.remove('shifted');
            document.body.style.overflow = '';
        }
        
        // Fermer avec la touche Echap
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && sidebar.classList.contains('open')) {
                closeSidebar();
            }
        });
    } else {
        console.error("Éléments du menu non trouvés !");
        console.log("menuToggle:", menuToggle);
        console.log("sidebar:", sidebar);
        console.log("sidebarOverlay:", sidebarOverlay);
    }
    
    // ===== GESTION DU MENU DÉROULANT =====
    const dropdownToggles = document.querySelectorAll('.dropdown-toggle-btn');
    
    dropdownToggles.forEach(toggle => {
        toggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const container = this.closest('.dropdown-container');
            
            // Fermer les autres dropdowns
            document.querySelectorAll('.dropdown-container').forEach(other => {
                if (other !== container && other.classList.contains('open')) {
                    other.classList.remove('open');
                }
            });
            
            // Ouvrir/fermer celui-ci
            container.classList.toggle('open');
        });
    });
    
    // Fermer les dropdowns si on clique ailleurs
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.dropdown-container')) {
            document.querySelectorAll('.dropdown-container.open').forEach(container => {
                container.classList.remove('open');
            });
        }
    });
});