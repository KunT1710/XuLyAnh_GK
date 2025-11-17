document.addEventListener('DOMContentLoaded', () => {
    const sidebar = document.querySelector('.editor-sidebar');
    const toggleBtn = document.querySelector('.sidebar-toggle-btn');
    if (sidebar && toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('is-closed');
        });
    }
});