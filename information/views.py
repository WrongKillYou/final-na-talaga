# information/views.py
# CLEANED - Unified chat system, proper role-based access

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Max, Count
from django.utils import timezone
from datetime import timedelta, datetime

from users.decorators import teacher_required, parent_required
from users.models import User, Parent, Teacher, Child
from .models import (
    Event, Announcement, AnnouncementRead,
    BotMessage, ChatConversation, ConversationMessage,
    Notification, Activity
)
from .forms import AnnouncementForm, EventForm  # Assume you'll create these


# ========================================
# EVENTS
# ========================================

@login_required
def event_list(request):
    """List all upcoming events"""
    from datetime import date
    
    # Get active, non-cancelled events
    events = Event.objects.filter(
        is_active=True,
        is_cancelled=False,
        start_date__gte=date.today()
    ).order_by('start_date')
    
    # Filter by target audience if needed
    if request.user.role == 'parent':
        events = events.filter(
            Q(target_audience='all') | Q(target_audience__icontains='parent')
        )
    elif request.user.role == 'teacher':
        events = events.filter(
            Q(target_audience='all') | Q(target_audience__icontains='teacher')
        )
    
    context = {
        'events': events,
    }
    return render(request, 'information/event_list.html', context)


@login_required
def event_detail(request, event_id):
    """View event details"""
    event = get_object_or_404(Event, id=event_id, is_active=True)
    
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
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = teacher
            event.save()
            
            # Log activity
            Activity.log_activity(
                user=request.user,
                activity_type='event',
                description=f"Created event: {event.title}",
                related_id=event.id,
                related_type='Event'
            )
            
            messages.success(request, '✅ Event created successfully!')
            return redirect('information:event_list')
    else:
        form = EventForm()
    
    context = {
        'form': form,
        'teacher': teacher,
    }
    return render(request, 'information/create_event.html', context)


@login_required
@teacher_required
def edit_event(request, event_id):
    """Edit event (teachers only)"""
    teacher = request.user.teacher_profile
    event = get_object_or_404(Event, id=event_id, created_by=teacher)
    
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Event updated successfully!')
            return redirect('information:event_detail', event_id=event_id)
    else:
        form = EventForm(instance=event)
    
    context = {
        'form': form,
        'event': event,
        'teacher': teacher,
    }
    return render(request, 'information/edit_event.html', context)


@login_required
@teacher_required
def delete_event(request, event_id):
    """Delete event (teachers only)"""
    teacher = request.user.teacher_profile
    event = get_object_or_404(Event, id=event_id, created_by=teacher)
    
    if request.method == 'POST':
        event_title = event.title
        event.delete()
        
        messages.success(request, f'✅ Event "{event_title}" deleted successfully!')
        return redirect('information:event_list')
    
    return redirect('information:event_detail', event_id=event_id)


# ========================================
# ANNOUNCEMENTS
# ========================================

@login_required
def announcement_list(request):
    """List all published announcements"""
    # Base query - only published announcements
    announcements = Announcement.objects.filter(
        is_active=True,
        publish_date__lte=timezone.now()
    ).select_related('teacher__user')
    
    # Exclude expired announcements
    announcements = [a for a in announcements if not a.is_expired()]
    
    # Role-based filtering
    if request.user.role == 'parent':
        announcements = [
            a for a in announcements 
            if a.target_audience in ['all', 'parents']
        ]
    elif request.user.role == 'teacher':
        announcements = [
            a for a in announcements 
            if a.target_audience in ['all', 'teachers']
        ]
    
    # Apply additional filters from GET params
    filter_type = request.GET.get('filter', 'all')
    if filter_type == 'important':
        announcements = [a for a in announcements if a.is_important]
    elif filter_type == 'recent':
        seven_days_ago = timezone.now() - timedelta(days=7)
        announcements = [a for a in announcements if a.created_at >= seven_days_ago]
    
    # Search functionality
    search_query = request.GET.get('search', '').strip()
    if search_query:
        announcements = [
            a for a in announcements 
            if search_query.lower() in (a.title.lower() + ' ' + a.content.lower())
        ]
    
    context = {
        'announcements': announcements,
        'search_query': search_query,
        'filter_type': filter_type,
    }
    return render(request, 'information/announcement_list.html', context)


@login_required
def announcement_detail(request, announcement_id):
    """View announcement details"""
    announcement = get_object_or_404(
        Announcement,
        pk=announcement_id,
        is_active=True
    )
    
    # Check if expired
    if announcement.is_expired():
        messages.warning(request, 'This announcement has expired.')
    
    # Mark as read
    AnnouncementRead.objects.get_or_create(
        announcement=announcement,
        user=request.user
    )
    
    # Increment view count
    announcement.views_count += 1
    announcement.save(update_fields=['views_count'])
    
    context = {
        'announcement': announcement,
    }
    return render(request, 'information/announcement_detail.html', context)


@login_required
@teacher_required
def create_announcement(request):
    """Create new announcement (teachers only)"""
    teacher = request.user.teacher_profile
    
    if request.method == 'POST':
        form = AnnouncementForm(request.POST, request.FILES)
        
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.teacher = teacher
            announcement.is_active = True
            announcement.save()
            
            # Handle notifications if requested
            send_notification = form.cleaned_data.get('send_notification', False)
            
            if send_notification:
                # Determine recipients based on target audience
                target = announcement.target_audience.lower()
                
                if target == 'all':
                    recipients = User.objects.filter(
                        is_active=True
                    ).exclude(id=request.user.id)
                elif target == 'parents':
                    recipients = User.objects.filter(
                        role='parent', 
                        is_active=True
                    )
                elif target == 'teachers':
                    recipients = User.objects.filter(
                        role='teacher', 
                        is_active=True
                    ).exclude(id=request.user.id)
                else:
                    recipients = User.objects.filter(
                        is_active=True
                    ).exclude(id=request.user.id)
                
                # Create notifications in batch
                notifications = [
                    Notification(
                        recipient=recipient,
                        notification_type='new_announcement',
                        title=f'New Announcement: {announcement.title}',
                        message=announcement.content[:200],
                        link_url=f'/information/announcement/{announcement.id}/'
                    )
                    for recipient in recipients[:100]  # Limit to prevent overload
                ]
                
                if notifications:
                    Notification.objects.bulk_create(notifications)
            
            # Log activity
            Activity.log_activity(
                user=request.user,
                activity_type='announcement',
                description=f"Created announcement: {announcement.title}",
                related_id=announcement.id,
                related_type='Announcement'
            )
            
            messages.success(request, '✅ Announcement created successfully!')
            return redirect('information:announcement_list')
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
@teacher_required
def edit_announcement(request, announcement_id):
    """Edit announcement (teachers only)"""
    teacher = request.user.teacher_profile
    announcement = get_object_or_404(
        Announcement, 
        id=announcement_id, 
        teacher=teacher
    )
    
    if request.method == 'POST':
        form = AnnouncementForm(request.POST, request.FILES, instance=announcement)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Announcement updated successfully!')
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
    """Delete announcement (teachers only)"""
    teacher = request.user.teacher_profile
    announcement = get_object_or_404(
        Announcement, 
        id=announcement_id, 
        teacher=teacher
    )
    
    if request.method == 'POST':
        announcement_title = announcement.title
        announcement.delete()
        messages.success(request, f'✅ Announcement "{announcement_title}" deleted successfully!')
        return redirect('information:announcement_list')
    
    return redirect('information:announcement_detail', announcement_id=announcement_id)


# ========================================
# CHATBOT (FAQ System)
# ========================================

@login_required
@parent_required
def chatbot(request):
    """Chatbot interface for parents"""
    parent = request.user.parent_profile
    
    # Get available categories for quick access
    categories = BotMessage.objects.filter(
        is_active=True
    ).values_list('category', flat=True).distinct()
    
    context = {
        'parent': parent,
        'categories': categories,
    }
    return render(request, 'information/chatbot.html', context)


@login_required
@parent_required
def chatbot_query(request):
    """Process chatbot query (AJAX)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    query = request.POST.get('query', '').strip().lower()
    
    if not query:
        return JsonResponse({'error': 'Query cannot be empty'}, status=400)
    
    # Search for matching bot message
    bot_messages = BotMessage.objects.filter(
        is_active=True
    ).order_by('-priority')
    
    response = None
    matched_message = None
    
    for bot_msg in bot_messages:
        keywords = bot_msg.get_keywords_list()
        if any(keyword in query for keyword in keywords):
            response = bot_msg.response_text
            matched_message = bot_msg
            
            # Increment usage count
            bot_msg.usage_count += 1
            bot_msg.save(update_fields=['usage_count'])
            break
    
    if not response:
        # No match found - suggest starting a chat with teacher
        response = {
            'text': "I'm sorry, I don't have an answer for that. Would you like to start a conversation with a teacher?",
            'suggest_chat': True
        }
    else:
        response = {
            'text': response,
            'suggest_chat': False,
            'buttons': matched_message.button_options if matched_message and matched_message.has_buttons else None
        }
    
    return JsonResponse({
        'success': True,
        'response': response
    })


# ========================================
# CHAT CONVERSATIONS (Parent-Teacher)
# ========================================

@login_required
@parent_required
def start_conversation(request):
    """Start a new conversation with a teacher"""
    parent = request.user.parent_profile
    
    if request.method != 'POST':
        return redirect('information:chat_history')
    
    subject = request.POST.get('subject', '').strip()
    child_id = request.POST.get('child_id')
    initial_message = request.POST.get('message', '').strip()
    
    if not subject or not initial_message:
        messages.error(request, 'Subject and message are required.')
        return redirect('information:chatbot')
    
    # Get child if specified
    child = None
    if child_id:
        child = get_object_or_404(Child, id=child_id, parents=parent)
        # Try to assign child's class teacher
        teacher = child.class_teacher
    else:
        teacher = None
    
    # Create conversation
    conversation = ChatConversation.objects.create(
        parent=parent,
        teacher=teacher,
        child=child,
        subject=subject,
        status='waiting' if not teacher else 'active'
    )
    
    # Create initial message
    ConversationMessage.objects.create(
        conversation=conversation,
        sender_role='parent',
        sender_user=request.user,
        message=initial_message
    )
    
    # If teacher assigned, notify them
    if teacher:
        Notification.objects.create(
            recipient=teacher.user,
            notification_type='new_message',
            title='New Message from Parent',
            message=f"{parent.user.get_full_name()} started a conversation: {subject}",
            link_url=f'/information/conversation/{conversation.id}/'
        )
        conversation.assigned_at = timezone.now()
        conversation.save()
    
    messages.success(request, '✅ Conversation started! A teacher will respond soon.')
    return redirect('information:conversation_detail', conversation_id=conversation.id)


@login_required
def chat_history(request):
    """Display conversation history"""
    if request.user.role == 'parent':
        parent = request.user.parent_profile
        
        conversations = ChatConversation.objects.filter(
            parent=parent
        ).annotate(
            last_message_time=Max('messages__timestamp')
        ).order_by('-last_message_time')
        
        # Add unread count to each conversation
        for conv in conversations:
            conv.unread_count = conv.get_unread_count_for_parent()
        
    elif request.user.role == 'teacher':
        teacher = request.user.teacher_profile
        
        conversations = ChatConversation.objects.filter(
            teacher=teacher
        ).annotate(
            last_message_time=Max('messages__timestamp')
        ).order_by('-last_message_time')
        
        # Add unread count to each conversation
        for conv in conversations:
            conv.unread_count = conv.get_unread_count_for_teacher()
    else:
        conversations = []
    
    context = {
        'conversations': conversations,
    }
    return render(request, 'information/chat_history.html', context)


@login_required
def conversation_detail(request, conversation_id):
    """View a specific conversation with all messages"""
    if request.user.role == 'parent':
        parent = request.user.parent_profile
        conversation = get_object_or_404(
            ChatConversation,
            id=conversation_id,
            parent=parent
        )
        # Mark messages as read
        conversation.mark_as_read_by_parent()
        
    elif request.user.role == 'teacher':
        teacher = request.user.teacher_profile
        conversation = get_object_or_404(
            ChatConversation,
            id=conversation_id,
            teacher=teacher
        )
        # Mark messages as read
        conversation.mark_as_read_by_teacher()
    else:
        messages.error(request, 'Unauthorized access.')
        return redirect('users:dashboard')
    
    # Get all messages
    chat_messages = conversation.messages.all().order_by('timestamp')
    
    context = {
        'conversation': conversation,
        'chat_messages': chat_messages,
    }
    return render(request, 'information/conversation_detail.html', context)


@login_required
def send_conversation_message(request, conversation_id):
    """Send a message in a conversation"""
    if request.method != 'POST':
        return redirect('information:chat_history')
    
    if request.user.role == 'parent':
        parent = request.user.parent_profile
        conversation = get_object_or_404(
            ChatConversation,
            id=conversation_id,
            parent=parent
        )
        sender_role = 'parent'
        
    elif request.user.role == 'teacher':
        teacher = request.user.teacher_profile
        conversation = get_object_or_404(
            ChatConversation,
            id=conversation_id,
            teacher=teacher
        )
        sender_role = 'teacher'
    else:
        messages.error(request, 'Unauthorized access.')
        return redirect('users:dashboard')
    
    message_text = request.POST.get('message', '').strip()
    
    if not message_text:
        messages.error(request, 'Message cannot be empty.')
        return redirect('information:conversation_detail', conversation_id=conversation_id)
    
    # Reopen conversation if closed
    if conversation.status == 'closed':
        conversation.status = 'active'
        conversation.resolved_at = None
    
    # Create message
    new_message = ConversationMessage.objects.create(
        conversation=conversation,
        sender_role=sender_role,
        sender_user=request.user,
        message=message_text
    )
    
    # Update conversation waiting flags
    if sender_role == 'parent':
        conversation.teacher_waiting = True
        conversation.parent_waiting = False
        
        # Notify teacher
        if conversation.teacher:
            Notification.objects.create(
                recipient=conversation.teacher.user,
                notification_type='new_message',
                title='New Message from Parent',
                message=f"{conversation.parent.user.get_full_name()}: {message_text[:100]}",
                link_url=f'/information/conversation/{conversation.id}/'
            )
    else:
        conversation.parent_waiting = True
        conversation.teacher_waiting = False
        
        # Notify parent
        Notification.objects.create(
            recipient=conversation.parent.user,
            notification_type='new_message',
            title='New Message from Teacher',
            message=f"{conversation.teacher.user.get_full_name()}: {message_text[:100]}",
            link_url=f'/information/conversation/{conversation.id}/'
        )
    
    conversation.save()
    
    # Log activity
    Activity.log_activity(
        user=request.user,
        activity_type='message',
        description=f"Sent message in conversation: {conversation.subject}",
        related_id=conversation.id,
        related_type='ChatConversation'
    )
    
    messages.success(request, '✅ Message sent!')
    return redirect('information:conversation_detail', conversation_id=conversation_id)


@login_required
def close_conversation(request, conversation_id):
    """Close/resolve a conversation"""
    if request.method != 'POST':
        return redirect('information:chat_history')
    
    if request.user.role == 'teacher':
        teacher = request.user.teacher_profile
        conversation = get_object_or_404(
            ChatConversation,
            id=conversation_id,
            teacher=teacher
        )
    else:
        messages.error(request, 'Only teachers can close conversations.')
        return redirect('information:conversation_detail', conversation_id=conversation_id)
    
    conversation.status = 'resolved'
    conversation.resolved_at = timezone.now()
    conversation.save()
    
    messages.success(request, '✅ Conversation marked as resolved.')
    return redirect('information:chat_history')


# ========================================
# NOTIFICATIONS
# ========================================

@login_required
def notification_list(request):
    """List all notifications for user"""
    notifications = Notification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')
    
    # Pagination (optional)
    from django.core.paginator import Paginator
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'information/notification_list.html', context)


@login_required
def mark_notification_read(request, notification_id):
    """Mark a specific notification as read"""
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        recipient=request.user
    )
    notification.mark_as_read()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    # Redirect to link if available
    if notification.link_url:
        return redirect(notification.link_url)
    
    return redirect('information:notification_list')


@login_required
def mark_all_notifications_read(request):
    """Mark all notifications as read"""
    Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).update(is_read=True, read_at=timezone.now())
    
    messages.success(request, '✅ All notifications marked as read!')
    return redirect('information:notification_list')


@login_required
def get_unread_notifications_count(request):
    """API endpoint to get unread notification count (AJAX)"""
    count = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()
    
    return JsonResponse({'count': count})