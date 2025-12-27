// chatbot.js - KinderCare Messenger Chat System
// This should be placed in your static/js/ folder

(function() {
    'use strict';

    // ==================== CONFIGURATION ====================
    const FAQ_DATA = []; // Will be loaded from database
    let FAQ_LOADED = false;

    // ==================== STATE MANAGEMENT ====================
    let chatState = {
        isOpen: false,
        activeConvId: null,
        conversations: [],
        userRole: null,
        userName: null,
        csrfToken: null,
        messageRefreshInterval: null,
        selectedFile: null
    };

    // ==================== UTILITY FUNCTIONS ====================
    function getCurrentTime() {
        const now = new Date();
        return now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    }

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

    // ==================== INITIALIZATION ====================
    function initChat() {
        chatState.csrfToken = getCookie('csrftoken');
        
        // Get user role from data attribute or detect from page
        const chatContainer = document.getElementById('kindercare-chat');
        if (chatContainer) {
            chatState.userRole = chatContainer.dataset.userRole || detectUserRole();
            chatState.userName = chatContainer.dataset.userName || 'User';
        }

        createChatHTML();
        
        if (chatState.userRole === 'parent') {
            initParentConversations();
            // Auto-refresh for parents every 30 seconds to see new messages
            setInterval(() => {
                if (chatState.isOpen && chatState.activeConvId === null) {
                    loadParentConversations();
                }
            }, 30000);
        } else if (chatState.userRole === 'teacher') {
            loadTeacherConversations();
            // Auto-refresh for teachers every 30 seconds
            setInterval(() => {
                if (chatState.isOpen && chatState.activeConvId === null) {
                    loadTeacherConversations();
                }
            }, 30000);
        }

        attachEventListeners();
    }

    function detectUserRole() {
        // Try to detect from URL or page class
        const path = window.location.pathname;
        if (path.includes('/parent/')) return 'parent';
        if (path.includes('/teacher/')) return 'teacher';
        return 'parent'; // default
    }

    function initParentConversations() {
        // Load FAQs from database first
        loadFAQs().then(() => {
            // Then load bot conversation and existing teacher conversations from server
            loadParentConversations();
        });
    }
    
    function loadFAQs() {
        return fetch('/information/api/chat/get-faqs/', {
            headers: {
                'X-CSRFToken': chatState.csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            // Clear and populate FAQ_DATA
            FAQ_DATA.length = 0;
            data.faqs.forEach(faq => {
                FAQ_DATA.push(faq);
            });
            FAQ_LOADED = true;
            console.log('FAQs loaded:', FAQ_DATA.length);
        })
        .catch(error => {
            console.error('Error loading FAQs:', error);
            FAQ_LOADED = true; // Continue even if FAQs fail to load
        });
    }

    function loadParentConversations() {
        // Fetch existing conversations from Django backend
        fetch('/information/api/chat/conversations/', {
            headers: {
                'X-CSRFToken': chatState.csrfToken
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Parent conversations loaded:', data);
            
            // Add bot conversation first
            const botConv = {
                id: 'bot',
                name: 'KinderCare Assistant',
                type: 'bot',
                avatar: '🤖',
                unread: 0,
                lastMessage: 'Hello! How can I help you today?',
                lastTime: getCurrentTime(),
                messages: [{
                    id: 1,
                    sender: 'bot',
                    text: 'Hello! 👋 Welcome to KinderCare. How can I assist you today?',
                    time: getCurrentTime(),
                    showFAQ: true
                }]
            };
            
            // Map teacher conversations from API
            const teacherConvs = data.conversations.map(conv => ({
                id: conv.id,
                name: conv.teacher_name,
                type: 'teacher',
                avatar: '👨‍🏫',
                section: conv.section,
                unread: conv.unread_count || 0,
                lastMessage: conv.last_message || 'Start conversation',
                lastTime: conv.last_message_time || getCurrentTime(),
                messages: []
            }));
            
            // Combine bot + teacher conversations
            chatState.conversations = [botConv, ...teacherConvs];
            
            renderConversationList();
            updateUnreadBadge();
        })
        .catch(error => {
            console.error('Error loading parent conversations:', error);
            // If API fails, at least show the bot
            chatState.conversations = [{
                id: 'bot',
                name: 'KinderCare Assistant',
                type: 'bot',
                avatar: '🤖',
                unread: 0,
                lastMessage: 'Hello! How can I help you today?',
                lastTime: getCurrentTime(),
                messages: [{
                    id: 1,
                    sender: 'bot',
                    text: 'Hello! 👋 Welcome to KinderCare. How can I assist you today?',
                    time: getCurrentTime(),
                    showFAQ: true
                }]
            }];
            renderConversationList();
        });
    }

    function loadTeacherConversations() {
        // Load parent conversations for teachers
        fetch('/information/api/chat/teacher-conversations/', {
            headers: {
                'X-CSRFToken': chatState.csrfToken
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Teacher conversations loaded:', data);
            chatState.conversations = data.conversations.map(conv => ({
                id: conv.id,
                name: conv.parent_name,
                type: 'parent',
                avatar: '👤',
                childName: conv.child_name,
                unread: conv.unread_count || 0,
                lastMessage: conv.last_message || 'No messages',
                lastTime: conv.last_message_time || getCurrentTime(),
                messages: []
            }));
            renderConversationList();
            updateUnreadBadge();
        })
        .catch(error => {
            console.error('Error loading teacher conversations:', error);
        });
    }

    // ==================== HTML GENERATION ====================
    function createChatHTML() {
        const container = document.getElementById('kindercare-chat');
        if (!container) return;

        container.innerHTML = `
            <button class="kc-chat-button" id="kcChatButton">
                💬
                <span class="kc-unread-badge" id="kcUnreadBadge" style="display: none;">0</span>
            </button>

            <div class="kc-chat-window" id="kcChatWindow">
                <div class="kc-chat-header">
                    <div class="kc-chat-header-left">
                        <button class="kc-back-btn" id="kcBackBtn" style="display: none;">←</button>
                        <span id="kcHeaderTitle">Messages</span>
                    </div>
                    <button class="kc-close-btn" id="kcCloseBtn">×</button>
                </div>

                <div class="kc-conversation-list" id="kcConversationList"></div>

                <div class="kc-messages-container" id="kcMessagesContainer"></div>

                <div class="kc-message-input-container" id="kcMessageInputContainer">
                    <input type="file" id="kcFileInput" accept="image/*,video/*" style="display: none;" onchange="window.kcHandleFileSelect(event)">
                    <button class="kc-attach-btn" id="kcAttachBtn" onclick="document.getElementById('kcFileInput').click()">📎</button>
                    <input type="text" class="kc-message-input" id="kcMessageInput" placeholder="Type a message...">
                    <button class="kc-send-btn" id="kcSendBtn">➤</button>
                </div>
            </div>
        `;
    }

    // ==================== EVENT LISTENERS ====================
    function attachEventListeners() {
        document.getElementById('kcChatButton').addEventListener('click', openChat);
        document.getElementById('kcCloseBtn').addEventListener('click', closeChat);
        document.getElementById('kcBackBtn').addEventListener('click', backToList);
        document.getElementById('kcSendBtn').addEventListener('click', sendMessage);
        
        const input = document.getElementById('kcMessageInput');
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
    }

    // ==================== CHAT CONTROLS ====================
    function openChat() {
        chatState.isOpen = true;
        document.getElementById('kcChatWindow').classList.add('kc-open');
        document.getElementById('kcChatButton').style.display = 'none';
        renderConversationList();
    }

    function closeChat() {
        chatState.isOpen = false;
        document.getElementById('kcChatWindow').classList.remove('kc-open');
        document.getElementById('kcChatButton').style.display = 'flex';
        backToList();
    }

    function backToList() {
        // Clear message refresh interval
        if (chatState.messageRefreshInterval) {
            clearInterval(chatState.messageRefreshInterval);
            chatState.messageRefreshInterval = null;
        }
        
        chatState.activeConvId = null;
        document.getElementById('kcConversationList').style.display = 'block';
        document.getElementById('kcMessagesContainer').classList.remove('kc-active');
        document.getElementById('kcMessageInputContainer').classList.remove('kc-active');
        document.getElementById('kcBackBtn').style.display = 'none';
        document.getElementById('kcHeaderTitle').textContent = 'Messages';
        
        // Reload conversation list to get latest
        if (chatState.userRole === 'parent') {
            loadParentConversations();
        } else if (chatState.userRole === 'teacher') {
            loadTeacherConversations();
        }
    }

    // ==================== RENDERING ====================
    function renderConversationList() {
        const listEl = document.getElementById('kcConversationList');
        
        if (chatState.conversations.length === 0) {
            listEl.innerHTML = `
                <div class="kc-empty-state">
                    <div style="font-size: 48px; margin-bottom: 10px;">💬</div>
                    <div>No conversations yet</div>
                </div>
            `;
            return;
        }

        listEl.innerHTML = chatState.conversations.map(conv => `
            <div class="kc-conversation-item" onclick="window.kcOpenConversation('${conv.id}')">
                <div class="kc-conv-avatar">${conv.avatar}</div>
                <div class="kc-conv-info">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                        <div class="kc-conv-name">${conv.name}</div>
                        <div class="kc-conv-time">${conv.lastTime}</div>
                    </div>
                    <div class="kc-conv-last-message">${conv.lastMessage}</div>
                </div>
                ${conv.unread > 0 ? `<div class="kc-conv-unread">${conv.unread}</div>` : ''}
            </div>
        `).join('');
    }

    function openConversation(convId) {
        chatState.activeConvId = convId;
        const conv = chatState.conversations.find(c => c.id === convId);
        
        // Mark as read
        conv.unread = 0;
        updateUnreadBadge();
        
        // Load messages if not loaded yet
        if (conv.type !== 'bot' && conv.messages.length === 0) {
            loadConversationMessages(convId);
        }
        
        document.getElementById('kcConversationList').style.display = 'none';
        document.getElementById('kcMessagesContainer').classList.add('kc-active');
        document.getElementById('kcMessageInputContainer').classList.add('kc-active');
        document.getElementById('kcBackBtn').style.display = 'block';
        
        let headerText = conv.name;
        let headerHTML = `<div style="display: flex; align-items: center; gap: 8px; flex: 1;">`;
        
        if (conv.type === 'teacher') {
            headerHTML += `
                <span>${conv.name} - ${conv.section}</span>
                <button onclick="window.kcViewProfile('teacher', '${conv.id}')" 
                        class="kc-view-profile-btn" title="View Profile">
                    ℹ️
                </button>
            `;
        } else if (conv.type === 'parent') {
            headerHTML += `
                <span>${conv.name}</span>
                <button onclick="window.kcViewProfile('parent', '${conv.id}')" 
                        class="kc-view-profile-btn" title="View Profile">
                    ℹ️
                </button>
            `;
        } else {
            headerHTML += `<span>${conv.name}</span>`;
        }
        
        headerHTML += `</div>`;
        document.getElementById('kcHeaderTitle').innerHTML = headerHTML;
        
        renderMessages();
        
        // Auto-refresh messages every 10 seconds for active conversation
        if (chatState.messageRefreshInterval) {
            clearInterval(chatState.messageRefreshInterval);
        }
        
        if (conv.type !== 'bot') {
            chatState.messageRefreshInterval = setInterval(() => {
                if (chatState.activeConvId === convId && chatState.isOpen) {
                    loadConversationMessages(convId, true); // true = silent refresh
                }
            }, 10000);
        }
    }

    function loadConversationMessages(convId, silent = false) {
        fetch(`/information/api/chat/conversation/${convId}/messages/`, {
            headers: {
                'X-CSRFToken': chatState.csrfToken
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Messages loaded:', data);
            const conv = chatState.conversations.find(c => c.id === convId);
            if (conv) {
                const oldLength = conv.messages.length;
                conv.messages = data.messages.map(msg => {
                    const message = {
                        id: msg.id,
                        sender: msg.sender_role,
                        text: msg.message,
                        time: msg.timestamp
                    };
                    
                    // Add attachment if present
                    if (msg.attachment_url) {
                        message.attachment = {
                            type: msg.attachment_type || 'image',
                            url: msg.attachment_url
                        };
                    }
                    
                    return message;
                });
                
                // Only render if not silent or if new messages arrived
                if (!silent || conv.messages.length !== oldLength) {
                    renderMessages();
                }
            }
        })
        .catch(error => {
            console.error('Error loading messages:', error);
        });
    }

    function renderMessages() {
        const conv = chatState.conversations.find(c => c.id === chatState.activeConvId);
        const container = document.getElementById('kcMessagesContainer');
        
        container.innerHTML = conv.messages.map((msg, index) => {
            // Determine if this is a sent or received message
            const isSentByMe = (
                (chatState.userRole === 'parent' && msg.sender === 'parent') ||
                (chatState.userRole === 'teacher' && msg.sender === 'teacher') ||
                msg.sender === 'bot' // Bot messages always on left
            );
            
            const messageClass = isSentByMe && msg.sender !== 'bot' ? 'kc-sent' : 'kc-received';
            
            // Check if we should show avatar (first message or sender changed)
            const prevMsg = index > 0 ? conv.messages[index - 1] : null;
            const showAvatar = !prevMsg || prevMsg.sender !== msg.sender;
            
            // Get avatar
            let avatar = '';
            if (msg.sender === 'bot') {
                avatar = '🤖';
            } else if (msg.sender === 'parent') {
                avatar = '👤';
            } else if (msg.sender === 'teacher') {
                avatar = '👨‍🏫';
            } else if (msg.sender === 'system') {
                avatar = 'ℹ️';
            }
            
            let html = `<div class="kc-message ${messageClass}">`;
            
            // Add avatar for received messages
            if (!isSentByMe || msg.sender === 'bot') {
                if (showAvatar) {
                    html += `<div class="kc-message-avatar">${avatar}</div>`;
                } else {
                    html += `<div class="kc-message-avatar-spacer"></div>`;
                }
            }
            
            html += `<div class="kc-message-content">`;
            
            if (msg.sender === 'system') {
                html += `<div class="kc-message-bubble kc-system">${msg.text}</div>`;
            } else {
                html += `<div class="kc-message-bubble">${msg.text}</div>`;
                
                // Show attachment if present
                if (msg.attachment) {
                    if (msg.attachment.type === 'image') {
                        html += `
                            <div class="kc-attachment">
                                <img src="${msg.attachment.url}" alt="Image" class="kc-attachment-image" onclick="window.open('${msg.attachment.url}', '_blank')">
                            </div>
                        `;
                    } else if (msg.attachment.type === 'video') {
                        html += `
                            <div class="kc-attachment">
                                <video controls class="kc-attachment-video">
                                    <source src="${msg.attachment.url}" type="video/mp4">
                                    Your browser does not support the video tag.
                                </video>
                            </div>
                        `;
                    }
                }
            }
            
            html += `<div class="kc-message-time">${msg.time}</div>`;
            
            if (msg.showFAQ) {
                html += `<div class="kc-faq-container">`;
                html += `<button class="kc-faq-toggle" onclick="window.kcToggleFAQ(this)">📚 Choose FAQ</button>`;
                html += `<div class="kc-faq-options" style="display: none;"></div>`;
                html += `</div>`;
            }
            
            if (msg.showTeacherPrompt) {
                html += `
                    <div class="kc-teacher-prompt">
                        <div class="kc-teacher-prompt-buttons">
                            <button class="kc-btn-yes" onclick="window.kcShowTeacherSelect()">Yes, please</button>
                            <button class="kc-btn-no" onclick="window.kcDeclineTeacher()">No, thanks</button>
                        </div>
                    </div>
                `;
            }
            
            if (msg.showTeacherSelect) {
                html += '<div class="kc-teacher-select" id="kcTeacherSelect"></div>';
            }
            
            html += `</div>`; // close message-content
            html += `</div>`; // close message
            
            return html;
        }).join('');
        
        // Add typing indicator if present
        if (conv.isTyping) {
            container.innerHTML += `
                <div class="kc-message kc-received">
                    <div class="kc-message-avatar">🤖</div>
                    <div class="kc-message-content">
                        <div class="kc-typing-indicator">
                            <span></span>
                            <span></span>
                            <span></span>
                        </div>
                    </div>
                </div>
            `;
        }
        
        // Load teachers if needed
        if (conv.messages.some(m => m.showTeacherSelect)) {
            loadTeachers();
        }
        
        container.scrollTop = container.scrollHeight;
    }
    
    function renderFAQOptions() {
        // This function is no longer used - FAQs are rendered on-demand when button is clicked
        // Keeping for backwards compatibility
        return;
    }

    function loadTeachers() {
        fetch('/information/api/chat/available-teachers/', {
            headers: {
                'X-CSRFToken': chatState.csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            const selectEl = document.getElementById('kcTeacherSelect');
            if (selectEl) {
                selectEl.innerHTML = data.teachers.map(teacher => `
                    <div class="kc-teacher-option" onclick="window.kcSelectTeacher(${teacher.id}, '${teacher.name}', '${teacher.section}')">
                        <div class="kc-teacher-name">${teacher.name}</div>
                        <div class="kc-teacher-section">${teacher.section}</div>
                    </div>
                `).join('');
            }
        })
        .catch(error => {
            console.log('Could not load teachers:', error);
        });
    }

    function updateUnreadBadge() {
        const total = chatState.conversations.reduce((sum, conv) => sum + conv.unread, 0);
        const badge = document.getElementById('kcUnreadBadge');
        
        if (total > 0) {
            badge.textContent = total;
            badge.style.display = 'flex';
        } else {
            badge.style.display = 'none';
        }
    }

    // ==================== MESSAGE HANDLING ====================
    function sendMessage() {
        const input = document.getElementById('kcMessageInput');
        const text = input.value.trim();
        
        if (!text && !chatState.selectedFile) return;
        
        const conv = chatState.conversations.find(c => c.id === chatState.activeConvId);
        
        const newMessage = {
            id: Date.now(),
            sender: chatState.userRole,
            text: text || '📎 Attachment',
            time: getCurrentTime()
        };
        
        // If file is selected, add attachment info
        if (chatState.selectedFile) {
            newMessage.attachment = {
                type: chatState.selectedFile.type.startsWith('image/') ? 'image' : 'video',
                url: URL.createObjectURL(chatState.selectedFile),
                file: chatState.selectedFile
            };
        }
        
        conv.messages.push(newMessage);
        conv.lastMessage = text || '📎 Attachment';
        conv.lastTime = getCurrentTime();
        
        input.value = '';
        chatState.selectedFile = null;
        document.getElementById('kcFileInput').value = '';
        renderMessages();
        
        // Handle bot conversation
        if (conv.type === 'bot') {
            // Show typing indicator
            conv.isTyping = true;
            renderMessages();
            
            // Search for bot response in database
            searchBotResponse(text, conv);
        } else {
            // Send to server
            saveMessage(chatState.activeConvId, text, newMessage.attachment?.file);
        }
    }
    
    function searchBotResponse(message, conv) {
        fetch('/information/api/chat/bot-search/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': chatState.csrfToken
            },
            body: JSON.stringify({
                message: message
            })
        })
        .then(response => response.json())
        .then(data => {
            setTimeout(() => {
                conv.isTyping = false;
                
                if (data.found) {
                    // Bot found a matching response
                    conv.messages.push({
                        id: Date.now(),
                        sender: 'bot',
                        text: data.response,
                        time: getCurrentTime(),
                        showFAQ: true
                    });
                } else {
                    // No match found, offer teacher connection
                    conv.messages.push({
                        id: Date.now(),
                        sender: 'bot',
                        text: 'It looks like you have a different concern. Would you like to speak with one of our teachers?',
                        time: getCurrentTime(),
                        showTeacherPrompt: true
                    });
                }
                
                renderMessages();
            }, 1800);
        })
        .catch(error => {
            console.error('Error searching bot response:', error);
            // Fallback to teacher prompt on error
            setTimeout(() => {
                conv.isTyping = false;
                conv.messages.push({
                    id: Date.now(),
                    sender: 'bot',
                    text: 'It looks like you have a different concern. Would you like to speak with one of our teachers?',
                    time: getCurrentTime(),
                    showTeacherPrompt: true
                });
                renderMessages();
            }, 1800);
        });
    }

    function saveMessage(conversationId, messageText, attachmentFile) {
        const formData = new FormData();
        formData.append('message', messageText || '');
        
        if (attachmentFile) {
            formData.append('attachment', attachmentFile);
        }
        
        fetch(`/information/api/chat/conversation/${conversationId}/send/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': chatState.csrfToken
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            console.log('Message sent successfully');
        })
        .catch(error => {
            console.log('Could not send message:', error);
        });
    }

    function selectFAQ(faqId) {
        const faq = FAQ_DATA.find(f => f.id === faqId);
        if (!faq) {
            console.error('FAQ not found:', faqId);
            return;
        }
        
        const conv = chatState.conversations.find(c => c.id === chatState.activeConvId);
        
        conv.messages.push({
            id: Date.now(),
            sender: chatState.userRole,
            text: faq.question,
            time: getCurrentTime()
        });
        
        renderMessages();
        
        // Show typing indicator
        conv.isTyping = true;
        renderMessages();
        
        // Simulate bot thinking and typing (1-2 seconds)
        setTimeout(() => {
            conv.isTyping = false;
            conv.messages.push({
                id: Date.now(),
                sender: 'bot',
                text: faq.answer,
                time: getCurrentTime(),
                showFAQ: true
            });
            conv.lastMessage = faq.answer;
            conv.lastTime = getCurrentTime();
            renderMessages();
        }, 1500);
    }

    function showTeacherSelect() {
        const conv = chatState.conversations.find(c => c.id === chatState.activeConvId);
        
        conv.messages.push({
            id: Date.now(),
            sender: 'bot',
            text: 'Great! Please select a teacher to connect with:',
            time: getCurrentTime(),
            showTeacherSelect: true
        });
        
        renderMessages();
    }

    function declineTeacher() {
        const conv = chatState.conversations.find(c => c.id === chatState.activeConvId);
        
        // Show typing indicator
        conv.isTyping = true;
        renderMessages();
        
        setTimeout(() => {
            conv.isTyping = false;
            conv.messages.push({
                id: Date.now(),
                sender: 'bot',
                text: 'No problem! Feel free to select any question below or type your message.',
                time: getCurrentTime(),
                showFAQ: true
            });
            renderMessages();
        }, 1200);
    }

    function selectTeacher(teacherId, teacherName, section) {
        // Create new conversation with teacher via API
        fetch('/information/api/chat/create-conversation/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': chatState.csrfToken
            },
            body: JSON.stringify({
                teacher_id: teacherId
            })
        })
        .then(response => response.json())
        .then(data => {
            const newConv = {
                id: data.conversation_id,
                name: teacherName,
                type: 'teacher',
                avatar: '👨‍🏫',
                section: section,
                unread: 0,
                lastMessage: 'Conversation started',
                lastTime: getCurrentTime(),
                messages: [{
                    id: 1,
                    sender: 'system',
                    text: `You are now connected with ${teacherName}. Feel free to ask your questions.`,
                    time: getCurrentTime()
                }]
            };
            
            chatState.conversations.push(newConv);
            chatState.activeConvId = newConv.id;
            openConversation(newConv.id);
        })
        .catch(error => {
            console.log('Could not create conversation:', error);
        });
    }

    // ==================== EXPOSE TO WINDOW ====================
    window.kcOpenConversation = openConversation;
    window.kcSelectFAQ = selectFAQ;
    window.kcShowTeacherSelect = showTeacherSelect;
    window.kcDeclineTeacher = declineTeacher;
    window.kcSelectTeacher = selectTeacher;
    window.kcHandleFileSelect = function(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        // Validate file type
        const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'video/mp4', 'video/quicktime'];
        if (!validTypes.includes(file.type)) {
            alert('Please select an image (JPG, PNG, GIF) or video (MP4, MOV) file.');
            event.target.value = '';
            return;
        }
        
        // Validate file size (max 10MB)
        const maxSize = 10 * 1024 * 1024; // 10MB
        if (file.size > maxSize) {
            alert('File size must be less than 10MB.');
            event.target.value = '';
            return;
        }
        
        chatState.selectedFile = file;
        
        // Show file preview or name
        const input = document.getElementById('kcMessageInput');
        input.placeholder = `📎 ${file.name} - Click send to attach`;
    };
    window.kcToggleFAQ = function(button) {
        const faqOptions = button.nextElementSibling;
        
        if (faqOptions.style.display === 'none') {
            // Render FAQs if not already rendered
            if (!faqOptions.innerHTML || faqOptions.innerHTML.trim() === '') {
                renderFAQOptionsInContainer(faqOptions);
            }
            faqOptions.style.display = 'block';
            button.textContent = '❌ Close FAQ';
        } else {
            faqOptions.style.display = 'none';
            button.textContent = '📚 Choose FAQ';
        }
    };
    
    function renderFAQOptionsInContainer(container) {
        if (!FAQ_LOADED || FAQ_DATA.length === 0) {
            container.innerHTML = '<div style="padding: 10px; text-align: center; color: #65676b;">Loading FAQs...</div>';
            return;
        }
        
        // Group FAQs by category
        const categories = {
            'enrollment': { title: '📚 Enrollment & Fees', faqs: [] },
            'schedule': { title: '🕐 Schedules & Hours', faqs: [] },
            'attendance': { title: '📅 Attendance', faqs: [] },
            'health': { title: '🏥 Health & Safety', faqs: [] },
            'records': { title: '📊 Progress & Records', faqs: [] },
            'contact': { title: '📞 Contact & Teachers', faqs: [] },
            'general': { title: '🎒 General Info', faqs: [] }
        };
        
        // Categorize FAQs (skip greetings and help)
        FAQ_DATA.forEach(faq => {
            if (faq.category !== 'greeting' && faq.category !== 'faq') {
                if (categories[faq.category]) {
                    categories[faq.category].faqs.push(faq);
                }
            }
        });
        
        // Build HTML
        let html = '';
        for (const [key, cat] of Object.entries(categories)) {
            if (cat.faqs.length > 0) {
                html += `<details class="kc-faq-category">`;
                html += `<summary>${cat.title}</summary>`;
                cat.faqs.forEach(faq => {
                    html += `<button class="kc-faq-button" onclick="window.kcSelectFAQ(${faq.id})">${faq.question}</button>`;
                });
                html += `</details>`;
            }
        }
        
        container.innerHTML = html;
    }
    window.kcViewProfile = function(type, convId) {
        const conv = chatState.conversations.find(c => c.id === convId);
        if (!conv) return;
        
        // Create profile modal
        const modal = document.createElement('div');
        modal.className = 'kc-profile-modal';
        modal.innerHTML = `
            <div class="kc-profile-overlay" onclick="this.parentElement.remove()"></div>
            <div class="kc-profile-content">
                <div class="kc-profile-header">
                    <h3>${conv.name}</h3>
                    <button onclick="this.closest('.kc-profile-modal').remove()" class="kc-profile-close">×</button>
                </div>
                <div class="kc-profile-body">
                    <div class="kc-profile-loading">Loading profile...</div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        
        // Fetch profile data
        const url = type === 'parent' 
            ? `/information/api/chat/parent-profile/${convId}/`
            : `/information/api/chat/teacher-profile/${convId}/`;
        
        fetch(url, {
            headers: {
                'X-CSRFToken': chatState.csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            const body = modal.querySelector('.kc-profile-body');
            
            if (type === 'parent') {
                body.innerHTML = `
                    <div class="kc-profile-avatar">${conv.avatar}</div>
                    <div class="kc-profile-info">
                        <div class="kc-profile-item">
                            <strong>Name:</strong> ${data.name}
                        </div>
                        <div class="kc-profile-item">
                            <strong>Email:</strong> ${data.email}
                        </div>
                        <div class="kc-profile-item">
                            <strong>Contact:</strong> ${data.contact}
                        </div>
                        <div class="kc-profile-item">
                            <strong>Child:</strong> ${data.child_name || 'N/A'}
                        </div>
                        ${data.address ? `
                        <div class="kc-profile-item">
                            <strong>Address:</strong> ${data.address}
                        </div>
                        ` : ''}
                    </div>
                `;
            } else {
                body.innerHTML = `
                    <div class="kc-profile-avatar">${conv.avatar}</div>
                    <div class="kc-profile-info">
                        <div class="kc-profile-item">
                            <strong>Name:</strong> ${data.name}
                        </div>
                        <div class="kc-profile-item">
                            <strong>Department:</strong> ${data.department}
                        </div>
                        <div class="kc-profile-item">
                            <strong>Section:</strong> ${data.section}
                        </div>
                        <div class="kc-profile-item">
                            <strong>Email:</strong> ${data.email}
                        </div>
                        ${data.contact ? `
                        <div class="kc-profile-item">
                            <strong>Contact:</strong> ${data.contact}
                        </div>
                        ` : ''}
                    </div>
                `;
            }
        })
        .catch(error => {
            const body = modal.querySelector('.kc-profile-body');
            body.innerHTML = '<div class="kc-profile-error">Could not load profile</div>';
        });
    };

    // ==================== INITIALIZE ON LOAD ====================
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initChat);
    } else {
        initChat();
    }

})();