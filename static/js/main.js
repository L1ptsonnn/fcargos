// Main JavaScript for FCargos

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Animate elements on scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    document.querySelectorAll('.card, .route-item, .stats-card').forEach(el => {
        observer.observe(el);
    });

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Form validation enhancement
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Phone number formatting (Ukrainian format)
    const phoneInputs = document.querySelectorAll('input[name="phone"], input[id*="phone"]');
    phoneInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.startsWith('0')) {
                value = value.substring(1);
            }
            if (value.length > 0 && !value.startsWith('380')) {
                value = '380' + value;
            }
            if (value.length > 0) {
                let formatted = '+380';
                if (value.length > 3) {
                    formatted += ' (' + value.substring(3, 6);
                }
                if (value.length > 6) {
                    formatted += ') ' + value.substring(6, 9);
                }
                if (value.length > 9) {
                    formatted += ' ' + value.substring(9, 11);
                }
                if (value.length > 11) {
                    formatted += ' ' + value.substring(11, 13);
                }
                e.target.value = formatted;
            }
        });
        
        input.addEventListener('focus', function(e) {
            if (!e.target.value) {
                e.target.placeholder = '+380 (__) ___ __ __';
            }
        });
    });

    // Tax ID formatting (Ukrainian format: 12345678)
    const taxInputs = document.querySelectorAll('input[name="tax_id"], input[id*="tax_id"]');
    taxInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 8) {
                value = value.substring(0, 8);
            }
            e.target.value = value;
        });
        
        input.setAttribute('maxlength', '8');
        input.setAttribute('pattern', '[0-9]{8}');
        input.addEventListener('invalid', function(e) {
            if (e.target.validity.patternMismatch) {
                e.target.setCustomValidity('Податковий номер повинен містити 8 цифр');
            }
        });
        input.addEventListener('input', function(e) {
            e.target.setCustomValidity('');
        });
    });

    // License number formatting
    const licenseInputs = document.querySelectorAll('input[name="license_number"], input[id*="license_number"]');
    licenseInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            let value = e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, '');
            if (value.length > 20) {
                value = value.substring(0, 20);
            }
            e.target.value = value;
        });
    });

    // Dynamic route animation
    if (typeof map !== 'undefined' && typeof routesData !== 'undefined') {
        animateRoutes();
    }
});

// Function to animate routes on map
function animateRoutes() {
    // This will be called from the home page template
    console.log('Routes animation initialized');
}

// Function to update map markers dynamically
function updateMapMarkers(routes) {
    if (typeof map === 'undefined') return;
    
    routes.forEach(route => {
        // Update route markers logic here
        console.log('Updating route:', route);
    });
}

