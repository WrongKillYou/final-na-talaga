from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Max, Count
from django.utils import timezone
from datetime import timedelta
from information.forms import AnnouncementForm
from users.decorators import teacher_required, parent_required
from users.models import User
from .models import Event, Announcement, ChatRoom, ChatRoomMessage, ConversationMessage, Notification, BotMessage, ChatConversation

# ========================================
# Events
# ========================================

@login_required
def event_list(request):
    """List all upcoming events"""
    from datetime import date
    
    events = Event.objects.filter(
        is_active=True,
        start_date__gte=date.today()
    ).order_by('start_date')
    
    context = {
        'events': events,
    }
    return render(request, 'information/event_list.html', context)


@login_required
def event_detail(request, event_id):
    """View event details"""
    event = get_object_or_404(Event, id=event_id)
    
    context = {
        'event': event,
    }
    return render(request, 'information/event_detail.html', context)


@login_required
@teacher_required
def create_event(request):
    """Create new event (teachers only)"""
    teacher = request.user.teacher_profile
    
    if request.method == 'POST':
        # Handle event creation
        messages.success(request, 'Event created successfully!')
        return redirect('information:event_list')
    
    context = {
        'teacher': teacher,
    }
    return render(request, 'information/create_event.html', context)


@login_required
@teacher_required
def edit_event(request, event_id):
    """Edit event"""
    teacher = request.user.teacher_profile
    event = get_object_or_404(Event, id=event_id, created_by=teacher)
    
    if request.method == 'POST':
        # Handle event editing
        messages.success(request, 'Event updated successfully!')
        return redirect('information:event_detail', event_id=event_id)
    
    context = {
        'event': event,
        'teacher': teacher,
    }
    return render(request, 'information/edit_event.html', context)


@login_required
@teacher_required
def delete_event(request, event_id):
    """Delete event"""
    teacher = request.user.teacher_profile
    event = get_object_or_404(Event, id=event_id, created_by=teacher)
    
    if request.method == 'POST':
        event.delete()
        messages.success(request, 'Event deleted successfully!')
        return redirect('information:event_list')
    
    return redirect('information:event_detail', event_id=event_id)


# ========================================
# Announcements - FIXED
# ========================================

@login_required
def announcement_list(request):
    """List all announcements with filtering and search"""
    # Base queryset - get all active announcements
    announcements = Announcement.objects.filter(
        is_active=True
    ).select_related('teacher__user').order_by('-created_at')
    
    # DEBUG: Print total count
    print(f"Total announcements found: {announcements.count()}")
    for ann in announcements[:3]:  # Print first 3
        print(f"ID: {ann.id}, Title: {ann.title}, Has image: {bool(ann.image)}")
        if ann.image:
            print(f"  Image path: {ann.image.name}")
    
    # Filter by role
    if request.user.is_parent():
        announcements = announcements.filter(
            Q(target_audience='all') | Q(target_audience='parents')
        )
    elif request.user.is_teacher():
        announcements = announcements.filter(
            Q(target_audience='all') | Q(target_audience='teachers')
        )
    
    print(f"After filtering: {announcements.count()} announcements")
    
    # Apply filters from GET parameters
    filter_type = request.GET.get('filter', 'all')
    
    if filter_type == 'important':
        announcements = announcements.filter(is_important=True)
    elif filter_type == 'recent':
        seven_days_ago = timezone.now() - timedelta(days=7)
        announcements = announcements.filter(created_at__gte=seven_days_ago)
    
    # Apply search
    search_query = request.GET.get('search', '').strip()
    if search_query:
        announcements = announcements.filter(
            Q(title__icontains=search_query) | 
            Q(content__icontains=search_query)
        )
    
    print(f"Final count: {announcements.count()} announcements")
    
    context = {
        'announcements': announcements,
        'search_query': search_query,
        'filter_type': filter_type,
    }
    return render(request, 'information/announcement_list.html', context)


@login_required
def announcement_detail(request, announcement_id):
    try:
        announcement = Announcement.objects.select_related('teacher__user').get(
            pk=announcement_id
        )
        
        # Debug code - INSIDE the function
        print(f"Announcement ID: {announcement.id}")  # Use announcement.id, not Announcement.id
        if announcement.image:
            print(f"Has image: Yes")
            print(f"Image URL: {announcement.image.url}")
        else:
            print(f"Has image: No")
            
    except Announcement.DoesNotExist:
        messages.error(request, "Announcement not found.")
        return redirect('information:announcement_list')
    
    # Mark as read
    #try:
        from .models import AnnouncementView
        AnnouncementView.objects.get_or_create(
            announcement=announcement,
            user=request.user
        )
    #except ImportError:
        pass
    
    # Increment view count
    #if hasattr(announcement, 'views_count'):
        announcement.views_count = (announcement.views_count or 0) + 1
        announcement.save(update_fields=['views_count'])
    
    context = {
        'announcement': announcement,
    }
    return render(request, 'information/announcement_detail.html', context)


@login_required
@teacher_required
def edit_announcement(request, announcement_id):
    """Edit announcement"""
    teacher = request.user.teacher_profile
    announcement = get_object_or_404(Announcement, id=announcement_id, teacher=teacher)
    
    if request.method == 'POST':
        form = AnnouncementForm(request.POST, request.FILES, instance=announcement)
        if form.is_valid():
            form.save()
            messages.success(request, 'Announcement updated successfully!')
            return redirect('information:announcement_detail', announcement_id=announcement_id)
    else:
        form = AnnouncementForm(instance=announcement)
    
    context = {
        'form': form,
        'announcement': announcement,
        'teacher': teacher,
    }
    return render(request, 'information/edit_announcement.html', context)


@login_required
@teacher_required
def delete_announcement(request, announcement_id):
    """Delete announcement - FIXED"""
    teacher = request.user.teacher_profile
    announcement = get_object_or_404(Announcement, id=announcement_id, teacher=teacher)
    
    if request.method == 'POST':
        announcement.delete()
        messages.success(request, 'Announcement deleted successfully!')
        return redirect('information:announcement_list')
    
    return redirect('information:announcement_detail', announcement_id=announcement_id)


@login_required
@teacher_required
def create_announcement(request):
    """Create new announcement (teachers only)"""
    teacher = request.user.teacher_profile
    
    if request.method == 'POST':
        form = AnnouncementForm(request.POST, request.FILES)
        
        if form.is_valid():
            # Save the announcement
            announcement = form.save(commit=False)
            announcement.teacher = teacher
            
            # Handle custom fields
            announcement.is_active = form.cleaned_data.get('is_active', True)
            if hasattr(announcement, 'is_pinned'):
                announcement.is_pinned = form.cleaned_data.get('is_pinned', False)
            
            try:
                announcement.save()
                
                # Handle notifications if requested
                send_notification = form.cleaned_data.get('send_notification', False)
                
                if send_notification and announcement.is_active:
                    # Determine recipients based on target audience
                    target = announcement.target_audience.lower()
                    
                    if target == 'all':
                        recipients = User.objects.filter(is_active=True).exclude(id=request.user.id)
                    elif target == 'parents':
                        recipients = User.objects.filter(role='parent', is_active=True)
                    elif target == 'teachers':
                        recipients = User.objects.filter(role='teacher', is_active=True).exclude(id=request.user.id)
                    else:
                        recipients = User.objects.filter(is_active=True).exclude(id=request.user.id)
                    
                    # Create notifications in batch
                    notifications = []
                    for recipient in recipients[:100]:
                        notifications.append(
                            Notification(
                                recipient=recipient,
                                notification_type='new_announcement',
                                title=f'New Announcement: {announcement.title}',
                                message=announcement.content[:200],
                                link_url=f'/information/announcement/{announcement.id}/'
                            )
                        )
                    
                    if notifications:
                        Notification.objects.bulk_create(notifications)
                
                messages.success(request, '✅ Announcement created successfully!')
                return redirect('information:announcement_list')
                
            except Exception as e:
                messages.error(request, f'❌ Error saving announcement: {str(e)}')
                print(f"Error: {e}")
        else:
            messages.error(request, '❌ Please correct the errors below.')
    else:
        form = AnnouncementForm()
    
    context = {
        'form': form,
        'teacher': teacher,
    }
    return render(request, 'information/create_announcement.html', context)

@login_required
def recent_conversations_api(request):
    """API endpoint for recent chat conversations (AJAX)"""
    # Allow only parents to access this
    if request.user.role != 'parent':
        return JsonResponse({
            'success': True,
            'conversations': []  # Return empty list instead of error for non-parents
        })
    
    try:
        parent = request.user.parent_profile
        
        # Get recent conversations
        conversations = ChatConversation.objects.filter(
            parent=parent
        ).annotate(
            last_message_time=Max('conversation_messages__timestamp'),
            unread_count=Count(
                'conversation_messages',
                filter=Q(
                    conversation_messages__sender_role='teacher',
                    conversation_messages__is_read=False
                )
            )
        ).order_by('-last_message_time')[:5]  # Get last 5
        
        data = []
        for conv in conversations:
            last_msg = conv.get_last_message()
            data.append({
                'id': conv.id,
                'subject': conv.subject or 'Conversation',
                'status': conv.status,
                'unread_count': conv.unread_count,
                'last_message': last_msg.message[:50] if last_msg else '',
                'last_message_time': conv.last_message_time.isoformat() if conv.last_message_time else None,
            })
        
        return JsonResponse({
            'success': True,
            'conversations': data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'conversations': []
        }, status=500)

# ========================================
# Chat System (Original)
# ========================================

@login_required
def chat_list(request):
    """List all chat rooms for user"""
    if request.user.is_parent():
        parent = request.user.parent_profile
        chat_rooms = ChatRoom.objects.filter(
            parent=parent,
            is_active=True
        ).select_related('teacher__user').order_by('-last_message_at')
    elif request.user.is_teacher():
        teacher = request.user.teacher_profile
        chat_rooms = ChatRoom.objects.filter(
            teacher=teacher,
            is_active=True
        ).select_related('parent__user').order_by('-last_message_at')
    else:
        chat_rooms = []
    
    context = {
        'chat_rooms': chat_rooms,
    }
    return render(request, 'information/chat_list.html', context)


@login_required
def chat_room(request, room_id):
    """View chat room messages"""
    if request.user.is_parent():
        parent = request.user.parent_profile
        room = get_object_or_404(ChatRoom, id=room_id, parent=parent)
    elif request.user.is_teacher():
        teacher = request.user.teacher_profile
        room = get_object_or_404(ChatRoom, id=room_id, teacher=teacher)
    else:
        return redirect('information:chat_list')
    
    # Get messages
    messages_list = room.messages.all().order_by('created_at')
    
    # Mark messages as read
    unread_messages = messages_list.filter(is_read=False).exclude(sender=request.user)
    for msg in unread_messages:
        msg.mark_as_read()
    
    context = {
        'room': room,
        'messages': messages_list,
    }
    return render(request, 'information/chat_room.html', context)


@login_required
@parent_required
def start_chat(request, teacher_id):
    """Start a new chat with teacher"""
    parent = request.user.parent_profile
    from users.models import Teacher
    
    teacher = get_object_or_404(Teacher, id=teacher_id)
    
    # Get or create chat room
    room, created = ChatRoom.objects.get_or_create(
        parent=parent,
        teacher=teacher
    )
    
    if created:
        messages.success(request, 'Chat started successfully!')
    
    return redirect('information:chat_room', room_id=room.id)


@login_required
def send_message(request, room_id):
    """Send a message in chat room (AJAX)"""
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        
        if not content:
            return JsonResponse({'error': 'Message cannot be empty'}, status=400)
        
        # Verify access to room
        if request.user.is_parent():
            parent = request.user.parent_profile
            room = get_object_or_404(ChatRoom, id=room_id, parent=parent)
        elif request.user.is_teacher():
            teacher = request.user.teacher_profile
            room = get_object_or_404(ChatRoom, id=room_id, teacher=teacher)
        else:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        # Create message
        message = ChatRoomMessage.objects.create(
            chat_room=room,
            sender=request.user,
            content=content,
            message_type='text'
        )
        
        # Update room's last message time
        room.last_message_at = timezone.now()
        room.save()
        
        return JsonResponse({
            'success': True,
            'message_id': message.id,
            'content': message.content,
            'created_at': message.created_at.isoformat()
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def mark_messages_read(request, room_id):
    """Mark all messages as read (AJAX)"""
    if request.user.is_parent():
        parent = request.user.parent_profile
        room = get_object_or_404(ChatRoom, id=room_id, parent=parent)
    elif request.user.is_teacher():
        teacher = request.user.teacher_profile
        room = get_object_or_404(ChatRoom, id=room_id, teacher=teacher)
    else:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Mark messages as read
    unread = room.messages.filter(is_read=False).exclude(sender=request.user)
    count = unread.count()
    
    for msg in unread:
        msg.mark_as_read()
    
    return JsonResponse({'success': True, 'count': count})


# ========================================
# Chat History (NEW - For Chatbot Integration)
# ========================================

@login_required
def chat_history(request):
    """Display all chat conversations for parent"""
    if request.user.role != 'parent':
        messages.error(request, 'Unauthorized access')
        return redirect('users:dashboard')
    
    parent = request.user.parent_profile
    
    # Get all conversations (active and closed)
    conversations = ChatConversation.objects.filter(
        parent=parent
    ).annotate(
        last_message_time=Max('conversation_messages__timestamp'),
        message_count=Count('conversation_messages')
    ).order_by('-last_message_time')
    
    # Add unread count and last message to each conversation
    for conv in conversations:
        conv.unread_messages = conv.conversation_messages.filter(
            sender_role='teacher',
            is_read=False
        ).count()
        conv.last_msg = conv.get_last_message()
    
    context = {
        'conversations': conversations,
        'active_count': conversations.filter(status__in=['waiting', 'active']).count(),
        'closed_count': conversations.filter(status='closed').count(),
    }
    
    return render(request, 'information/chat_history.html', context)


@login_required
def conversation_detail(request, conversation_id):
    """View a specific conversation with all messages"""
    if request.user.role != 'parent':
        messages.error(request, 'Unauthorized access')
        return redirect('users:dashboard')
    
    parent = request.user.parent_profile
    conversation = get_object_or_404(
        ChatConversation, 
        id=conversation_id, 
        parent=parent
    )
    
    # Mark all teacher messages as read
    conversation.mark_as_read_by_parent()
    
    # Get all messages
    chat_messages = conversation.conversation_messages.all().order_by('timestamp')
    
    context = {
        'conversation': conversation,
        'chat_messages': chat_messages,
    }
    
    return render(request, 'information/conversation_detail.html', context)


@login_required
def send_conversation_message(request, conversation_id):
    """Send a message in a conversation from the history page"""
    if request.method == 'POST' and request.user.role == 'parent':
        parent = request.user.parent_profile
        conversation = get_object_or_404(
            ChatConversation, 
            id=conversation_id, 
            parent=parent
        )
        
        message_text = request.POST.get('message', '').strip()
        
        if message_text:
            # Reopen conversation if closed
            if conversation.status == 'closed':
                conversation.status = 'waiting'
                conversation.resolved_at = None
                conversation.save()
            
            # Create message
            ConversationMessage.objects.create(
                conversation=conversation,
                sender_role='parent',
                sender_user=request.user,
                message=message_text
            )
            
            # Update conversation flags
            conversation.teacher_waiting = True
            conversation.parent_waiting = False
            conversation.save()
            
            messages.success(request, 'Message sent successfully!')
        else:
            messages.error(request, 'Message cannot be empty')
    
    return redirect('information:conversation_detail', conversation_id=conversation_id)


@login_required
def delete_conversation(request, conversation_id):
    """Delete a conversation"""
    if request.user.role != 'parent':
        messages.error(request, 'Unauthorized access')
        return redirect('users:dashboard')
    
    parent = request.user.parent_profile
    conversation = get_object_or_404(
        ChatConversation, 
        id=conversation_id, 
        parent=parent
    )
    
    if request.method == 'POST':
        conversation.delete()
        messages.success(request, 'Conversation deleted successfully!')
        return redirect('information:chat_history')
    
    return redirect('information:conversation_detail', conversation_id=conversation_id)


# ========================================
# Notifications
# ========================================

@login_required
def notification_list(request):
    """List all notifications for user"""
    notifications = Notification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')
    
    context = {
        'notifications': notifications,
    }
    return render(request, 'information/notification_list.html', context)


@login_required
def mark_notification_read(request, notification_id):
    """Mark notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.mark_as_read()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('information:notification_list')


@login_required
def mark_all_notifications_read(request):
    """Mark all notifications as read"""
    Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).update(is_read=True)
    
    messages.success(request, 'All notifications marked as read!')
    return redirect('information:notification_list')


# ========================================
# Chatbot
# ========================================

@login_required
def chatbot(request):
    """Chatbot interface"""
    context = {}
    return render(request, 'information/chatbot.html', context)


@login_required
def chatbot_query(request):
    """Process chatbot query (AJAX)"""
    if request.method == 'POST':
        query = request.POST.get('query', '').strip().lower()
        
        if not query:
            return JsonResponse({'error': 'Query cannot be empty'}, status=400)
        
        # Search for matching bot message
        bot_messages = BotMessage.objects.filter(is_active=True).order_by('-priority')
        
        response = None
        for bot_msg in bot_messages:
            keywords = bot_msg.get_keywords_list()
            if any(keyword in query for keyword in keywords):
                response = bot_msg.response_text
                
                # Increment usage count
                bot_msg.usage_count += 1
                bot_msg.save()
                break
        
        if not response:
            response = "I'm sorry, I don't understand. Please try rephrasing your question or contact support."
        
        return JsonResponse({
            'success': True,
            'response': response
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)