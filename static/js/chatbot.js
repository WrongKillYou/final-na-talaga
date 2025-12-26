// static/js/chatbot.js
// Floating Chatbot Widget with FAQ and Teacher Contact

class ChatbotWidget {
    constructor() {
        this.isOpen = false;
        this.messages = [];
        this.waitingForTeacherContact = false;
        this.init();
    }

    init() {
        this.createChatbotHTML();
        this.attachEventListeners();
        this.showWelcomeMessage();
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
                               placeholder="Type your message..."
                               disabled>
                        <button class="chatbot-send-btn" id="chatbotSend" disabled>
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
            <button class="quick-reply-btn" data-action="${btn.action}">
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
                text: `👨‍🏫 Would you like to start a conversation with your child's teacher?<br><br>
                       This will open a direct chat where you can discuss:<br>
                       • Your child's progress<br>
                       • Attendance concerns<br>
                       • Schedule questions<br>
                       • Any other concerns`,
                buttons: [
                    { action: 'start_chat', text: '✅ Yes, Contact Teacher', icon: 'bi-chat-text' },
                    { action: 'back', text: '← Back to Menu', icon: 'bi-arrow-left' }
                ]
            },
            'start_chat': {
                text: `✅ Great! I'm redirecting you to start a conversation with your teacher.<br><br>
                       <a href="/information/chat/start/" class="message-action-btn">
                           <i class="bi bi-chat-text-fill"></i> Open Teacher Chat
                       </a><br><br>
                       You can also view your message history anytime.`,
                buttons: [
                    { action: 'view_history', text: '📜 View Message History', icon: 'bi-clock-history' },
                    { action: 'back', text: '← Back to Menu', icon: 'bi-arrow-left' }
                ]
            },
            'view_history': {
                text: `Opening your message history...`,
                buttons: null
            },
            'back': {
                text: `What else would you like to know?`,
                buttons: this.getMainMenuButtons()
            }
        };

        const response = responses[action];
        if (response) {
            this.addBotMessage(response.text, response.buttons);

            // Handle special actions
            if (action === 'view_history') {
                setTimeout(() => {
                    window.location.href = '/information/chat/history/';
                }, 1500);
            }
        }
    }

    getBackButton() {
        return [
            { action: 'back', text: '← Back to Main Menu', icon: 'bi-arrow-left' }
        ];
    }

    handleSend() {
        const input = document.getElementById('chatbotInput');
        const message = input.value.trim();

        if (message) {
            this.addUserMessage(message);
            input.value = '';

            // Process custom message (you can add AI integration here)
            setTimeout(() => {
                this.addBotMessage(
                    "I'm sorry, I can only help with the menu options above. Please select one of the quick replies, or contact a teacher directly for specific questions.",
                    this.getMainMenuButtons()
                );
            }, 500);
        }
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