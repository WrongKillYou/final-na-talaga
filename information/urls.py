from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from information import api_views
from . import views

app_name = 'information'

urlpatterns = [
    # ========================================
    # Events
    # ========================================
    path('events/', views.event_list, name='event_list'),
    path('event/<int:event_id>/', views.event_detail, name='event_detail'),
    path('event/create/', views.create_event, name='create_event'),
    path('event/<int:event_id>/edit/', views.edit_event, name='edit_event'),
    path('event/<int:event_id>/delete/', views.delete_event, name='delete_event'),
    
    #   # Announcements - FIXED NAMES
    path('announcements/', views.announcement_list, name='announcement_list'),
    path('announcement/<int:announcement_id>/', views.announcement_detail, name='announcement_detail'),
    path('announcement/create/', views.create_announcement, name='create_announcement'),
    path('announcement/<int:announcement_id>/edit/', views.edit_announcement, name='announcement_edit'),  # Changed name
    path('announcement/<int:announcement_id>/delete/', views.delete_announcement, name='announcement_delete'),  # Changed name
    # ========================================
    # Chat System
    # ========================================
    path('chat/', views.chat_list, name='chat_list'),
    path('chat/<int:room_id>/', views.chat_room, name='chat_room'),
    path('chat/start/<int:teacher_id>/', views.start_chat, name='start_chat'),
    path('chat/<int:room_id>/send/', views.send_message, name='send_message'),
    path('chat/<int:room_id>/mark-read/', views.mark_messages_read, name='mark_messages_read'),
    
    # ========================================
    # Notifications
    # ========================================
    path('notifications/', views.notification_list, name='notification_list'),
    path('notification/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    
    # ========================================
    # Chatbot
    # ========================================
    path('chatbot/', views.chatbot, name='chatbot'),
    path('chatbot/query/', views.chatbot_query, name='chatbot_query'),

   
    # API Endpoints
    path('api/announcements/recent/', api_views.recent_announcements_api, name='api_recent_announcements'),
    path('api/events/upcoming/', api_views.upcoming_events_api, name='api_upcoming_events'),
    path('api/children/', api_views.parent_children_api, name='api_parent_children'),
    path('api/children/<int:child_id>/schedule/', api_views.child_schedule_api, name='api_child_schedule'),
     path('api/chat/recent-conversations/', views.recent_conversations_api, name='recent_conversations'),
    
    # Live Chat API
    path('api/chat/conversations/', api_views.parent_conversations_api, name='api_parent_conversations'),
    path('api/chat/conversations/create/', api_views.create_conversation_api, name='api_create_conversation'),
    path('api/chat/conversations/<int:conversation_id>/messages/', api_views.conversation_messages_api, name='api_conversation_messages'),
    path('api/chat/conversations/<int:conversation_id>/send/', api_views.send_message_api, name='api_send_message'),
    path('api/chat/conversations/<int:conversation_id>/close/', api_views.close_conversation_api, name='api_close_conversation'),
    path('api/chat/teacher/inbox/', api_views.teacher_inbox_api, name='api_teacher_inbox'),
    path('api/chat/unread-count/', api_views.unread_count_api, name='api_unread_count'),

    # Chat History
    path('chat/history/', views.chat_history, name='chat_history'),
    path('chat/conversation/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('chat/conversation/<int:conversation_id>/send/', views.send_conversation_message, name='send_conversation_message'),
    path('chat/conversation/<int:conversation_id>/delete/', views.delete_conversation, name='delete_conversation'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)