// Show preloader on page navigation
document.addEventListener('click', function(event) {
    const target = event.target;
    // Only show preloader for links, not form submissions
    if (target.tagName === 'A' && target.getAttribute('type') !== 'submit') {
        const preloader = document.getElementById('preloader');
        preloader.style.display = 'flex';
        preloader.style.opacity = '1';
    }
});

// Handle page transitions
window.addEventListener('pageshow', function(event) {
    const preloader = document.getElementById('preloader');
    if (preloader && (event.persisted || performance.navigation.type === 2)) {
        preloader.style.opacity = '0';
        preloader.style.display = 'none';
    }
});

// Show preloader on page refresh
window.addEventListener('beforeunload', function() {
    const preloader = document.getElementById('preloader');
    preloader.style.display = 'flex';
    preloader.style.opacity = '1';
});

// Hide preloader when the page is fully loaded
window.addEventListener('load', function() {
    const preloader = document.getElementById('preloader');
    if (preloader) {
        preloader.style.opacity = '0';
        setTimeout(() => {
            preloader.style.display = 'none';
        }, 500);
    }
});

// Ensure preloader is hidden on initial page load
document.addEventListener('DOMContentLoaded', function() {
    const preloader = document.getElementById('preloader');
    if (preloader) {
        preloader.style.opacity = '0';
        preloader.style.display = 'none';
    }
});