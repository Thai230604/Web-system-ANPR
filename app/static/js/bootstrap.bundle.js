// Bootstrap JS - Minimal version for responsive navbar toggle
// Replace this with your actual Bootstrap JS file
// Download from: https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js

document.addEventListener('DOMContentLoaded', function () {
    // Navbar toggle functionality
    const navbarTogglers = document.querySelectorAll('.navbar-toggler');
    navbarTogglers.forEach(toggler => {
        toggler.addEventListener('click', function () {
            const target = this.getAttribute('data-bs-target');
            const collapseElement = document.querySelector(target);
            if (collapseElement) {
                collapseElement.classList.toggle('show');
            }
        });
    });

    // Close alert on close button click
    const closeButtons = document.querySelectorAll('.btn-close');
    closeButtons.forEach(btn => {
        btn.addEventListener('click', function () {
            this.closest('.alert').remove();
        });
    });

    // Add active class to current nav link
    const currentLocation = location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentLocation) {
            link.classList.add('active');
        }
    });
});
