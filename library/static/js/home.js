// Text Banner Slider
let currentTextSlide = 0;
let totalTextSlides = document.querySelectorAll('[id^="text-dot-"]').length;
let autoTextSlideInterval;

function showTextSlide(index) {
    const slidesContainer = document.getElementById('text-slides-container');
    const offset = -index * 100;
    slidesContainer.style.transform = `translateX(${offset}%)`;
    
    // Update active dot
    document.querySelectorAll('[id^="text-dot-"]').forEach(dot => {
        dot.classList.remove('bg-white');
        dot.classList.add('bg-white/50');
    });
    document.getElementById(`text-dot-${index}`)?.classList.remove('bg-white/50');
    document.getElementById(`text-dot-${index}`)?.classList.add('bg-white');
}

function nextTextSlide() {
    currentTextSlide = (currentTextSlide + 1) % totalTextSlides;
    showTextSlide(currentTextSlide);
    resetAutoTextSlide();
}

function prevTextSlide() {
    currentTextSlide = (currentTextSlide - 1 + totalTextSlides) % totalTextSlides;
    showTextSlide(currentTextSlide);
    resetAutoTextSlide();
}

function goToTextSlide(index) {
    currentTextSlide = index;
    showTextSlide(currentTextSlide);
    resetAutoTextSlide();
}

function startAutoTextSlide() {
    autoTextSlideInterval = setInterval(nextTextSlide, 3000);
}

function resetAutoTextSlide() {
    clearInterval(autoTextSlideInterval);
    startAutoTextSlide();
}

// Image Banner Slider
let currentSlide = 0;
let totalSlides = document.querySelectorAll('[id^="dot-"]').length;
let autoSlideInterval;

function showSlide(index) {
    const slidesContainer = document.getElementById('slides-container');
    const offset = -index * 100;
    slidesContainer.style.transform = `translateX(${offset}%)`;
    
    // Update active dot
    document.querySelectorAll('[id^="dot-"]').forEach(dot => {
        dot.classList.remove('bg-white');
        dot.classList.add('bg-white/50');
    });
    document.getElementById(`dot-${index}`).classList.remove('bg-white/50');
    document.getElementById(`dot-${index}`).classList.add('bg-white');
}

function nextSlide() {
    currentSlide = (currentSlide + 1) % totalSlides;
    showSlide(currentSlide);
    resetAutoSlide();
}

function prevSlide() {
    currentSlide = (currentSlide - 1 + totalSlides) % totalSlides;
    showSlide(currentSlide);
    resetAutoSlide();
}

function goToSlide(index) {
    currentSlide = index;
    showSlide(currentSlide);
    resetAutoSlide();
}

function startAutoSlide() {
    autoSlideInterval = setInterval(nextSlide, 3000);
}

function resetAutoSlide() {
    clearInterval(autoSlideInterval);
    startAutoSlide();
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    if (totalSlides > 0) {
        showSlide(0);
        startAutoSlide();
    }
    if (totalTextSlides > 0) {
        showTextSlide(0);
        startAutoTextSlide();
    }
}); 