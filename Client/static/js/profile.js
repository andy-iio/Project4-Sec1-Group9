
document.addEventListener('DOMContentLoaded', function() {

    initProfilePicture();
    initProfileStats();
});

/**
 * Profile picture change no point in integrating really
 */
function initProfilePicture() {
    const changeProfileBtn = document.getElementById('change-profile-btn');
    if (changeProfileBtn) {
        changeProfileBtn.addEventListener('click', function() {
            alert('Profile picture upload functionality will be added soon!');
        });
    }
}

/** profile stats*/
function initProfileStats() {
    const statCards = document.querySelectorAll('.stat-card');
    if (statCards.length) {
        statCards.forEach(card => {
            card.addEventListener('mouseenter', function() {
                this.classList.add('shadow');
            });
            
            card.addEventListener('mouseleave', function() {
                this.classList.remove('shadow');
            });
        });
    }
}