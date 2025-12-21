function loadNavMessages() {
    fetch('/information/api/chat/recent-conversations/')
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('navMessagesContainer');
            const badge = document.getElementById('unreadBadge');
            
            // Update unread badge
            if (data.unread_count > 0) {
                badge.textContent = data.unread_count;
                badge.style.display = 'inline-block';
            } else {
                badge.style.display = 'none';
            }
            
            // Clear loading spinner
            container.innerHTML = '';
            
            if (data.conversations.length === 0) {
                container.innerHTML = `
                    <li class="text-center py-3 text-muted">
                        <i class="bi bi-inbox" style="font-size: 2rem;"></i>
                        <p class="mb-0 mt-2">No messages yet</p>
                    </li>
                `;
                return;
            }
            
            // Display conversations
            data.conversations.forEach(conv => {
                const hasUnread = conv.unread_count > 0;
                const item = document.createElement('li');
                
                item.innerHTML = `
                    <a class="dropdown-item ${hasUnread ? 'bg-light' : ''}" 
                       href="/information/chat/conversation/${conv.id}/">
                        <div class="d-flex align-items-start">
                            <div class="me-2">
                                <i class="bi bi-person-circle text-primary" style="font-size: 1.5rem;"></i>
                            </div>
                            <div class="flex-grow-1">
                                <div class="d-flex justify-content-between align-items-start">
                                    <strong class="text-dark">${conv.teacher_name || 'Waiting for teacher'}</strong>
                                    ${hasUnread ? '<span class="badge bg-danger rounded-pill">New</span>' : ''}
                                </div>
                                <small class="text-muted d-block">${conv.subject}</small>
                                <small class="text-muted">${conv.last_message_preview}</small>
                                <small class="text-muted d-block">
                                    <i class="bi bi-clock"></i> ${conv.time_ago}
                                </small>
                            </div>
                        </div>
                    </a>
                `;
                
                container.appendChild(item);
            });
        })
        .catch(error => {
            console.error('Error loading messages:', error);
            document.getElementById('navMessagesContainer').innerHTML = `
                <li class="text-center py-3 text-danger">
                    <small>Error loading messages</small>
                </li>
            `;
        });
}

// Load messages on page load
document.addEventListener('DOMContentLoaded', function() {
    loadNavMessages();
    
    // Refresh every 30 seconds
    setInterval(loadNavMessages, 30000);
});