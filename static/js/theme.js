// Theme Management
class ThemeManager {
    constructor() {
        this.currentTheme = localStorage.getItem('theme') || 'light';
        this.currentLang = localStorage.getItem('language') || 'en';
        this.init();
    }

    init() {
        this.applyTheme();
        this.applyLanguage();
        this.createControls();
    }

    applyTheme() {
        document.documentElement.setAttribute('data-theme', this.currentTheme);
        localStorage.setItem('theme', this.currentTheme);
    }

    toggleTheme() {
        this.currentTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.applyTheme();
        this.updateThemeIcon();
    }

    applyLanguage() {
        document.documentElement.setAttribute('lang', this.currentLang);
        localStorage.setItem('language', this.currentLang);
        this.translatePage();
    }

    setLanguage(lang) {
        this.currentLang = lang;
        this.applyLanguage();
    }

    translatePage() {
        const elements = document.querySelectorAll('[data-translate]');
        elements.forEach(element => {
            const key = element.getAttribute('data-translate');
            if (translations[this.currentLang] && translations[this.currentLang][key]) {
                if (element.tagName === 'INPUT' && element.type === 'text') {
                    element.placeholder = translations[this.currentLang][key];
                } else {
                    element.textContent = translations[this.currentLang][key];
                }
            }
        });
    }

    createControls() {

        // Language Selector in sidebar
        const sidebar = document.querySelector('.sidebar');
        if (sidebar) {
            const langDiv = document.createElement('div');
            langDiv.className = 'p-3 border-top';
            langDiv.innerHTML = `
                <small class="text-muted d-block mb-2">Language</small>
                <select class="form-select form-select-sm" id="langSelector">
                    <option value="en" ${this.currentLang === 'en' ? 'selected' : ''}>English</option>
                    <option value="ta" ${this.currentLang === 'ta' ? 'selected' : ''}>தமிழ்</option>
                    <option value="hi" ${this.currentLang === 'hi' ? 'selected' : ''}>हिंदी</option>
                </select>
            `;
            sidebar.appendChild(langDiv);
            
            const langSelector = langDiv.querySelector('#langSelector');
            langSelector.onchange = (e) => this.setLanguage(e.target.value);
        }
    }

    updateThemeIcon() {
        const themeToggle = document.querySelector('.theme-toggle-btn i');
        if (themeToggle) {
            themeToggle.className = `fas fa-${this.currentTheme === 'light' ? 'moon' : 'sun'}`;
        }
    }
}

// Translations
const translations = {
    en: {
        dashboard: "Dashboard",
        courses: "Courses",
        assignments: "Assignments",
        messages: "Messages",
        calendar: "Calendar",
        profile: "Profile",
        logout: "Logout",
        welcome: "Welcome",
        create_course: "Create Course",
        join_course: "Join Course",
        practice_quiz: "Practice Quiz",
        notifications: "Notifications",
        students: "Students",
        teachers: "Teachers",
        admin: "Admin"
    },
    ta: {
        dashboard: "டாஷ்போர்டு",
        courses: "பாடங்கள்",
        assignments: "பணிகள்",
        messages: "செய்திகள்",
        calendar: "நாட்காட்டி",
        profile: "சுயவிவரம்",
        logout: "வெளியேறு",
        welcome: "வரவேற்கிறோம்",
        create_course: "பாடம் உருவாக்கு",
        join_course: "பாடத்தில் சேர்",
        practice_quiz: "பயிற்சி வினாடி வினா",
        notifications: "அறிவிப்புகள்",
        students: "மாணவர்கள்",
        teachers: "ஆசிரியர்கள்",
        admin: "நிர்வாகி"
    },
    hi: {
        dashboard: "डैशबोर्ड",
        courses: "पाठ्यक्रम",
        assignments: "असाइनमेंट",
        messages: "संदेश",
        calendar: "कैलेंडर",
        profile: "प्रोफ़ाइल",
        logout: "लॉगआउट",
        welcome: "स्वागत है",
        create_course: "कोर्स बनाएं",
        join_course: "कोर्स में शामिल हों",
        practice_quiz: "अभ्यास प्रश्नोत्तरी",
        notifications: "सूचनाएं",
        students: "छात्र",
        teachers: "शिक्षक",
        admin: "व्यवस्थापक"
    }
};

// Initialize Theme Manager
document.addEventListener('DOMContentLoaded', () => {
    window.themeManager = new ThemeManager();
});

// Smooth Animations
function addAnimations() {
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
        card.classList.add('animate-slide-in');
    });
}

// Initialize animations when page loads
document.addEventListener('DOMContentLoaded', addAnimations);