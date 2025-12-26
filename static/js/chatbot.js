// static/js/chatbot.js
// Floating Chatbot Widget with FAQ and Teacher Contact

class ChatbotWidget {
    constructor() {
        this.isOpen = false;
        this.messages = [];
        this.waitingForTeacherSelection = false;
        this.waitingForChildSelection = false;
        this.pendingMessage = null;
        this.availableChildren = [];
        this.selectedChild = null;
        this.init();
    }

    init() {
        this.createChatbotHTML();
        this.attachEventListeners();
        this.showWelcomeMessage();
        this.loadChildren();
    }

    createChatbotHTML() {
        const chatbotHTML = `
            <!-- Floating Chatbot Toggle Button -->
            <button class="chatbot-toggle" id="chatbotToggle">
                <i class="bi bi-chat-dots-fill"></i>
            </button>

            <!-- Chatbot Window -->
            <div class="chatbot-window" id="chatbotWindow">
                <!-- Header -->
                <div class="chatbot-header">
                    <div class="chatbot-header-title">
                        <div class="chatbot-avatar">🤖</div>
                        <div>
                            <h5>KinderCare Assistant</h5>
                            <small>Always here to help</small>
                        </div>
                    </div>
                    <button class="chatbot-close" id="chatbotClose">
                        <i class="bi bi-x-lg"></i>
                    </button>
                </div>

                <!-- Messages Area -->
                <div class="chatbot-messages" id="chatbotMessages">
                    <!-- Messages will be inserted here -->
                </div>

                <!-- Input Area -->
                <div class="chatbot-input-area">
                    <div class="chatbot-input-container">
                        <input type="text" 
                               class="chatbot-input" 
                               id="chatbotInput" 
                               placeholder="Type your message...">
                        <button class="chatbot-send-btn" id="chatbotSend">
                            <i class="bi bi-send-fill"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', chatbotHTML);
    }

    attachEventListeners() {
        const toggle = document.getElementById('chatbotToggle');
        const close = document.getElementById('chatbotClose');
        const send = document.getElementById('chatbotSend');
        const input = document.getElementById('chatbotInput');

        toggle.addEventListener('click', () => this.toggleChatbot());
        close.addEventListener('click', () => this.closeChatbot());
        send.addEventListener('click', () => this.handleSend());
        
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handleSend();
            }
        });

        // Handle quick reply buttons (delegated event)
        document.getElementById('chatbotMessages').addEventListener('click', (e) => {
            if (e.target.classList.contains('quick-reply-btn')) {
                this.handleQuickReply(e.target.dataset.action, e.target.textContent);
            }
            
            // Handle child selection
            if (e.target.classList.contains('child-select-btn')) {
                this.selectChild(e.target.dataset.childId, e.target.dataset.childName);
            }
        });
    }

    toggleChatbot() {
        this.isOpen = !this.isOpen;
        const window = document.getElementById('chatbotWindow');
        const toggle = document.getElementById('chatbotToggle');
        
        if (this.isOpen) {
            window.classList.add('active');
            toggle.classList.add('active');
            toggle.innerHTML = '<i class="bi bi-x-lg"></i>';
            this.scrollToBottom();
        } else {
            window.classList.remove('active');
            toggle.classList.remove('active');
            toggle.innerHTML = '<i class="bi bi-chat-dots-fill"></i>';
        }
    }

    closeChatbot() {
        this.isOpen = false;
        document.getElementById('chatbotWindow').classList.remove('active');
        const toggle = document.getElementById('chatbotToggle');
        toggle.classList.remove('active');
        toggle.innerHTML = '<i class="bi bi-chat-dots-fill"></i>';
    }

    showWelcomeMessage() {
        setTimeout(() => {
            this.addBotMessage(
                "👋 Hello! Welcome to KinderCare! I'm your virtual assistant. How can I help you today?",
                this.getMainMenuButtons()
            );
        }, 500);
    }

    getMainMenuButtons() {
        return [
            { action: 'hours', text: '🕒 Operating Hours', icon: 'bi-clock' },
            { action: 'enrollment', text: '📝 Enrollment Info', icon: 'bi-file-text' },
            { action: 'curriculum', text: '📚 Curriculum', icon: 'bi-book' },
            { action: 'fees', text: '💰 Fees & Payment', icon: 'bi-cash' },
            { action: 'contact', text: '📞 Contact Teacher', icon: 'bi-person-video' }
        ];
    }

    addMessage(type, text, quickReplies = null) {
        const messagesContainer = document.getElementById('chatbotMessages');
        const time = new Date().toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });

        let avatarContent = type === 'bot' ? '🤖' : '👤';
        
        const messageHTML = `
            <div class="message ${type}">
                <div class="message-avatar">${avatarContent}</div>
                <div>
                    <div class="message-bubble">
                        ${text}
                    </div>
                    <div class="message-time">${time}</div>
                    ${quickReplies ? this.createQuickReplies(quickReplies) : ''}
                </div>
            </div>
        `;

        messagesContainer.insertAdjacentHTML('beforeend', messageHTML);
        this.scrollToBottom();
    }

    addBotMessage(text, quickReplies = null) {
        // Show typing indicator
        this.showTypingIndicator();

        // Simulate typing delay
        setTimeout(() => {
            this.hideTypingIndicator();
            this.addMessage('bot', text, quickReplies);
        }, 800);
    }

    addUserMessage(text) {
        this.addMessage('user', text);
    }

    createQuickReplies(buttons) {
        const buttonsHTML = buttons.map(btn => `
            <button class="quick-reply-btn ${btn.class || ''}" 
                    data-action="${btn.action}"
                    ${btn.childId ? `data-child-id="${btn.childId}"` : ''}
                    ${btn.childName ? `data-child-name="${btn.childName}"` : ''}>
                <i class="bi ${btn.icon || 'bi-arrow-right'}"></i>
                ${btn.text}
            </button>
        `).join('');

        return `<div class="quick-replies">${buttonsHTML}</div>`;
    }

    showTypingIndicator() {
        const messagesContainer = document.getElementById('chatbotMessages');
        const typingHTML = `
            <div class="message bot" id="typingIndicator">
                <div class="message-avatar">🤖</div>
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        messagesContainer.insertAdjacentHTML('beforeend', typingHTML);
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        const indicator = document.getElementById('typingIndicator');
        if (indicator) {
            indicator.remove();
        }
    }

    handleQuickReply(action, text) {
        // Add user's choice as message
        this.addUserMessage(text);

        // Process the action
        setTimeout(() => {
            this.processAction(action);
        }, 500);
    }

    processAction(action) {
        const responses = {
            'hours': {
                text: `📅 <strong>Operating Hours:</strong><br><br>
                       Monday - Friday: 7:00 AM - 6:00 PM<br>
                       Saturday: 8:00 AM - 12:00 PM<br>
                       Sunday: Closed<br><br>
                       We're closed on public holidays.`,
                buttons: this.getBackButton()
            },
            'enrollment': {
                text: `📋 <strong>Enrollment Process:</strong><br><br>
                       1. Fill out the enrollment form<br>
                       2. Submit required documents (Birth Certificate, Medical Records)<br>
                       3. Schedule an orientation visit<br>
                       4. Complete enrollment fee payment<br><br>
                       Current openings available!`,
                buttons: this.getBackButton()
            },
            'curriculum': {
                text: `📖 <strong>Our Curriculum:</strong><br><br>
                       We follow the K-12 Kindergarten Framework with focus on:<br><br>
                       • Health & Motor Development<br>
                       • Socio-Emotional Development<br>
                       • Language & Literacy<br>
                       • Mathematics<br>
                       • Understanding the Environment<br><br>
                       Learning through play-based activities!`,
                buttons: this.getBackButton()
            },
            'fees': {
                text: `💳 <strong>Fees & Payment:</strong><br><br>
                       Monthly Tuition: ₱3,500<br>
                       Enrollment Fee: ₱2,000 (one-time)<br>
                       Materials Fee: ₱1,500/semester<br><br>
                       Payment Options:<br>
                       • Cash/Check<br>
                       • Bank Transfer<br>
                       • GCash/PayMaya<br><br>
                       Sibling discounts available!`,
                buttons: this.getBackButton()
            },
            'contact': {
                text: `👨‍🏫 I can help you start a conversation with a teacher!<br><br>
                       Would you like to specify which child this is about?`,
                buttons: null
            },
            'back': {
                text: `What else would you like to know?`,
                buttons: this.getMainMenuButtons()
            }
        };

        const response = responses[action];
        if (response) {
            if (action === 'contact') {
                this.showChildSelection();
            } else {
                this.addBotMessage(response.text, response.buttons);
            }
        }
    }

    loadChildren() {
        // Fetch parent's children
        fetch('/information/api/children/')
            .then(response => response.json())
            .then(data => {
                this.availableChildren = data || [];
            })
            .catch(error => {
                console.error('Error loading children:', error);
                this.availableChildren = [];
            });
    }

    showChildSelection() {
        if (this.availableChildren.length === 0) {
            // No children, proceed directly to create conversation
            this.addBotMessage(
                "I'll help you start a conversation with a teacher. You can type your message below, or click the button to open the chat window.",
                [
                    { action: 'open_chat', text: '💬 Open Chat Window', icon: 'bi-chat-text' },
                    { action: 'back', text: '← Back to Menu', icon: 'bi-arrow-left' }
                ]
            );
            this.waitingForTeacherSelection = true;
            return;
        }

        const childButtons = this.availableChildren.map(child => ({
            action: 'select_child',
            text: `${child.name}`,
            icon: 'bi-person-circle',
            class: 'child-select-btn',
            childId: child.id,
            childName: child.name
        }));

        childButtons.push({ 
            action: 'no_child', 
            text: 'General Question (no specific child)', 
            icon: 'bi-chat-dots' 
        });
        childButtons.push({ 
            action: 'back', 
            text: '← Back to Menu', 
            icon: 'bi-arrow-left' 
        });

        this.addBotMessage(
            "👶 Please select which child this is about:",
            childButtons
        );
    }

    selectChild(childId, childName) {
        this.addUserMessage(`About ${childName}`);
        this.selectedChild = childId;
        this.showMessagePrompt(childName);
    }

    showMessagePrompt(childName) {
        this.waitingForTeacherSelection = true;
        
        const message = childName 
            ? `Great! You can now type your question or concern about ${childName}, or click the button below to open the chat window.`
            : `Great! You can now type your question or concern, or click the button below to open the chat window.`;
        
        this.addBotMessage(
            message,
            [
                { action: 'open_chat', text: '💬 Open Chat Window', icon: 'bi-chat-text' },
                { action: 'back', text: '← Back to Menu', icon: 'bi-arrow-left' }
            ]
        );
    }

    createConversationWithMessage(message) {
        this.addBotMessage(
            `Creating conversation and sending your message...`,
            null
        );

        // Prepare request data
        const requestData = {
            initial_message: message,
            subject: message.substring(0, 100) // First 100 chars as subject
        };

        // Add child_id if selected
        if (this.selectedChild) {
            requestData.child_id = this.selectedChild;
        }

        // Send the message via API
        fetch('/information/api/chat/create/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify(requestData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.addBotMessage(
                    `✅ Your message has been sent! ${data.assigned ? 'A teacher has been assigned to help you.' : 'A teacher will respond to you shortly.'}<br><br>
                    Redirecting to your conversation...`,
                    null
                );
                setTimeout(() => {
                    window.location.href = `/information/chat/conversation/${data.conversation_id}/`;
                }, 2000);
            } else if (data.conversation_id) {
                // Already has active conversation
                this.addBotMessage(
                    `You already have an active conversation. Redirecting you there...`,
                    null
                );
                setTimeout(() => {
                    window.location.href = `/information/chat/conversation/${data.conversation_id}/`;
                }, 1500);
            } else {
                this.addBotMessage(
                    `Sorry, there was an error: ${data.error || 'Unknown error'}. Please try again.`,
                    this.getBackButton()
                );
            }
        })
        .catch(error => {
            console.error('Error:', error);
            this.addBotMessage(
                "Sorry, there was an error. Please try again.",
                this.getBackButton()
            );
        });

        this.pendingMessage = null;
        this.waitingForTeacherSelection = false;
        this.selectedChild = null;
    }

    getBackButton() {
        return [
            { action: 'back', text: '← Back to Main Menu', icon: 'bi-arrow-left' }
        ];
    }

    handleSend() {
        const input = document.getElementById('chatbotInput');
        const message = input.value.trim();

        if (!message) return;

        this.addUserMessage(message);
        input.value = '';

        // Check if waiting for teacher contact
        if (this.waitingForTeacherSelection) {
            this.pendingMessage = message;
            this.createConversationWithMessage(message);
            return;
        }

        // Try to match with FAQ keywords (simple matching)
        const lowerMessage = message.toLowerCase();
        let matchedAction = null;

        if (lowerMessage.includes('hour') || lowerMessage.includes('time') || lowerMessage.includes('open') || lowerMessage.includes('close')) {
            matchedAction = 'hours';
        } else if (lowerMessage.includes('enroll') || lowerMessage.includes('admission') || lowerMessage.includes('register')) {
            matchedAction = 'enrollment';
        } else if (lowerMessage.includes('curriculum') || lowerMessage.includes('program') || lowerMessage.includes('learn') || lowerMessage.includes('teach')) {
            matchedAction = 'curriculum';
        } else if (lowerMessage.includes('fee') || lowerMessage.includes('tuition') || lowerMessage.includes('payment') || lowerMessage.includes('cost') || lowerMessage.includes('price')) {
            matchedAction = 'fees';
        } else if (lowerMessage.includes('teacher') || lowerMessage.includes('talk') || lowerMessage.includes('speak') || lowerMessage.includes('contact')) {
            matchedAction = 'contact';
        }

        if (matchedAction) {
            // Found a match, respond with FAQ
            setTimeout(() => {
                this.processAction(matchedAction);
            }, 500);
        } else {
            // No match found, offer to contact teacher
            this.pendingMessage = message;
            
            setTimeout(() => {
                this.addBotMessage(
                    `I understand you have a specific question. Would you like me to connect you with a teacher who can help?<br><br>
                    Your message: "<em>${message}</em>"`,
                    [
                        { action: 'contact', text: '✅ Yes, Contact Teacher', icon: 'bi-chat-text' },
                        { action: 'back', text: '← Back to Menu', icon: 'bi-arrow-left' }
                    ]
                );
            }, 500);
        }
    }

    getCSRFToken() {
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    scrollToBottom() {
        const messagesContainer = document.getElementById('chatbotMessages');
        setTimeout(() => {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }, 100);
    }
}

// Initialize chatbot when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize on parent dashboard
    if (document.body.classList.contains('parent-dashboard') || 
        window.location.pathname.includes('parent/dashboard')) {
        new ChatbotWidget();
    }
});