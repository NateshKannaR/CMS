// Modern UI Enhancement System for BrainLow CMS

// Form validation
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
                    showNotification('Changes saved automatically', 'success');
                }
            })
            .catch(() => {
                showNotification('Auto-save failed', 'error');
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

// Modern notification system
function showNotification(message, type = 'info', duration = 4000) {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = `
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        border: none;
        border-radius: 12px;
        animation: slideInRight 0.3s ease;
    `;
    
    const icons = {
        success: 'fas fa-check-circle',
        danger: 'fas fa-exclamation-circle',
        warning: 'fas fa-exclamation-triangle',
        info: 'fas fa-info-circle',
        error: 'fas fa-exclamation-circle'
    };
    
    notification.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="${icons[type] || icons.info} me-2"></i>
            <span>${message}</span>
        </div>
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, duration);
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
                showNotification('File uploaded successfully', 'success');
                progress.style.width = '100%';
            } else {
                showNotification('Upload failed', 'error');
                progress.style.width = '0%';
            }
        });
        
        xhr.addEventListener('error', () => {
            showNotification('Upload failed', 'error');
            progress.style.width = '0%';
        });
        
        xhr.open('POST', '/upload');
        xhr.send(formData);
    });
}

// Enhanced search functionality
function setupSearch(inputId, resultsId) {
    const input = document.getElementById(inputId);
    const results = document.getElementById(resultsId);
    
    if (!input || !results) return;
    
    input.addEventListener('input', debounce((e) => {
        const query = e.target.value.trim();
        
        if (query.length < 2) {
            results.innerHTML = '';
            results.style.display = 'none';
            return;
        }
        
        fetch(`/search?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                results.innerHTML = '';
                
                if (data.length === 0) {
                    results.innerHTML = '<div class="text-muted p-3">No results found</div>';
                } else {
                    data.forEach(item => {
                        const div = document.createElement('div');
                        div.className = 'search-result p-2 border-bottom cursor-pointer';
                        div.innerHTML = `
                            <div class="fw-bold">${item.title}</div>
                            <div class="text-muted small">${item.description}</div>
                        `;
                        div.addEventListener('click', () => {
                            window.location.href = item.url;
                        });
                        results.appendChild(div);
                    });
                }
                
                results.style.display = 'block';
            })
            .catch(() => {
                results.innerHTML = '<div class="text-danger p-3">Search failed</div>';
                results.style.display = 'block';
            });
    }, 300));
}

// Enhanced Chatbot functionality
class ModernChatbot {
    constructor() {
        this.isOpen = false;
        this.messages = [];
        this.init();
    }
    
    init() {
        // Create modern chatbot UI if it doesn't exist
        if (!document.getElementById('chatbotPopup')) {
            this.createChatbotUI();
        }
        
        this.bindEvents();
    }
    
    createChatbotUI() {
        const chatbotHTML = `
            <div id="chatbotPopup" class="chatbot-popup" style="display: none;">
                <div class="chatbot-header">
                    <div class="d-flex align-items-center">
                        <div class="avatar bg-primary text-white me-2" style="width: 32px; height: 32px; font-size: 0.8rem;">
                            <i class="fas fa-robot"></i>
                        </div>
                        <div>
                            <h6 class="mb-0">AI Assistant</h6>
                            <small class="text-muted">Online</small>
                        </div>
                    </div>
                    <button class="btn btn-sm btn-ghost" onclick="chatbot.close()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="chatbot-messages" id="chatMessages"></div>
                <div class="chatbot-input">
                    <div class="input-group">
                        <input type="text" id="chatInput" class="form-control" placeholder="Ask me anything..." onkeypress="chatbot.handleKeyPress(event)">
                        <button class="btn btn-primary" onclick="chatbot.sendMessage()">
                            <i class="fas fa-paper-plane"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', chatbotHTML);
        
        // Add styles
        const style = document.createElement('style');
        style.textContent = `
            .chatbot-popup {
                position: fixed;
                bottom: 90px;
                right: 20px;
                width: 380px;
                height: 500px;
                background: white;
                border-radius: 16px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.15);
                z-index: 1001;
                display: flex;
                flex-direction: column;
                overflow: hidden;
                border: 1px solid var(--gray-200);
            }
            
            .chatbot-header {
                padding: 16px;
                background: linear-gradient(135deg, var(--primary-600), var(--primary-700));
                color: white;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .chatbot-messages {
                flex: 1;
                padding: 16px;
                overflow-y: auto;
                background: var(--gray-50);
            }
            
            .chatbot-input {
                padding: 16px;
                border-top: 1px solid var(--gray-200);
                background: white;
            }
            
            .message {
                margin-bottom: 12px;
                display: flex;
                align-items: flex-start;
                gap: 8px;
            }
            
            .message.user {
                flex-direction: row-reverse;
            }
            
            .message-bubble {
                max-width: 80%;
                padding: 8px 12px;
                border-radius: 12px;
                font-size: 0.875rem;
                line-height: 1.4;
            }
            
            .message.user .message-bubble {
                background: var(--primary-600);
                color: white;
                border-bottom-right-radius: 4px;
            }
            
            .message.bot .message-bubble {
                background: white;
                color: var(--gray-800);
                border: 1px solid var(--gray-200);
                border-bottom-left-radius: 4px;
            }
            
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
            
            @media (max-width: 768px) {
                .chatbot-popup {
                    width: calc(100vw - 40px);
                    height: calc(100vh - 140px);
                    right: 20px;
                    bottom: 90px;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    bindEvents() {
        // Initialize with welcome message
        this.addMessage('Hello! I\'m your AI assistant. How can I help you today?', 'bot');
    }
    
    toggle() {
        if (this.isOpen) {
            this.close();
        } else {
            this.open();
        }
    }
    
    open() {
        const popup = document.getElementById('chatbotPopup');
        popup.style.display = 'flex';
        this.isOpen = true;
        document.getElementById('chatInput').focus();
    }
    
    close() {
        const popup = document.getElementById('chatbotPopup');
        popup.style.display = 'none';
        this.isOpen = false;
    }
    
    handleKeyPress(event) {
        if (event.key === 'Enter') {
            this.sendMessage();
        }
    }
    
    addMessage(content, sender) {
        const messagesContainer = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        messageDiv.innerHTML = `
            <div class="message-bubble">
                ${content}
            </div>
        `;
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    sendMessage() {
        const input = document.getElementById('chatInput');
        const message = input.value.trim();
        if (!message) return;
        
        // Add user message
        this.addMessage(message, 'user');
        input.value = '';
        
        // Add typing indicator
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message bot';
        typingDiv.id = 'typing-indicator';
        typingDiv.innerHTML = `
            <div class="message-bubble">
                <i class="fas fa-spinner fa-spin me-1"></i> Thinking...
            </div>
        `;
        document.getElementById('chatMessages').appendChild(typingDiv);
        
        // Send to backend
        fetch('/chatbot', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({message: message})
        })
        .then(response => response.json())
        .then(data => {
            document.getElementById('typing-indicator')?.remove();
            this.addMessage(data.response || 'Sorry, I couldn\'t process that request.', 'bot');
        })
        .catch(error => {
            document.getElementById('typing-indicator')?.remove();
            this.addMessage('Sorry, I\'m having trouble right now. Please try again later.', 'bot');
        });
    }
}

// Initialize chatbot
let chatbot;

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
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
        const openModal = document.querySelector('.modal.show');
        if (openModal) {
            const modal = bootstrap.Modal.getInstance(openModal);
            if (modal) modal.hide();
        }
        
        if (chatbot && chatbot.isOpen) {
            chatbot.close();
        }
    }
});

// Modern UI Enhancements
document.addEventListener('DOMContentLoaded', function() {
    // Initialize chatbot for students
    if (document.querySelector('.chatbot-float')) {
        chatbot = new ModernChatbot();
    }
    
    // Add smooth scrolling to all anchor links
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
    
    // Add loading states to buttons
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Loading...';
                submitBtn.disabled = true;
                
                // Re-enable after 5 seconds as fallback
                setTimeout(() => {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                }, 5000);
            }
        });
    });
    
    // Add hover effects to cards
    document.querySelectorAll('.card, .course-card').forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Auto-dismiss alerts
    document.querySelectorAll('.alert:not(.alert-permanent)').forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
    
    // Hide search results when clicking outside
    document.addEventListener('click', function(e) {
        const searchContainer = e.target.closest('.search-container');
        if (!searchContainer) {
            document.querySelectorAll('.search-results').forEach(results => {
                results.style.display = 'none';
            });
        }
    });
});

// Legacy functions for compatibility
function toggleChatbot() {
    if (chatbot) chatbot.toggle();
}

function closeChatbot() {
    if (chatbot) chatbot.close();
}

function handleEnter(event) {
    if (chatbot) chatbot.handleKeyPress(event);
}

function sendMessage() {
    if (chatbot) chatbot.sendMessage();
}

// Enhanced form handling
function handleFormSubmit(form, options = {}) {
    const formData = new FormData(form);
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn?.innerHTML;
    
    if (submitBtn) {
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
        submitBtn.disabled = true;
    }
    
    fetch(form.action || window.location.href, {
        method: form.method || 'POST',
        body: formData
    })
    .then(response => {
        if (response.ok) {
            if (options.successMessage) {
                showNotification(options.successMessage, 'success');
            }
            if (options.redirect) {
                window.location.href = options.redirect;
            } else if (options.reload) {
                window.location.reload();
            }
        } else {
            throw new Error('Form submission failed');
        }
    })
    .catch(error => {
        showNotification(options.errorMessage || 'An error occurred', 'danger');
    })
    .finally(() => {
        if (submitBtn) {
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    });
}

// Utility functions
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

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