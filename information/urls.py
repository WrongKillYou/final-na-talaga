# information/urls.py
# URL Configuration for INFORMATION App - Unified Chat System

from django.urls import path
from . import views

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
    
    # ========================================
    # CHATBOT (FAQ System)
    # ========================================
    path('chatbot/', 
         views.chatbot, 
         name='chatbot'),
    
    path('chatbot/query/', 
         views.chatbot_query, 
         name='chatbot_query'),
    
    # ========================================
    # CHAT CONVERSATIONS (Parent-Teacher)
    # ========================================
    path('chat/start/', 
         views.start_conversation, 
         name='start_conversation'),
    
    path('chat/history/', 
         views.chat_history, 
         name='chat_history'),
    
    path('conversation/<int:conversation_id>/', 
         views.conversation_detail, 
         name='conversation_detail'),
    
    path('conversation/<int:conversation_id>/send/', 
         views.send_conversation_message, 
         name='send_conversation_message'),
    
    path('conversation/<int:conversation_id>/close/', 
         views.close_conversation, 
         name='close_conversation'),
    
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
]