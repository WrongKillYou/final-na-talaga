# information/api_views.py

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from datetime import datetime, timedelta
from django.utils.timesince import timesince
from users import models
from .models import Announcement, Event, ChatConversation, ConversationMessage
from users.models import Child
import json


@login_required
@require_http_methods(["GET"])
def recent_announcements_api(request):
    """API endpoint to get recent announcements for chatbot"""
    
    # Get announcements based on user role
    if request.user.role == 'parent':
        # Parents see all published announcements
        announcements = Announcement.objects.filter(
            is_published=True,
            publish_date__lte=datetime.now()
        ).order_by('-publish_date')[:10]
    elif request.user.role == 'teacher':
        # Teachers see their own announcements
        announcements = Announcement.objects.filter(
            posted_by=request.user.teacher_profile
        ).order_by('-publish_date')[:10]
    else:
        announcements = []
    
    # Convert to JSON-serializable format
    data = []
    for announcement in announcements:
        data.append({
            'id': announcement.id,
            'title': announcement.title,
            'content': announcement.content,
            'is_important': announcement.priority in ['high', 'urgent'],
            'publish_date': announcement.publish_date.isoformat(),
            'teacher_name': announcement.posted_by.user.get_full_name() if announcement.posted_by else 'Admin',
        })
    
    return JsonResponse(data, safe=False)


@login_required
@require_http_methods(["GET"])
def upcoming_events_api(request):
    """API endpoint to get upcoming events for chatbot"""
    
    today = datetime.now().date()
    
    # Get upcoming events (next 30 days)
    events = Event.objects.filter(
        start_date__gte=today,
        start_date__lte=today + timedelta(days=30),
        is_active=True
    ).order_by('start_date')[:10]
    
    # Convert to JSON-serializable format
    data = []
    for event in events:
        data.append({
            'id': event.id,
            'title': event.title,
            'description': event.description,
            'event_type': event.get_event_type_display(),
            'date': event.start_date.isoformat(),
            'start_time': event.start_time.strftime('%I:%M %p') if event.start_time else None,
            'end_time': event.end_time.strftime('%I:%M %p') if event.end_time else None,
            'location': event.location,
        })
    
    return JsonResponse(data, safe=False)


@login_required
@require_http_methods(["GET"])
def parent_children_api(request):
    """Get parent's children list"""
    if request.user.role != 'parent':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    parent = request.user.parent_profile
    children = parent.children.all()
    
    return JsonResponse([
        {
            'id': child.id,
            'name': child.get_full_name(),
            'grade_level': child.grade_level,
            'section': child.section
        }
        for child in children
    ], safe=False)


@login_required
@require_http_methods(["GET"])
def child_schedule_api(request, child_id):
    """Get child's class schedule"""
    if request.user.role != 'parent':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    parent = request.user.parent_profile
    
    try:
        child = Child.objects.get(id=child_id, parents=parent)
        
        # Get enrolled classes
        from academics.models import Enrollment
        enrollments = Enrollment.objects.filter(
            student=child,
            status='enrolled'
        ).select_related('class_enrolled__subject', 'class_enrolled__teacher')
        
        schedule_data = []
        for enrollment in enrollments:
            class_obj = enrollment.class_enrolled
            schedule_data.append({
                'subject': class_obj.subject.name,
                'teacher': class_obj.teacher.user.get_full_name(),
                'schedule': class_obj.schedule if hasattr(class_obj, 'schedule') else 'Not specified',
                'room': class_obj.room if hasattr(class_obj, 'room') else 'TBA',
            })
        
        return JsonResponse({
            'child_name': child.get_full_name(),
            'grade_level': child.grade_level,
            'section': child.section,
            'schedule': schedule_data
        })
    
    except Child.DoesNotExist:
        return JsonResponse({'error': 'Child not found'}, status=404)


# ========================================
# LIVE CHAT API ENDPOINTS
# ========================================

@login_required
@require_http_methods(["GET"])
def parent_conversations_api(request):
    """Get parent's active conversations"""
    if request.user.role != 'parent':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    parent = request.user.parent_profile
    
    # Get active conversation
    active_conv = ChatConversation.objects.filter(
        parent=parent,
        status__in=['waiting', 'active']
    ).first()
    
    if active_conv:
        return JsonResponse({
            'has_active': True,
            'conversation': {
                'id': active_conv.id,
                'subject': active_conv.subject,
                'status': active_conv.status,
                'teacher_name': active_conv.teacher.user.get_full_name() if active_conv.teacher else 'Waiting for teacher...',
                'created_at': active_conv.created_at.isoformat(),
            }
        })
    
    return JsonResponse({'has_active': False})


@login_required
@require_http_methods(["POST"])
def create_conversation_api(request):
    """Create new chat conversation"""
    if request.user.role != 'parent':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        data = json.loads(request.body)
        parent = request.user.parent_profile
        
        subject = data.get('subject', 'General Inquiry')
        child_id = data.get('child_id')
        initial_message = data.get('initial_message')
        
        if not initial_message:
            return JsonResponse({'success': False, 'error': 'Message is required'}, status=400)
        
        # Check for existing active conversation
        existing = ChatConversation.objects.filter(
            parent=parent,
            status__in=['waiting', 'active']
        ).first()
        
        if existing:
            return JsonResponse({
                'success': False, 
                'error': 'You already have an active conversation',
                'conversation_id': existing.id
            }, status=400)
        
        # Get child if specified
        child = None
        if child_id:
            try:
                child = Child.objects.get(id=child_id, parents=parent)
            except Child.DoesNotExist:
                pass
        
        # Create conversation
        conversation = ChatConversation.objects.create(
            parent=parent,
            child=child,
            subject=subject,
            status='waiting'
        )
        
        # Add initial message
        ConversationMessage.objects.create(
            conversation=conversation,
            sender_role='parent',
            sender_user=request.user,
            message=initial_message
        )
        
        # Try to assign available teacher
        assigned = assign_teacher_to_conversation(conversation)
        
        return JsonResponse({
            'success': True,
            'conversation_id': conversation.id,
            'assigned': assigned
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def conversation_messages_api(request, conversation_id):
    """Get messages for a conversation"""
    try:
        conversation = ChatConversation.objects.get(id=conversation_id)
        
        # Check permissions
        if request.user.role == 'parent':
            if conversation.parent.user != request.user:
                return JsonResponse({'error': 'Unauthorized'}, status=403)
            # Mark as read by parent
            conversation.mark_as_read_by_parent()
        elif request.user.role == 'teacher':
            if conversation.teacher and conversation.teacher.user != request.user:
                return JsonResponse({'error': 'Unauthorized'}, status=403)
            # Mark as read by teacher
            conversation.mark_as_read_by_teacher()
        
        messages = conversation.conversation_messages.all()
        
        return JsonResponse({
            'conversation_id': conversation.id,
            'subject': conversation.subject,
            'status': conversation.status,
            'teacher_name': conversation.teacher.user.get_full_name() if conversation.teacher else 'Waiting for teacher...',
            'messages': [
                {
                    'id': msg.id,
                    'sender_role': msg.sender_role,
                    'sender_name': msg.sender_user.get_full_name() if msg.sender_user else 'System',
                    'message': msg.message,
                    'timestamp': msg.timestamp.isoformat(),
                    'is_read': msg.is_read
                }
                for msg in messages
            ]
        })
    
    except ChatConversation.DoesNotExist:
        return JsonResponse({'error': 'Conversation not found'}, status=404)


@login_required
@require_http_methods(["POST"])
def send_message_api(request, conversation_id):
    """Send message in conversation"""
    try:
        conversation = ChatConversation.objects.get(id=conversation_id)
        data = json.loads(request.body)
        message_text = data.get('message', '').strip()
        
        if not message_text:
            return JsonResponse({'success': False, 'error': 'Message is required'}, status=400)
        
        # Determine sender role
        if request.user.role == 'parent':
            if conversation.parent.user != request.user:
                return JsonResponse({'error': 'Unauthorized'}, status=403)
            sender_role = 'parent'
            conversation.teacher_waiting = True
            conversation.parent_waiting = False
        elif request.user.role == 'teacher':
            if not conversation.teacher:
                # Assign this teacher
                conversation.teacher = request.user.teacher_profile
                conversation.status = 'active'
                conversation.assigned_at = datetime.now()
            elif conversation.teacher.user != request.user:
                return JsonResponse({'error': 'Unauthorized'}, status=403)
            sender_role = 'teacher'
            conversation.parent_waiting = True
            conversation.teacher_waiting = False
        else:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        # Create message
        message = ConversationMessage.objects.create(
            conversation=conversation,
            sender_role=sender_role,
            sender_user=request.user,
            message=message_text
        )
        
        conversation.save()
        
        return JsonResponse({
            'success': True,
            'message': {
                'id': message.id,
                'sender_role': message.sender_role,
                'sender_name': request.user.get_full_name(),
                'message': message.message,
                'timestamp': message.timestamp.isoformat()
            }
        })
    
    except ChatConversation.DoesNotExist:
        return JsonResponse({'error': 'Conversation not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def close_conversation_api(request, conversation_id):
    """Close a conversation"""
    try:
        conversation = ChatConversation.objects.get(id=conversation_id)
        
        # Check permissions
        if request.user.role == 'parent' and conversation.parent.user != request.user:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        if request.user.role == 'teacher' and conversation.teacher and conversation.teacher.user != request.user:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        conversation.status = 'closed'
        conversation.resolved_at = datetime.now()
        conversation.save()
        
        # Decrement teacher's conversation count
        if conversation.teacher:
            try:
                availability = conversation.teacher.chat_availability
                availability.decrement_conversations()
            except:
                pass
        
        return JsonResponse({'success': True})
    
    except ChatConversation.DoesNotExist:
        return JsonResponse({'error': 'Conversation not found'}, status=404)


@login_required
@require_http_methods(["GET"])
def teacher_inbox_api(request):
    """Get teacher's inbox conversations"""
    if request.user.role != 'teacher':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    teacher = request.user.teacher_profile
    
    # Get conversations assigned to this teacher
    conversations = ChatConversation.objects.filter(
        teacher=teacher,
        status__in=['waiting', 'active']
    ).order_by('-updated_at')
    
    # Also get waiting conversations if teacher is available
    waiting_conversations = ChatConversation.objects.filter(
        teacher=None,
        status='waiting'
    ).order_by('created_at')[:5]
    
    data = {
        'conversations': [],
        'waiting': []
    }
    
    for conv in conversations:
        last_msg = conv.get_last_message()
        data['conversations'].append({
            'id': conv.id,
            'subject': conv.subject,
            'parent_name': conv.parent.user.get_full_name(),
            'status': conv.status,
            'last_message': last_msg.message[:50] if last_msg else '',
            'updated_at': conv.updated_at.isoformat(),
            'has_unread': conv.teacher_waiting
        })
    
    for conv in waiting_conversations:
        last_msg = conv.get_last_message()
        data['waiting'].append({
            'id': conv.id,
            'subject': conv.subject,
            'parent_name': conv.parent.user.get_full_name(),
            'last_message': last_msg.message[:50] if last_msg else '',
            'created_at': conv.created_at.isoformat()
        })
    
    return JsonResponse(data)


@login_required
@require_http_methods(["GET"])
def unread_count_api(request):
    """Get unread message count"""
    count = 0
    
    if request.user.role == 'parent':
        parent = request.user.parent_profile
        count = ConversationMessage.objects.filter(
            conversation__parent=parent,
            sender_role='teacher',
            is_read=False
        ).count()
    elif request.user.role == 'teacher':
        teacher = request.user.teacher_profile
        count = ConversationMessage.objects.filter(
            conversation__teacher=teacher,
            sender_role='parent',
            is_read=False
        ).count()
    
    return JsonResponse({'count': count})


# ========================================
# HELPER FUNCTIONS
# ========================================

def assign_teacher_to_conversation(conversation):
    """Auto-assign available teacher to conversation"""
    
    # Priority 1: Child's class teacher
    if conversation.child:
        # Try to get the child's main teacher (from their enrolled classes)
        from academics.models import Enrollment
        enrollments = Enrollment.objects.filter(
            student=conversation.child,
            status='enrolled'
        ).select_related('class_enrolled__teacher')
        
        for enrollment in enrollments:
            teacher = enrollment.class_enrolled.teacher
            try:
                availability = teacher.chat_availability
                if availability.is_available():
                    conversation.teacher = teacher
                    conversation.status = 'active'
                    conversation.assigned_at = datetime.now()
                    conversation.save()
                    
                    availability.increment_conversations()
                    
                    # Send system message
                    ConversationMessage.objects.create(
                        conversation=conversation,
                        sender_role='system',
                        message=f"{teacher.user.get_full_name()} has joined the conversation."
                    )
                    return True
            except:
                continue
    
    # Priority 2: Any available teacher
    available_teachers = TeacherAvailability.objects.filter(
        status='online',
        current_conversations__lt=models.F('max_conversations')
    ).select_related('teacher')
    
    if available_teachers.exists():
        availability = available_teachers.first()
        conversation.teacher = availability.teacher
        conversation.status = 'active'
        conversation.assigned_at = datetime.now()
        conversation.save()
        
        availability.increment_conversations()
        
        # Send system message
        ConversationMessage.objects.create(
            conversation=conversation,
            sender_role='system',
            message=f"{availability.teacher.user.get_full_name()} has joined the conversation."
        )
        return True
    
    # No teacher available - send bot message
    ConversationMessage.objects.create(
        conversation=conversation,
        sender_role='bot',
        message="Thank you for your message. All teachers are currently busy. Someone will respond to you shortly!"
    )
    
    return False


@login_required
@require_http_methods(["GET"])
def recent_conversations_api(request):
    """Get recent conversations for navbar dropdown"""
    if request.user.role != 'parent':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    parent = request.user.parent_profile
    
    # Get recent conversations (last 5)
    conversations = ChatConversation.objects.filter(
        parent=parent
    ).order_by('-updated_at')[:5]
    
    # Count unread messages
    unread_count = ConversationMessage.objects.filter(
        conversation__parent=parent,
        sender_role='teacher',
        is_read=False
    ).count()
    
    conversation_list = []
    for conv in conversations:
        last_msg = conv.get_last_message()
        
        # Count unread for this conversation
        conv_unread = conv.conversation_messages.filter(
            sender_role='teacher',
            is_read=False
        ).count()
        
        conversation_list.append({
            'id': conv.id,
            'subject': conv.subject,
            'teacher_name': conv.teacher.user.get_full_name() if conv.teacher else None,
            'status': conv.status,
            'last_message_preview': last_msg.message[:50] + '...' if last_msg and len(last_msg.message) > 50 else (last_msg.message if last_msg else 'No messages yet'),
            'time_ago': timesince(conv.updated_at) + ' ago',
            'unread_count': conv_unread,
        })
    
    return JsonResponse({
        'conversations': conversation_list,
        'unread_count': unread_count
    })


@login_required
@require_http_methods(["GET"])
def conversation_stats_api(request):
    """Get conversation statistics for parent"""
    if request.user.role != 'parent':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    parent = request.user.parent_profile
    
    total = ChatConversation.objects.filter(parent=parent).count()
    active = ChatConversation.objects.filter(
        parent=parent, 
        status__in=['waiting', 'active']
    ).count()
    closed = ChatConversation.objects.filter(
        parent=parent, 
        status='closed'
    ).count()
    unread = ConversationMessage.objects.filter(
        conversation__parent=parent,
        sender_role='teacher',
        is_read=False
    ).count()
    
    return JsonResponse({
        'total': total,
        'active': active,
        'closed': closed,
        'unread': unread
    })