// Auto-hide flash message alerts after 5 seconds (not admin notifications)
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert:not(.admin-notification)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.style.opacity = '0';
            setTimeout(function() {
                alert.remove();
            }, 300);
        }, 5000);
    });
});

// Form validation
function validateForm(formId) {
    const form = document.getElementById(formId);
    const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
    let isValid = true;
    
    inputs.forEach(function(input) {
        if (!input.value.trim()) {
            input.classList.add('is-invalid');
            isValid = false;
        } else {
            input.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

// File upload preview
function previewFile(input) {
    const file = input.files[0];
    const preview = document.getElementById('file-preview');
    
    if (file && preview) {
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.innerHTML = `<p><strong>Selected:</strong> ${file.name}</p>`;
        };
        reader.readAsDataURL(file);
    }
}

// Auto-refresh messages every 30 seconds
function refreshMessages() {
    const messageContainer = document.querySelector('.message-container');
    if (messageContainer) {
        // This would typically make an AJAX call to refresh messages
        // For now, we'll just scroll to bottom if new content is added
        messageContainer.scrollTop = messageContainer.scrollHeight;
    }
}

setInterval(refreshMessages, 30000);

// Smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        document.querySelector(this.getAttribute('href')).scrollIntoView({
            behavior: 'smooth'
        });
    });
});

// Grade input validation
function validateGrade(input, maxPoints) {
    const value = parseInt(input.value);
    if (value > maxPoints) {
        input.value = maxPoints;
        alert(`Grade cannot exceed ${maxPoints} points`);
    }
    if (value < 0) {
        input.value = 0;
    }
}

// Character counter for textareas
function addCharacterCounter(textareaId, maxLength = 1000) {
    const textarea = document.getElementById(textareaId);
    if (textarea) {
        const counter = document.createElement('small');
        counter.className = 'text-muted';
        counter.id = textareaId + '-counter';
        textarea.parentNode.appendChild(counter);
        
        function updateCounter() {
            const remaining = maxLength - textarea.value.length;
            counter.textContent = `${remaining} characters remaining`;
            if (remaining < 50) {
                counter.className = 'text-warning';
            } else {
                counter.className = 'text-muted';
            }
        }
        
        textarea.addEventListener('input', updateCounter);
        updateCounter();
    }
}

// Initialize character counters
document.addEventListener('DOMContentLoaded', function() {
    addCharacterCounter('content', 2000);
    addCharacterCounter('description', 500);
});

// Chatbot functions
function toggleChatbot() {
    const modal = new bootstrap.Modal(document.getElementById('chatbotModal'));
    modal.show();
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
    
    const chatMessages = document.getElementById('chatMessages');
    
    // Add user message
    chatMessages.innerHTML += `<div class="mb-2"><strong>You:</strong> ${message}</div>`;
    input.value = '';
    
    // Add loading indicator
    chatMessages.innerHTML += `<div class="mb-2 text-muted" id="loading"><strong>AI:</strong> <i class="fas fa-spinner fa-spin"></i> Thinking...</div>`;
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Send to backend
    fetch('/chatbot', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message: message})
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('loading').remove();
        chatMessages.innerHTML += `<div class="mb-2"><strong>AI:</strong> ${data.response}</div>`;
        chatMessages.scrollTop = chatMessages.scrollHeight;
    })
    .catch(error => {
        document.getElementById('loading').remove();
        chatMessages.innerHTML += `<div class="mb-2 text-danger"><strong>AI:</strong> Sorry, I'm having trouble right now. Please try again later.</div>`;
        chatMessages.scrollTop = chatMessages.scrollHeight;
    });
}