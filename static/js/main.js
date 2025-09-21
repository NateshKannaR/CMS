// Modern CMS JavaScript

// Chatbot functionality
function toggleChatbot() {
    const popup = document.getElementById('chatbotPopup');
    if (popup.style.display === 'none' || popup.style.display === '') {
        popup.style.display = 'block';
        popup.style.animation = 'slideUp 0.3s ease';
        document.getElementById('chatInput').focus();
    } else {
        popup.style.display = 'none';
    }
}

function closeChatbot() {
    document.getElementById('chatbotPopup').style.display = 'none';
}

function handleEnter(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    const messagesDiv = document.getElementById('chatMessages');
    
    // Add user message
    messagesDiv.innerHTML += `
        <div class="mb-2 text-end">
            <span class="badge bg-primary">${message}</span>
        </div>
    `;
    
    input.value = '';
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    
    // Show typing indicator
    messagesDiv.innerHTML += `
        <div class="mb-2" id="typing">
            <span class="text-muted"><i class="fas fa-circle-notch fa-spin"></i> AI is typing...</span>
        </div>
    `;
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    
    // Send to backend
    fetch('/chatbot', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: message })
    })
    .then(response => response.json())
    .then(data => {
        // Remove typing indicator
        document.getElementById('typing').remove();
        
        // Add AI response
        messagesDiv.innerHTML += `
            <div class="mb-2">
                <span class="badge bg-light text-dark">${data.response}</span>
            </div>
        `;
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    })
    .catch(error => {
        document.getElementById('typing').remove();
        messagesDiv.innerHTML += `
            <div class="mb-2">
                <span class="badge bg-danger">Sorry, I'm having trouble right now. Please try again later.</span>
            </div>
        `;
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    });
}

// Enhanced form validation
function validateForm(formId) {
    const form = document.getElementById(formId);
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('is-invalid');
            isValid = false;
        } else {
            input.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

// Auto-save functionality for forms
function enableAutoSave(formId, saveUrl) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    const inputs = form.querySelectorAll('input, textarea, select');
    
    inputs.forEach(input => {
        input.addEventListener('input', debounce(() => {
            const formData = new FormData(form);
            
            fetch(saveUrl, {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (response.ok) {
                    showSnackbar('Changes saved automatically', 'success');
                }
            })
            .catch(() => {
                showSnackbar('Auto-save failed', 'error');
            });
        }, 2000));
    });
}

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Snackbar notifications
function showSnackbar(message, type = 'info') {
    const snackbar = document.createElement('div');
    snackbar.className = `snackbar show ${type}`;
    snackbar.textContent = message;
    
    document.body.appendChild(snackbar);
    
    setTimeout(() => {
        snackbar.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(snackbar);
        }, 300);
    }, 3000);
}

// Enhanced file upload with progress
function setupFileUpload(inputId, progressId) {
    const input = document.getElementById(inputId);
    const progress = document.getElementById(progressId);
    
    if (!input || !progress) return;
    
    input.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        const formData = new FormData();
        formData.append('file', file);
        
        const xhr = new XMLHttpRequest();
        
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percentComplete = (e.loaded / e.total) * 100;
                progress.style.width = percentComplete + '%';
                progress.textContent = Math.round(percentComplete) + '%';
            }
        });
        
        xhr.addEventListener('load', () => {
            if (xhr.status === 200) {
                showSnackbar('File uploaded successfully', 'success');
                progress.style.width = '100%';
            } else {
                showSnackbar('Upload failed', 'error');
                progress.style.width = '0%';
            }
        });
        
        xhr.addEventListener('error', () => {
            showSnackbar('Upload failed', 'error');
            progress.style.width = '0%';
        });
        
        xhr.open('POST', '/upload');
        xhr.send(formData);
    });
}

// Smooth scrolling for anchor links
document.addEventListener('DOMContentLoaded', () => {
    const links = document.querySelectorAll('a[href^="#"]');
    
    links.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            
            const targetId = link.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
});

// Enhanced search functionality
function setupSearch(inputId, resultsId) {
    const input = document.getElementById(inputId);
    const results = document.getElementById(resultsId);
    
    if (!input || !results) return;
    
    input.addEventListener('input', debounce((e) => {
        const query = e.target.value.trim();
        
        if (query.length < 2) {
            results.innerHTML = '';
            return;
        }
        
        fetch(`/search?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                results.innerHTML = '';
                
                if (data.length === 0) {
                    results.innerHTML = '<div class="text-muted p-3">No results found</div>';
                    return;
                }
                
                data.forEach(item => {
                    const div = document.createElement('div');
                    div.className = 'search-result p-2 border-bottom';
                    div.innerHTML = `
                        <div class="fw-bold">${item.title}</div>
                        <div class="text-muted small">${item.description}</div>
                    `;
                    div.addEventListener('click', () => {
                        window.location.href = item.url;
                    });
                    results.appendChild(div);
                });
            })
            .catch(() => {
                results.innerHTML = '<div class="text-danger p-3">Search failed</div>';
            });
    }, 300));
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + K for search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.querySelector('input[type="search"], input[placeholder*="search" i]');
        if (searchInput) {
            searchInput.focus();
        }
    }
    
    // Escape to close modals/popups
    if (e.key === 'Escape') {
        const chatbot = document.getElementById('chatbotPopup');
        if (chatbot && chatbot.style.display !== 'none') {
            closeChatbot();
        }
    }
});

// Initialize tooltips and popovers
document.addEventListener('DOMContentLoaded', () => {
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(tooltipTriggerEl => {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize Bootstrap popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(popoverTriggerEl => {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});

// Auto-dismiss alerts
document.addEventListener('DOMContentLoaded', () => {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
});

// Loading states for buttons
function setButtonLoading(buttonId, loading = true) {
    const button = document.getElementById(buttonId);
    if (!button) return;
    
    if (loading) {
        button.disabled = true;
        button.innerHTML = '<span class="loading me-2"></span>Loading...';
    } else {
        button.disabled = false;
        button.innerHTML = button.getAttribute('data-original-text') || 'Submit';
    }
}

// Form submission with loading state
document.addEventListener('DOMContentLoaded', () => {
    const forms = document.querySelectorAll('form[data-loading]');
    
    forms.forEach(form => {
        form.addEventListener('submit', (e) => {
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.setAttribute('data-original-text', submitButton.innerHTML);
                setButtonLoading(submitButton.id || 'submit-btn', true);
            }
        });
    });
});

// CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideUp {
        from {
            transform: translateY(20px);
            opacity: 0;
        }
        to {
            transform: translateY(0);
            opacity: 1;
        }
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    .search-result {
        cursor: pointer;
        transition: background-color 0.2s ease;
    }
    
    .search-result:hover {
        background-color: var(--hover-color);
    }
    
    .snackbar {
        animation: slideUp 0.3s ease;
    }
    
    .snackbar.success {
        background-color: var(--secondary-color);
    }
    
    .snackbar.error {
        background-color: var(--accent-color);
    }
`;
document.head.appendChild(style);