// Chatbot functionality
document.addEventListener('DOMContentLoaded', function() {
    // Chatbot state
    let currentConversationId = null;
    let messagePollingInterval = null;
    let children = [];
    
    // Chatbot Elements
    const chatbotToggle = document.getElementById('chatbotToggle');
    const chatbotWindow = document.getElementById('chatbotWindow');
    const chatbotClose = document.getElementById('chatbotClose');
    const chatbotMessages = document.getElementById('chatbotMessages');
    const chatbotInput = document.getElementById('chatbotMessageInput');
    const chatbotSend = document.getElementById('chatbotSend');
    
    // Check if elements exist
    if (!chatbotToggle || !chatbotWindow) {
        console.error('Chatbot elements not found');
        return;
    }
    
    // Toggle chatbot window
    chatbotToggle.addEventListener('click', () => {
        chatbotWindow.classList.toggle('active');
    });
    
    chatbotClose.addEventListener('click', () => {
        chatbotWindow.classList.remove('active');
    });
    
    // Tab switching
    const tabs = document.querySelectorAll('.chatbot-tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-pane').forEach(pane => {
                pane.classList.remove('active');
            });
            
            tab.classList.add('active');
            const tabName = tab.dataset.tab;
            
            if (tabName === 'chat') {
                document.getElementById('chatTab').classList.add('active');
            } else if (tabName === 'live-chat') {
                document.getElementById('liveChatTab').classList.add('active');
                loadLiveChat();
            } else if (tabName === 'announcements') {
                document.getElementById('announcementsTab').classList.add('active');
                loadAnnouncements();
            } else if (tabName === 'events') {
                document.getElementById('eventsTab').classList.add('active');
                loadEvents();
            } else if (tabName === 'faq') {
                document.getElementById('faqTab').classList.add('active');
                loadFAQ();
            }
        });
    });
    
    // Load children for schedule query
    fetch('/information/api/children/')
        .then(response => response.json())
        .then(data => {
            children = data;
            
            // Populate live chat child selector
            const liveChatSelect = document.getElementById('liveChatChildSelect');
            if (liveChatSelect) {
                children.forEach(child => {
                    const option = document.createElement('option');
                    option.value = child.id;
                    option.textContent = `${child.name} (${child.grade_level} - ${child.section})`;
                    liveChatSelect.appendChild(option);
                });
            }
        })
        .catch(error => {
            console.error('Error loading children:', error);
        });
    
    // Send message function
    function sendMessage() {
        const message = chatbotInput.value.trim();
        if (!message) return;
        
        addMessage(message, 'user');
        chatbotInput.value = '';
        
        showTypingIndicator();
        
        setTimeout(() => {
            processMessage(message);
        }, 1000);
    }
    
    if (chatbotSend) {
        chatbotSend.addEventListener('click', sendMessage);
    }
    
    if (chatbotInput) {
        chatbotInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }
    
    // Quick reply buttons
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('quick-reply')) {
            const action = e.target.dataset.action;
            handleQuickAction(action);
        }
    });
    
    // Add message to chat
    function addMessage(text, type = 'bot') {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chatbot-message ${type}-message`;
        
        messageDiv.innerHTML = `
            <div class="message-avatar">
                <i class="bi bi-${type === 'bot' ? 'robot' : 'person-fill'}"></i>
            </div>
            <div class="message-content">
                <p>${text}</p>
            </div>
        `;
        
        chatbotMessages.appendChild(messageDiv);
        chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
    }
    
    // Show typing indicator
    function showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'chatbot-message bot-message typing';
        typingDiv.innerHTML = `
            <div class="message-avatar">
                <i class="bi bi-robot"></i>
            </div>
            <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
            </div>
        `;
        chatbotMessages.appendChild(typingDiv);
        chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
    }
    
    function removeTypingIndicator() {
        const typing = document.querySelector('.typing');
        if (typing) typing.remove();
    }
    
    // Process message with AI-like responses
    function processMessage(message) {
        removeTypingIndicator();
        
        const lowerMessage = message.toLowerCase();
        let response = '';
        
        // Check for schedule query
        if (lowerMessage.includes('schedule') || lowerMessage.includes('class')) {
            if (children.length === 0) {
                response = 'No children found in your account. Please contact the school administrator.';
                addMessage(response, 'bot');
            } else if (children.length === 1) {
                // Only one child, fetch schedule directly
                fetchChildSchedule(children[0].id);
                return;
            } else {
                // Multiple children, show selection
                response = 'Which child\'s schedule would you like to see?';
                addMessage(response, 'bot');
                
                const buttonsDiv = document.createElement('div');
                buttonsDiv.className = 'quick-replies mt-2';
                children.forEach(child => {
                    const btn = document.createElement('button');
                    btn.className = 'quick-reply';
                    btn.textContent = `${child.name}`;
                    btn.onclick = () => fetchChildSchedule(child.id);
                    buttonsDiv.appendChild(btn);
                });
                
                const lastMessage = document.querySelector('.chatbot-messages .chatbot-message:last-child .message-content');
                if (lastMessage) {
                    lastMessage.appendChild(buttonsDiv);
                }
                return;
            }
        } else if (lowerMessage.includes('announcement')) {
            response = 'Let me show you the latest announcements!';
            addMessage(response, 'bot');
            setTimeout(() => {
                document.querySelector('[data-tab="announcements"]').click();
            }, 500);
            return;
        } else if (lowerMessage.includes('event')) {
            response = 'Here are the upcoming school events!';
            addMessage(response, 'bot');
            setTimeout(() => {
                document.querySelector('[data-tab="events"]').click();
            }, 500);
            return;
        } else if (lowerMessage.includes('teacher') || lowerMessage.includes('ask')) {
            response = 'You can chat with a teacher using the "Ask Teacher" tab!';
            addMessage(response, 'bot');
            setTimeout(() => {
                document.querySelector('[data-tab="live-chat"]').click();
            }, 500);
            return;
        } else if (lowerMessage.includes('contact') || lowerMessage.includes('phone')) {
            response = 'You can reach us at:<br>📞 Phone: (123) 456-7890<br>📧 Email: info@school.edu<br>📍 Address: 123 School Street';
        } else if (lowerMessage.includes('hello') || lowerMessage.includes('hi')) {
            response = 'Hello! How can I assist you today? You can ask me about class schedules, announcements, events, or talk to a teacher.';
        } else {
            response = 'I\'m here to help! You can ask me about:<br>• Class schedules<br>• Recent announcements<br>• Upcoming events<br>• Talk to a teacher<br>• Contact information';
        }
        
        addMessage(response, 'bot');
    }
    
    // Fetch child schedule
    function fetchChildSchedule(childId) {
        showTypingIndicator();
        
        fetch(`/information/api/children/${childId}/schedule/`)
            .then(response => response.json())
            .then(data => {
                removeTypingIndicator();
                
                let scheduleHtml = `<strong>${data.child_name}'s Schedule</strong><br>`;
                scheduleHtml += `<small>${data.grade_level} - ${data.section}</small><br><br>`;
                
                if (data.schedule.length === 0) {
                    scheduleHtml += '<em>No enrolled subjects yet.</em>';
                } else {
                    scheduleHtml += '<div style="font-size: 13px;">';
                    data.schedule.forEach(item => {
                        scheduleHtml += `
                            <div style="margin-bottom: 10px; padding: 8px; background: #f8f9fa; border-radius: 6px;">
                                <strong>📚 ${item.subject}</strong><br>
                                <small>👨‍🏫 ${item.teacher}</small><br>
                                <small>📍 ${item.room}</small>
                            </div>
                        `;
                    });
                    scheduleHtml += '</div>';
                }
                
                addMessage(scheduleHtml, 'bot');
            })
            .catch(error => {
                removeTypingIndicator();
                addMessage('Sorry, I couldn\'t fetch the schedule. Please try again later.', 'bot');
            });
    }
    
    // Handle quick actions
    function handleQuickAction(action) {
        if (action === 'schedule') {
            processMessage('show me the schedule');
        } else if (action === 'announcements') {
            document.querySelector('[data-tab="announcements"]').click();
        } else if (action === 'events') {
            document.querySelector('[data-tab="events"]').click();
        } else if (action === 'help') {
            document.querySelector('[data-tab="faq"]').click();
        }
    }
    
    // Load announcements
    function loadAnnouncements() {
        const container = document.querySelector('#announcementsTab .chatbot-messages');
        
        fetch('/information/api/announcements/recent/')
            .then(response => response.json())
            .then(data => {
                container.innerHTML = '';
                
                if (data.length === 0) {
                    container.innerHTML = '<p class="text-center text-muted">No announcements available.</p>';
                    return;
                }
                
                data.forEach(announcement => {
                    const card = document.createElement('div');
                    card.className = `announcement-card ${announcement.is_important ? 'important' : ''}`;
                    card.innerHTML = `
                        ${announcement.is_important ? '<span class="badge bg-danger mb-2">Important</span>' : ''}
                        <h6>${announcement.title}</h6>
                        <p>${announcement.content.substring(0, 100)}...</p>
                        <small>${new Date(announcement.publish_date).toLocaleDateString()}</small>
                    `;
                    container.appendChild(card);
                });
            })
            .catch(error => {
                container.innerHTML = '<p class="text-center text-danger">Error loading announcements.</p>';
            });
    }
    
    // Load events
    function loadEvents() {
        const container = document.querySelector('#eventsTab .chatbot-messages');
        
        fetch('/information/api/events/upcoming/')
            .then(response => response.json())
            .then(data => {
                container.innerHTML = '';
                
                if (data.length === 0) {
                    container.innerHTML = '<p class="text-center text-muted">No upcoming events.</p>';
                    return;
                }
                
                data.forEach(event => {
                    const card = document.createElement('div');
                    card.className = 'event-card';
                    card.innerHTML = `
                        <h6>${event.title}</h6>
                        <p>${event.description.substring(0, 80)}...</p>
                        <small>📅 ${new Date(event.date).toLocaleDateString()} ${event.start_time ? 'at ' + event.start_time : ''}</small>
                    `;
                    container.appendChild(card);
                });
            })
            .catch(error => {
                container.innerHTML = '<p class="text-center text-danger">Error loading events.</p>';
            });
    }
    
    // Load FAQ
    function loadFAQ() {
        const container = document.getElementById('faqList');
        const faqs = [
            {
                question: 'What are the school hours?',
                answer: 'Regular classes run from 7:30 AM to 3:30 PM, Monday through Friday.'
            },
            {
                question: 'How do I view my child\'s class schedule?',
                answer: 'You can ask me "show schedule" in the chat, or go to your child\'s detail page from the dashboard.'
            },
            {
                question: 'How can I check my child\'s grades?',
                answer: 'You can view grades anytime through your parent dashboard. Grades are updated regularly by teachers.'
            },
            {
                question: 'How do I contact teachers?',
                answer: 'You can use the "Ask Teacher" tab to start a live chat with available teachers.'
            },
            {
                question: 'What if my child is absent?',
                answer: 'Please inform the school through the attendance system or call the office. Provide a valid excuse letter upon return.'
            }
        ];
        
        container.innerHTML = '';
        faqs.forEach((faq, index) => {
            const faqItem = document.createElement('div');
            faqItem.className = 'faq-item';
            faqItem.innerHTML = `
                <button class="faq-question">
                    ${faq.question}
                    <i class="bi bi-chevron-down"></i>
                </button>
                <div class="faq-answer">${faq.answer}</div>
            `;
            
            faqItem.querySelector('.faq-question').addEventListener('click', () => {
                faqItem.classList.toggle('active');
            });
            
            container.appendChild(faqItem);
        });
    }
    
    // ========================================
    // LIVE CHAT FUNCTIONALITY
    // ========================================
    
    function loadLiveChat() {
        const loading = document.getElementById('liveChatLoading');
        const noActive = document.getElementById('noActiveChat');
        const active = document.getElementById('activeChat');
        const inputArea = document.getElementById('liveChatInputArea');
        
        loading.style.display = 'flex';
        noActive.style.display = 'none';
        active.style.display = 'none';
        inputArea.style.display = 'none';
        
        fetch('/information/api/chat/conversations/')
            .then(response => response.json())
            .then(data => {
                loading.style.display = 'none';
                
                if (data.has_active) {
                    currentConversationId = data.conversation.id;
                    active.style.display = 'block';
                    inputArea.style.display = 'flex';
                    loadConversationMessages(currentConversationId);
                    startMessagePolling();
                } else {
                    currentConversationId = null;
                    noActive.style.display = 'block';
                }
            })
            .catch(error => {
                loading.style.display = 'none';
                noActive.innerHTML = '<p class="text-center text-danger">Error loading chat</p>';
                noActive.style.display = 'block';
            });
    }
    
    // Start live chat
    const startLiveChatBtn = document.getElementById('startLiveChatBtn');
    if (startLiveChatBtn) {
        startLiveChatBtn.addEventListener('click', function() {
            const initialMessage = document.getElementById('initialMessage').value.trim();
            const childId = document.getElementById('liveChatChildSelect').value;
            
            if (!initialMessage) {
                alert('Please type a message');
                return;
            }
            
            this.disabled = true;
            this.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Starting...';
            
            fetch('/information/api/chat/conversations/create/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    initial_message: initialMessage,
                    child_id: childId || null,
                    subject: 'General Inquiry'
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('initialMessage').value = '';
                    loadLiveChat();
                } else {
                    alert(data.error || 'Failed to start conversation');
                    this.disabled = false;
                    this.innerHTML = '<i class="bi bi-send"></i> Start Conversation';
                }
            })
            .catch(error => {
                alert('Error starting conversation');
                this.disabled = false;
                this.innerHTML = '<i class="bi bi-send"></i> Start Conversation';
            });
        });
    }
    
    // Load conversation messages
    function loadConversationMessages(conversationId) {
        fetch(`/information/api/chat/conversations/${conversationId}/messages/`)
            .then(response => response.json())
            .then(data => {
                const container = document.getElementById('liveChatMessages');
                container.innerHTML = '';
                
                data.messages.forEach(msg => {
                    addLiveChatMessage(msg);
                });
                
                container.scrollTop = container.scrollHeight;
            });
    }
    
    // Add live chat message
    function addLiveChatMessage(msg) {
        const container = document.getElementById('liveChatMessages');
        const messageDiv = document.createElement('div');
        
        let messageClass = 'bot-message';
        let icon = 'robot';
        
        if (msg.sender_role === 'parent') {
            messageClass = 'user-message';
            icon = 'person-fill';
        } else if (msg.sender_role === 'teacher') {
            messageClass = 'teacher-message';
            icon = 'person-badge';
        } else if (msg.sender_role === 'system') {
            messageClass = 'system-message';
            icon = 'info-circle';
        }
        
        messageDiv.className = `chatbot-message ${messageClass}`;
        messageDiv.innerHTML = `
            <div class="message-avatar">
                <i class="bi bi-${icon}"></i>
            </div>
            <div class="message-content">
                <p>${msg.message}</p>
                <small class="message-time">${new Date(msg.timestamp).toLocaleTimeString()}</small>
            </div>
        `;
        
        container.appendChild(messageDiv);
    }
    
    // Send live chat message
    const liveChatSend = document.getElementById('liveChatSend');
    const liveChatMessageInput = document.getElementById('liveChatMessageInput');
    
    if (liveChatSend) {
        liveChatSend.addEventListener('click', sendLiveChatMessage);
    }
    
    if (liveChatMessageInput) {
        liveChatMessageInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendLiveChatMessage();
            }
        });
    }
    
    function sendLiveChatMessage() {
        const input = document.getElementById('liveChatMessageInput');
        const message = input.value.trim();
        
        if (!message || !currentConversationId) return;
        
        input.value = '';
        input.disabled = true;
        
        fetch(`/information/api/chat/conversations/${currentConversationId}/send/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ message: message })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                addLiveChatMessage(data.message);
                document.getElementById('liveChatMessages').scrollTop = document.getElementById('liveChatMessages').scrollHeight;
            }
            input.disabled = false;
            input.focus();
        })
        .catch(error => {
            alert('Error sending message');
            input.disabled = false;
        });
    }
    
    // Close conversation
    const closeLiveChatBtn = document.getElementById('closeLiveChatBtn');
    if (closeLiveChatBtn) {
        closeLiveChatBtn.addEventListener('click', function() {
            if (!currentConversationId) return;
            
            if (!confirm('Are you sure you want to end this conversation?')) return;
            
            fetch(`/information/api/chat/conversations/${currentConversationId}/close/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    stopMessagePolling();
                    loadLiveChat();
                }
            });
        });
    }
    
    // Poll for new messages
    function startMessagePolling() {
        if (messagePollingInterval) {
            clearInterval(messagePollingInterval);
        }
        
        messagePollingInterval = setInterval(() => {
            if (currentConversationId && document.getElementById('activeChat').style.display === 'block') {
                loadConversationMessages(currentConversationId);
            }
        }, 3000); // Poll every 3 seconds
    }
    
    function stopMessagePolling() {
        if (messagePollingInterval) {
            clearInterval(messagePollingInterval);
            messagePollingInterval = null;
        }
    }
    
    // Get CSRF token
    function getCookie(name) {
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
    
    // Check for unread messages periodically
    setInterval(() => {
        fetch('/information/api/chat/unread-count/')
            .then(response => response.json())
            .then(data => {
                const badge = document.getElementById('chatbotBadge');
                const notification = document.getElementById('liveChatNotification');
                
                if (data.count > 0) {
                    badge.textContent = data.count;
                    badge.style.display = 'flex';
                    if (notification) notification.style.display = 'block';
                } else {
                    badge.style.display = 'none';
                    if (notification) notification.style.display = 'none';
                }
            })
            .catch(error => {
                console.error('Error checking unread messages:', error);
            });
    }, 5000); // Check every 5 seconds
});