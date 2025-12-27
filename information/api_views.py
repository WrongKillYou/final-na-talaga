# information/api_views.py
# Chat API endpoints for KinderCare Messenger system

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q, Max, Count
import json

from .models import ChatConversation, ConversationMessage, Notification, BotMessage
from users.models import Teacher, Parent, Child


# ==================== GET CONVERSATIONS ====================

@login_required
@require_http_methods(["GET"])
def get_parent_conversations(request):
    """Get all conversations for a parent (teacher conversations only)"""
    try:
        parent = request.user.parent_profile
    except:
        return JsonResponse({'error': 'Not a parent'}, status=403)
    
    conversations = ChatConversation.objects.filter(
        parent=parent
    ).select_related('teacher__user', 'child').order_by('-updated_at')
    
    data = []
    for conv in conversations:
        last_msg = conv.get_last_message()
        data.append({
            'id': str(conv.id),
            'teacher_name': conv.teacher.user.get_full_name() if conv.teacher else 'Unassigned',
            'section': conv.teacher.department if conv.teacher else '',
            'child_name': conv.child.get_full_name() if conv.child else 'General',
            'subject': conv.subject,
            'status': conv.status,
            'unread_count': conv.get_unread_count_for_parent(),
            'last_message': last_msg.message if last_msg else '',
            'last_message_time': last_msg.timestamp.strftime('%I:%M %p') if last_msg else '',
        })
    
    return JsonResponse({'conversations': data})


@login_required
@require_http_methods(["GET"])
def get_teacher_conversations(request):
    """Get all conversations for a teacher (parent conversations)"""
    try:
        teacher = request.user.teacher_profile
    except:
        return JsonResponse({'error': 'Not a teacher'}, status=403)
    
    conversations = ChatConversation.objects.filter(
        Q(teacher=teacher) | Q(teacher__isnull=True, status='waiting')
    ).select_related('parent__user', 'child').order_by('-updated_at')
    
    data = []
    for conv in conversations:
        last_msg = conv.get_last_message()
        data.append({
            'id': str(conv.id),
            'parent_name': conv.parent.user.get_full_name(),
            'child_name': conv.child.get_full_name() if conv.child else 'General',
            'subject': conv.subject,
            'status': conv.status,
            'unread_count': conv.get_unread_count_for_teacher(),
            'last_message': last_msg.message if last_msg else '',
            'last_message_time': last_msg.timestamp.strftime('%I:%M %p') if last_msg else '',
        })
    
    return JsonResponse({'conversations': data})


# ==================== GET MESSAGES ====================

@login_required
@require_http_methods(["GET"])
def get_conversation_messages(request, conversation_id):
    """Get all messages in a conversation"""
    try:
        conversation = ChatConversation.objects.get(id=conversation_id)
        
        # Check permission
        if request.user.role == 'parent':
            if conversation.parent.user != request.user:
                return JsonResponse({'error': 'Not authorized'}, status=403)
            # Mark as read by parent
            conversation.mark_as_read_by_parent()
        elif request.user.role == 'teacher':
            if conversation.teacher and conversation.teacher.user != request.user:
                return JsonResponse({'error': 'Not authorized'}, status=403)
            # Mark as read by teacher
            conversation.mark_as_read_by_teacher()
        
    except ChatConversation.DoesNotExist:
        return JsonResponse({'error': 'Conversation not found'}, status=404)
    
    messages = conversation.messages.all().order_by('timestamp')
    
    data = []
    for msg in messages:
        message_data = {
            'id': msg.id,
            'sender_role': msg.sender_role,
            'sender_name': msg.sender_user.get_full_name() if msg.sender_user else 'System',
            'message': msg.message,
            'timestamp': msg.timestamp.strftime('%I:%M %p'),
            'is_read': msg.is_read,
        }
        
        # Add attachment info if present
        if msg.attachment:
            message_data['attachment_url'] = msg.attachment.url
            # Determine attachment type from file extension
            if msg.attachment.name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                message_data['attachment_type'] = 'image'
            elif msg.attachment.name.lower().endswith(('.mp4', '.mov')):
                message_data['attachment_type'] = 'video'
        
        data.append(message_data)
    
    return JsonResponse({'messages': data})


# ==================== SEND MESSAGE ====================

@login_required
@require_http_methods(["POST"])
def send_message(request, conversation_id):
    """Send a message in a conversation"""
    try:
        # Handle both JSON and FormData
        if request.content_type and 'multipart/form-data' in request.content_type:
            message_text = request.POST.get('message', '').strip()
            attachment = request.FILES.get('attachment')
        else:
            data = json.loads(request.body)
            message_text = data.get('message', '').strip()
            attachment = None
        
        if not message_text and not attachment:
            return JsonResponse({'error': 'Message or attachment required'}, status=400)
        
        conversation = ChatConversation.objects.get(id=conversation_id)
        
        # Determine sender role
        if request.user.role == 'parent':
            if conversation.parent.user != request.user:
                return JsonResponse({'error': 'Not authorized'}, status=403)
            sender_role = 'parent'
            # Update conversation status
            conversation.teacher_waiting = True
            conversation.parent_waiting = False
            
        elif request.user.role == 'teacher':
            if conversation.teacher and conversation.teacher.user != request.user:
                return JsonResponse({'error': 'Not authorized'}, status=403)
            sender_role = 'teacher'
            # Assign teacher if not assigned
            if not conversation.teacher:
                conversation.teacher = request.user.teacher_profile
                conversation.assigned_at = timezone.now()
                conversation.status = 'active'
            # Update conversation status
            conversation.parent_waiting = True
            conversation.teacher_waiting = False
        else:
            return JsonResponse({'error': 'Invalid role'}, status=403)
        
        # Create message
        message = ConversationMessage.objects.create(
            conversation=conversation,
            sender_role=sender_role,
            sender_user=request.user,
            message=message_text or '📎 Attachment',
            attachment=attachment
        )
        
        conversation.updated_at = timezone.now()
        conversation.save()
        
        # Create notification for recipient
        if sender_role == 'parent' and conversation.teacher:
            Notification.objects.create(
                recipient=conversation.teacher.user,
                notification_type='new_message',
                title='New Message from Parent',
                message=f'{request.user.get_full_name()}: {message_text[:50]}...' if message_text else 'Sent an attachment',
                link_url=f'/teacher/messages/{conversation.id}/'
            )
        elif sender_role == 'teacher':
            Notification.objects.create(
                recipient=conversation.parent.user,
                notification_type='new_message',
                title='New Message from Teacher',
                message=f'{request.user.get_full_name()}: {message_text[:50]}...' if message_text else 'Sent an attachment',
                link_url=f'/parent/messages/{conversation.id}/'
            )
        
        return JsonResponse({
            'success': True,
            'message_id': message.id,
            'timestamp': message.timestamp.strftime('%I:%M %p')
        })
        
    except ChatConversation.DoesNotExist:
        return JsonResponse({'error': 'Conversation not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        print(f"Send message error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


# ==================== GET AVAILABLE TEACHERS ====================

@login_required
@require_http_methods(["GET"])
def get_available_teachers(request):
    """Get list of ALL active teachers that parent can contact"""
    try:
        parent = request.user.parent_profile
    except:
        return JsonResponse({'error': 'Not a parent'}, status=403)
    
    # Get ALL active teachers
    teachers = Teacher.objects.filter(
        is_active=True
    ).select_related('user').order_by('user__last_name', 'user__first_name')
    
    data = []
    for teacher in teachers:
        # Get section info from classes
        from monitoring.models import Class
        classes = Class.objects.filter(teacher=teacher, is_active=True)
        
        # Get section name or use department
        if classes.exists():
            section = classes.first().class_name
        else:
            section = teacher.department
        
        data.append({
            'id': teacher.id,
            'name': teacher.user.get_full_name(),
            'section': section,
            'department': teacher.department,
        })
    
    return JsonResponse({'teachers': data})


# ==================== CREATE CONVERSATION ====================

@login_required
@require_http_methods(["POST"])
def create_conversation(request):
    """Create a new conversation between parent and teacher"""
    try:
        parent = request.user.parent_profile
    except:
        return JsonResponse({'error': 'Not a parent'}, status=403)
    
    try:
        data = json.loads(request.body)
        teacher_id = data.get('teacher_id')
        
        if not teacher_id:
            return JsonResponse({'error': 'Teacher ID required'}, status=400)
        
        teacher = Teacher.objects.get(id=teacher_id, is_active=True)
        
        # Get parent's child in teacher's class (if any)
        from monitoring.models import Class, Enrollment
        child = None
        teacher_classes = Class.objects.filter(teacher=teacher, is_active=True)
        for tc in teacher_classes:
            enrollment = Enrollment.objects.filter(
                class_obj=tc,
                student__in=parent.children.all(),
                is_active=True
            ).first()
            if enrollment:
                child = enrollment.student
                break
        
        # Check if conversation already exists
        existing = ChatConversation.objects.filter(
            parent=parent,
            teacher=teacher,
            status__in=['waiting', 'active']
        ).first()
        
        if existing:
            return JsonResponse({
                'success': True,
                'conversation_id': str(existing.id),
                'exists': True
            })
        
        # Create new conversation
        conversation = ChatConversation.objects.create(
            parent=parent,
            teacher=teacher,
            child=child,
            subject='General Inquiry',
            status='active',
            assigned_at=timezone.now(),
            teacher_waiting=True,
            parent_waiting=False
        )
        
        # Create initial system message
        ConversationMessage.objects.create(
            conversation=conversation,
            sender_role='system',
            message=f'Conversation started with {teacher.user.get_full_name()}'
        )
        
        # Notify teacher
        Notification.objects.create(
            recipient=teacher.user,
            notification_type='new_message',
            title='New Conversation Request',
            message=f'{parent.user.get_full_name()} wants to connect with you',
            link_url=f'/teacher/messages/{conversation.id}/'
        )
        
        return JsonResponse({
            'success': True,
            'conversation_id': str(conversation.id),
            'exists': False
        })
        
    except Teacher.DoesNotExist:
        return JsonResponse({'error': 'Teacher not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ==================== GET FAQs ====================

@login_required
@require_http_methods(["GET"])
def get_faqs(request):
    """Get all active FAQ bot messages for display"""
    try:
        bot_messages = BotMessage.objects.filter(
            is_active=True
        ).order_by('category', '-priority')
        
        faqs = []
        for bot_msg in bot_messages:
            # Generate question from keywords (take first keyword as question base)
            keywords = bot_msg.get_keywords_list()
            
            # Create a proper question based on category
            if bot_msg.category == 'enrollment':
                if 'payment' in bot_msg.keywords.lower() or 'fee' in bot_msg.keywords.lower():
                    question = 'Do you charge tuition fees?'
                else:
                    question = 'What are your enrollment requirements?'
            elif bot_msg.category == 'schedule':
                question = 'What are your class schedules?'
            elif bot_msg.category == 'attendance':
                question = 'What is your attendance policy?'
            elif bot_msg.category == 'health':
                question = 'What should I do if my child is sick?'
            elif bot_msg.category == 'records':
                question = 'How can I view my child\'s progress?'
            elif bot_msg.category == 'contact':
                if 'teacher' in bot_msg.keywords.lower():
                    question = 'How do I talk to a teacher?'
                elif 'update' in bot_msg.keywords.lower():
                    question = 'How do I update my contact information?'
                else:
                    question = 'How can I contact the center?'
            elif bot_msg.category == 'general':
                if 'bring' in bot_msg.keywords.lower() or 'supplies' in bot_msg.keywords.lower():
                    question = 'What should my child bring?'
                elif 'cancel' in bot_msg.keywords.lower() or 'typhoon' in bot_msg.keywords.lower():
                    question = 'What happens during typhoons?'
                elif 'location' in bot_msg.keywords.lower():
                    question = 'Where is the daycare center located?'
                elif 'curriculum' in bot_msg.keywords.lower():
                    question = 'What is your curriculum?'
                elif 'age' in bot_msg.keywords.lower():
                    question = 'What is the age requirement?'
                else:
                    continue  # Skip other general FAQs
            else:
                continue  # Skip greetings and generic help
            
            faqs.append({
                'id': bot_msg.id,
                'category': bot_msg.category,
                'question': question,
                'answer': bot_msg.response_text,
                'priority': bot_msg.priority
            })
        
        return JsonResponse({'faqs': faqs})
        
    except Exception as e:
        print(f"Get FAQs error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


# ==================== SEARCH BOT RESPONSES ====================

@login_required
@require_http_methods(["POST"])
def search_bot_response(request):
    """Search for bot response based on user message with improved intelligence"""
    try:
        data = json.loads(request.body)
        message = data.get('message', '').strip().lower()
        
        if not message:
            return JsonResponse({'found': False})
        
        # Clean the message
        original_message = message
        
        # Remove common stop words that cause false matches
        stop_words = ['i', 'a', 'an', 'the', 'to', 'for', 'of', 'in', 'on', 'at', 'is', 'am', 'are', 'was', 'were', 'be', 'been', 'being']
        words = [word.strip('.,!?;:') for word in message.split()]
        meaningful_words = [w for w in words if w not in stop_words and len(w) >= 3]
        
        if not meaningful_words:
            return JsonResponse({'found': False})
        
        # Get all active bot messages
        all_bot_messages = BotMessage.objects.filter(is_active=True)
        
        # Score each bot message based on keyword matches
        scored_messages = []
        
        for bot_msg in all_bot_messages:
            score = 0
            keywords = bot_msg.get_keywords_list()
            
            # HIGHEST PRIORITY: Multi-word phrase exact match
            for keyword in keywords:
                if len(keyword.split()) > 1 and keyword in original_message:
                    score += 50  # Very high score for phrase match
            
            # HIGH PRIORITY: Check for exact phrase patterns
            # Special case: "talk to teacher", "speak to teacher", etc.
            if 'teacher' in meaningful_words:
                if any(phrase in original_message for phrase in ['talk to teacher', 'speak to teacher', 'contact teacher', 'message teacher', 'chat with teacher', 'connect with teacher']):
                    if 'teacher' in bot_msg.keywords.lower():
                        score += 100  # Highest priority for teacher contact
            
            # MEDIUM PRIORITY: Exact single word match (but only meaningful words)
            for word in meaningful_words:
                for keyword in keywords:
                    # Exact word match
                    if word == keyword:
                        score += 10
                    # Keyword is part of the word (or vice versa) but must be substantial
                    elif len(word) >= 4 and len(keyword) >= 4:
                        if word in keyword or keyword in word:
                            score += 3
            
            # Bonus for high priority messages
            score += bot_msg.priority * 0.3
            
            if score > 0:
                scored_messages.append((score, bot_msg))
        
        # Sort by score (highest first)
        scored_messages.sort(reverse=True, key=lambda x: x[0])
        
        if scored_messages:
            best_message = scored_messages[0][1]
            best_score = scored_messages[0][0]
            
            # Log for debugging
            print(f"Query: '{message}' -> Matched: '{best_message.category}' with score {best_score}")
            
            # Only return if score is meaningful (> 5)
            if best_score > 5:
                # Increment usage count
                best_message.usage_count += 1
                best_message.save(update_fields=['usage_count'])
                
                return JsonResponse({
                    'found': True,
                    'response': best_message.response_text,
                    'category': best_message.category
                })
        
        return JsonResponse({'found': False})
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        print(f"Bot search error: {str(e)}")  # Debug logging
        return JsonResponse({'error': str(e)}, status=500)


# ==================== GET UNREAD COUNT ====================

@login_required
@require_http_methods(["GET"])
def get_unread_count(request):
    """Get total unread message count for user"""
    try:
        if request.user.role == 'parent':
            parent = request.user.parent_profile
            conversations = ChatConversation.objects.filter(parent=parent)
            total_unread = sum(conv.get_unread_count_for_parent() for conv in conversations)
            
        elif request.user.role == 'teacher':
            teacher = request.user.teacher_profile
            conversations = ChatConversation.objects.filter(
                Q(teacher=teacher) | Q(teacher__isnull=True, status='waiting')
            )
            total_unread = sum(conv.get_unread_count_for_teacher() for conv in conversations)
        else:
            total_unread = 0
        
        return JsonResponse({'unread_count': total_unread})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ==================== GET PROFILE INFO ====================

@login_required
@require_http_methods(["GET"])
def get_parent_profile(request, conversation_id):
    """Get parent profile information for teachers"""
    try:
        teacher = request.user.teacher_profile
    except:
        return JsonResponse({'error': 'Not a teacher'}, status=403)
    
    try:
        conversation = ChatConversation.objects.get(id=conversation_id)
        
        # Verify this is the teacher's conversation
        if conversation.teacher and conversation.teacher != teacher:
            return JsonResponse({'error': 'Not authorized'}, status=403)
        
        parent = conversation.parent
        
        data = {
            'name': parent.user.get_full_name(),
            'email': parent.parent_email,
            'contact': parent.parent_contact,
            'address': parent.address,
            'child_name': conversation.child.get_full_name() if conversation.child else 'N/A',
            'relationship': parent.get_relationship_to_child_display() if hasattr(parent, 'relationship_to_child') else 'Parent',
        }
        
        return JsonResponse(data)
        
    except ChatConversation.DoesNotExist:
        return JsonResponse({'error': 'Conversation not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_teacher_profile(request, conversation_id):
    """Get teacher profile information for parents"""
    try:
        parent = request.user.parent_profile
    except:
        return JsonResponse({'error': 'Not a parent'}, status=403)
    
    try:
        conversation = ChatConversation.objects.get(id=conversation_id)
        
        # Verify this is the parent's conversation
        if conversation.parent != parent:
            return JsonResponse({'error': 'Not authorized'}, status=403)
        
        teacher = conversation.teacher
        
        if not teacher:
            return JsonResponse({'error': 'Teacher not assigned'}, status=404)
        
        # Get section from classes
        from monitoring.models import Class
        classes = Class.objects.filter(teacher=teacher, is_active=True)
        section = classes.first().class_name if classes.exists() else teacher.department
        
        data = {
            'name': teacher.user.get_full_name(),
            'email': teacher.contact_email or teacher.user.email,
            'contact': teacher.contact_number,
            'department': teacher.department,
            'section': section,
            'specialization': teacher.specialization,
        }
        
        return JsonResponse(data)
        
    except ChatConversation.DoesNotExist:
        return JsonResponse({'error': 'Conversation not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ==================== MARK CONVERSATION AS RESOLVED ====================

@login_required
@require_http_methods(["POST"])
def mark_conversation_resolved(request, conversation_id):
    """Mark a conversation as resolved"""
    try:
        conversation = ChatConversation.objects.get(id=conversation_id)
        
        # Only teacher or parent can mark as resolved
        if request.user.role == 'parent':
            if conversation.parent.user != request.user:
                return JsonResponse({'error': 'Not authorized'}, status=403)
        elif request.user.role == 'teacher':
            if conversation.teacher and conversation.teacher.user != request.user:
                return JsonResponse({'error': 'Not authorized'}, status=403)
        else:
            return JsonResponse({'error': 'Not authorized'}, status=403)
        
        conversation.status = 'resolved'
        conversation.resolved_at = timezone.now()
        conversation.save()
        
        return JsonResponse({'success': True})
        
    except ChatConversation.DoesNotExist:
        return JsonResponse({'error': 'Conversation not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)