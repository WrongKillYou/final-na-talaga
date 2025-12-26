// chatbot.js - KinderCare Messenger Chat System
// This should be placed in your static/js/ folder

(function() {
    'use strict';

    // ==================== CONFIGURATION ====================
    const FAQ_DATA = [
        {
            id: 1,
            question: 'What are your enrollment requirements?',
            answer: 'To enroll your child, you need: Birth Certificate, Immunization Records, 2x2 ID Photos (4pcs), Health Certificate, and filled-out enrollment form. Please visit our office during enrollment period.'
        },
        {
            id: 2,
            question: 'What are your class schedules?',
            answer: 'Our kindergarten classes run from 8:00 AM to 12:00 PM, Monday to Friday. Extended care is available until 3:00 PM for working parents.'
        },
        {
            id: 3,
            question: 'What is your attendance policy?',
            answer: 'Regular attendance is important for your child\'s development. Please notify us if your child will be absent. Excused absences require a parent note or medical certificate.'
        },
        {
            id: 4,
            question: 'What should I do if my child is sick?',
            answer: 'Please keep your child at home if they have fever, cough, or any contagious illness. They may return 24 hours after symptoms subside. Always inform the teacher about any medical conditions.'
        },
        {
            id: 5,
            question: 'How can I contact the school?',
            answer: 'You can reach us at: Phone: (074) 424-xxxx, Email: kindercare@school.edu.ph, Office Hours: Monday-Friday, 7:30 AM - 4:30 PM'
        },
        {
            id: 6,
            question: 'How can I view my child\'s progress?',
            answer: 'You can view your child\'s competency records and attendance through your parent dashboard. Reports are updated quarterly and you\'ll receive notifications when new assessments are posted.'
        },
        {
            id: 7,
            question: 'What items should my child bring to school?',
            answer: 'Your child should bring: Clean uniform, Snack and water bottle, Extra clothes, Handkerchief/tissue, School bag. Please label all items with your child\'s name.'
        },
        {
            id: 8,
            question: 'What is your payment schedule?',
            answer: 'Tuition fees can be paid monthly or quarterly. Monthly payments are due on the 5th of each month. We accept cash, check, and bank transfer. Please see the accounting office for payment arrangements.'
        },
        {
            id: 9,
            question: 'What is your cancellation policy for classes?',
            answer: 'Classes are cancelled during typhoons, holidays, and emergencies. We will send announcements through the parent portal and SMS. Make-up classes will be scheduled as needed.'
        },
        {
            id: 10,
            question: 'How do I update my contact information?',
            answer: 'You can update your contact information through your Profile page or visit the school office. It\'s important to keep your contact details current for emergency situations.'
        }
    ];

    // ==================== STATE MANAGEMENT ====================
    let chatState = {
        isOpen: false,
        activeConvId: null,
        conversations: [],
        userRole: null,
        userName: null,
        csrfToken: null
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
        } else if (chatState.userRole === 'teacher') {
            loadTeacherConversations();
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
        
        // Also load existing teacher conversations from API
        loadParentConversations();
    }

    function loadParentConversations() {
        // This would fetch existing conversations from your Django backend
        fetch('/api/chat/conversations/', {
            headers: {
                'X-CSRFToken': chatState.csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            // Add teacher conversations to the list
            data.forEach(conv => {
                if (!chatState.conversations.find(c => c.id === conv.id)) {
                    chatState.conversations.push({
                        id: conv.id,
                        name: conv.teacher_name,
                        type: 'teacher',
                        avatar: '👨‍🏫',
                        section: conv.section,
                        unread: conv.unread_count || 0,
                        lastMessage: conv.last_message || 'Start conversation',
                        lastTime: conv.last_message_time || getCurrentTime(),
                        messages: []
                    });
                }
            });
            renderConversationList();
            updateUnreadBadge();
        })
        .catch(error => {
            console.log('Could not load conversations:', error);
            renderConversationList();
        });
    }

    function loadTeacherConversations() {
        // Load parent conversations for teachers
        fetch('/api/chat/teacher-conversations/', {
            headers: {
                'X-CSRFToken': chatState.csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            chatState.conversations = data.map(conv => ({
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
            console.log('Could not load conversations:', error);
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
        chatState.activeConvId = null;
        document.getElementById('kcConversationList').style.display = 'block';
        document.getElementById('kcMessagesContainer').classList.remove('kc-active');
        document.getElementById('kcMessageInputContainer').classList.remove('kc-active');
        document.getElementById('kcBackBtn').style.display = 'none';
        document.getElementById('kcHeaderTitle').textContent = 'Messages';
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
                    ${conv.type === 'parent' ? `<div style="font-size: 12px; color: #999;">Child: ${conv.childName}</div>` : ''}
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
        if (conv.type === 'teacher') {
            headerText += ` - ${conv.section}`;
        } else if (conv.type === 'parent') {
            headerText += ` (${conv.childName})`;
        }
        document.getElementById('kcHeaderTitle').textContent = headerText;
        
        renderMessages();
    }

    function loadConversationMessages(convId) {
        fetch(`/api/chat/conversation/${convId}/messages/`, {
            headers: {
                'X-CSRFToken': chatState.csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            const conv = chatState.conversations.find(c => c.id === convId);
            if (conv) {
                conv.messages = data.messages.map(msg => ({
                    id: msg.id,
                    sender: msg.sender_role,
                    text: msg.message,
                    time: msg.timestamp
                }));
                renderMessages();
            }
        })
        .catch(error => {
            console.log('Could not load messages:', error);
        });
    }

    function renderMessages() {
        const conv = chatState.conversations.find(c => c.id === chatState.activeConvId);
        const container = document.getElementById('kcMessagesContainer');
        
        container.innerHTML = conv.messages.map(msg => {
            let html = `<div class="kc-message"><div class="kc-message-sender kc-${msg.sender}">`;
            
            html += `<div class="kc-message-bubble">${msg.text}</div>`;
            html += `</div><div class="kc-message-time">${msg.time}</div>`;
            
            if (msg.showFAQ) {
                html += '<div class="kc-faq-options">';
                FAQ_DATA.forEach(faq => {
                    html += `<button class="kc-faq-button" onclick="window.kcSelectFAQ(${faq.id})">${faq.question}</button>`;
                });
                html += '</div>';
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
            
            html += '</div>';
            return html;
        }).join('');
        
        // Load teachers if needed
        if (conv.messages.some(m => m.showTeacherSelect)) {
            loadTeachers();
        }
        
        container.scrollTop = container.scrollHeight;
    }

    function loadTeachers() {
        fetch('/api/chat/available-teachers/', {
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
        
        if (!text) return;
        
        const conv = chatState.conversations.find(c => c.id === chatState.activeConvId);
        
        const newMessage = {
            id: Date.now(),
            sender: chatState.userRole,
            text: text,
            time: getCurrentTime()
        };
        
        conv.messages.push(newMessage);
        conv.lastMessage = text;
        conv.lastTime = getCurrentTime();
        
        input.value = '';
        renderMessages();
        
        // Handle bot conversation
        if (conv.type === 'bot') {
            setTimeout(() => {
                conv.messages.push({
                    id: Date.now(),
                    sender: 'bot',
                    text: 'It looks like you have a different concern. Would you like to speak with one of our teachers?',
                    time: getCurrentTime(),
                    showTeacherPrompt: true
                });
                renderMessages();
            }, 1000);
        } else {
            // Send to server
            saveMessage(chatState.activeConvId, text);
        }
    }

    function saveMessage(conversationId, messageText) {
        fetch(`/api/chat/conversation/${conversationId}/send/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': chatState.csrfToken
            },
            body: JSON.stringify({
                message: messageText
            })
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
        const conv = chatState.conversations.find(c => c.id === chatState.activeConvId);
        
        conv.messages.push({
            id: Date.now(),
            sender: chatState.userRole,
            text: faq.question,
            time: getCurrentTime()
        });
        
        setTimeout(() => {
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
        }, 500);
        
        renderMessages();
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
        
        conv.messages.push({
            id: Date.now(),
            sender: 'bot',
            text: 'No problem! Feel free to select any question below or type your message.',
            time: getCurrentTime(),
            showFAQ: true
        });
        
        renderMessages();
    }

    function selectTeacher(teacherId, teacherName, section) {
        // Create new conversation with teacher via API
        fetch('/api/chat/create-conversation/', {
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

    // ==================== INITIALIZE ON LOAD ====================
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initChat);
    } else {
        initChat();
    }

})();