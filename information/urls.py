# information/urls.py
# URL Configuration for INFORMATION App - Unified Chat System

from django.urls import path
from . import views, api_views

app_name = 'information'

urlpatterns = [
    # ========================================
    # EVENTS
    # ========================================
    path('events/', 
         views.event_list, 
         name='event_list'),
    
    path('event/<int:event_id>/', 
         views.event_detail, 
         name='event_detail'),
    
    path('event/create/', 
         views.create_event, 
         name='create_event'),
    
    path('event/<int:event_id>/edit/', 
         views.edit_event, 
         name='edit_event'),
    
    path('event/<int:event_id>/delete/', 
         views.delete_event, 
         name='delete_event'),
    
    # ========================================
    # ANNOUNCEMENTS
    # ========================================
    path('announcements/', 
         views.announcement_list, 
         name='announcement_list'),
    
    path('announcement/<int:announcement_id>/', 
         views.announcement_detail, 
         name='announcement_detail'),
    
    path('announcement/create/', 
         views.create_announcement, 
         name='create_announcement'),
    
    path('announcement/<int:announcement_id>/edit/', 
         views.edit_announcement, 
         name='edit_announcement'),
    
    path('announcement/<int:announcement_id>/delete/', 
         views.delete_announcement, 
         name='delete_announcement'),




     path(
        'parent/announcement/<int:pk>/',
        views.parent_announcement_detail,
        name='parent_announcement_detail'
    ),
    path(
        'parent/event/<int:pk>/',
        views.parent_event_detail,
        name='parent_event_detail'
    ),
    
    
    
    # ========================================
    # NOTIFICATIONS
    # ========================================
    path('notifications/', 
         views.notification_list, 
         name='notification_list'),
    
    path('notification/<int:notification_id>/read/', 
         views.mark_notification_read, 
         name='mark_notification_read'),
    
    path('notifications/read-all/', 
         views.mark_all_notifications_read, 
         name='mark_all_notifications_read'),
    
    # API Endpoints (AJAX)
    path('api/notifications/count/', 
         views.get_unread_notifications_count, 
         name='get_unread_notifications_count'),

     path('api/chat/conversations/', 
         api_views.get_parent_conversations, 
         name='api_parent_conversations'),
    
    path('api/chat/teacher-conversations/', 
         api_views.get_teacher_conversations, 
         name='api_teacher_conversations'),
    
    # Get messages in a conversation
    path('api/chat/conversation/<int:conversation_id>/messages/', 
         api_views.get_conversation_messages, 
         name='api_conversation_messages'),
    
    # Send message
    path('api/chat/conversation/<int:conversation_id>/send/', 
         api_views.send_message, 
         name='api_send_message'),
    
    # Get available teachers
    path('api/chat/available-teachers/', 
         api_views.get_available_teachers, 
         name='api_available_teachers'),
    
    # Create new conversation
    path('api/chat/create-conversation/', 
         api_views.create_conversation, 
         name='api_create_conversation'),
    
    # Get unread count
    path('api/chat/unread-count/', 
         api_views.get_unread_count, 
         name='api_unread_count'),
    
    # Search bot response
    path('api/chat/bot-search/', 
         api_views.search_bot_response, 
         name='api_bot_search'),
    
    # Mark conversation as resolved
    path('api/chat/conversation/<int:conversation_id>/resolve/', 
         api_views.mark_conversation_resolved, 
         name='api_resolve_conversation'),

]