# information/admin.py
# Add these admin configurations to your existing information app admin

from django.contrib import admin
from .models import (
    ChatConversation, ConversationMessage, BotMessage,
    Announcement, AnnouncementRead, Event, Notification, Activity
)


# ==================== CHATBOT ADMIN ====================

@admin.register(BotMessage)
class BotMessageAdmin(admin.ModelAdmin):
    list_display = ['category', 'keywords', 'priority', 'usage_count', 'is_active']
    list_filter = ['category', 'is_active', 'has_buttons']
    search_fields = ['keywords', 'response_text']
    ordering = ['-priority', 'category']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('category', 'keywords', 'priority')
        }),
        ('Response', {
            'fields': ('response_text', 'has_buttons', 'button_options')
        }),
        ('Status & Stats', {
            'fields': ('is_active', 'usage_count')
        }),
    )


# ==================== CHAT CONVERSATION ADMIN ====================

class ConversationMessageInline(admin.TabularInline):
    model = ConversationMessage
    extra = 0
    readonly_fields = ['sender_role', 'sender_user', 'timestamp', 'is_read']
    fields = ['sender_role', 'sender_user', 'message', 'timestamp', 'is_read']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ChatConversation)
class ChatConversationAdmin(admin.ModelAdmin):
    list_display = [
        'subject', 'parent_name', 'teacher_name', 'child_name', 
        'status', 'created_at', 'unread_parent', 'unread_teacher'
    ]
    list_filter = ['status', 'created_at', 'parent_waiting', 'teacher_waiting']
    search_fields = [
        'subject', 'parent__user__first_name', 'parent__user__last_name',
        'teacher__user__first_name', 'teacher__user__last_name',
        'child__first_name', 'child__last_name'
    ]
    readonly_fields = ['created_at', 'updated_at', 'assigned_at', 'resolved_at']
    inlines = [ConversationMessageInline]
    
    fieldsets = (
        ('Participants', {
            'fields': ('parent', 'teacher', 'child')
        }),
        ('Conversation Details', {
            'fields': ('subject', 'status')
        }),
        ('Status', {
            'fields': ('parent_waiting', 'teacher_waiting')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'assigned_at', 'resolved_at'),
            'classes': ('collapse',)
        }),
    )
    
    def parent_name(self, obj):
        return obj.parent.user.get_full_name()
    parent_name.short_description = 'Parent'
    
    def teacher_name(self, obj):
        return obj.teacher.user.get_full_name() if obj.teacher else 'Unassigned'
    teacher_name.short_description = 'Teacher'
    
    def child_name(self, obj):
        return obj.child.get_full_name() if obj.child else 'N/A'
    child_name.short_description = 'Child'
    
    def unread_parent(self, obj):
        return obj.get_unread_count_for_parent()
    unread_parent.short_description = 'Parent Unread'
    
    def unread_teacher(self, obj):
        return obj.get_unread_count_for_teacher()
    unread_teacher.short_description = 'Teacher Unread'


@admin.register(ConversationMessage)
class ConversationMessageAdmin(admin.ModelAdmin):
    list_display = [
        'conversation_subject', 'sender_role', 'sender_name', 
        'message_preview', 'timestamp', 'is_read'
    ]
    list_filter = ['sender_role', 'is_read', 'timestamp']
    search_fields = [
        'message', 'conversation__subject',
        'sender_user__first_name', 'sender_user__last_name'
    ]
    readonly_fields = ['timestamp', 'read_at']
    
    fieldsets = (
        ('Conversation', {
            'fields': ('conversation',)
        }),
        ('Sender', {
            'fields': ('sender_role', 'sender_user')
        }),
        ('Message', {
            'fields': ('message', 'attachment')
        }),
        ('Status', {
            'fields': ('is_read', 'read_at', 'timestamp')
        }),
    )
    
    def conversation_subject(self, obj):
        return obj.conversation.subject
    conversation_subject.short_description = 'Conversation'
    
    def sender_name(self, obj):
        return obj.sender_user.get_full_name() if obj.sender_user else obj.sender_role.title()
    sender_name.short_description = 'Sender'
    
    def message_preview(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Message'


# ==================== ANNOUNCEMENT ADMIN ====================

class AnnouncementReadInline(admin.TabularInline):
    model = AnnouncementRead
    extra = 0
    readonly_fields = ['user', 'read_at']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'category', 'priority', 'is_pinned', 
        'is_active', 'publish_date', 'views_count'
    ]
    list_filter = [
        'category', 'priority', 'is_pinned', 'is_active', 
        'publish_date', 'target_audience'
    ]
    search_fields = ['title', 'content']
    readonly_fields = ['views_count', 'created_at', 'updated_at']
    inlines = [AnnouncementReadInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'content', 'category', 'priority')
        }),
        ('Author', {
            'fields': ('teacher',)
        }),
        ('Targeting & Visibility', {
            'fields': ('target_audience', 'is_important', 'is_pinned', 'is_active')
        }),
        ('Publishing', {
            'fields': ('publish_date', 'scheduled_publish', 'expiry_date')
        }),
        ('Attachments', {
            'fields': ('image', 'attachment'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('views_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new
            try:
                obj.teacher = request.user.teacher_profile
            except:
                pass
        super().save_model(request, obj, form, change)


# ==================== EVENT ADMIN ====================

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'start_datetime', 'end_datetime', 
        'location', 'is_active', 'is_cancelled', 'target_audience'
    ]
    list_filter = ['is_active', 'is_cancelled', 'target_audience', 'start_datetime']
    search_fields = ['title', 'description', 'location']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description')
        }),
        ('Schedule', {
            'fields': ('start_datetime', 'end_datetime')
        }),
        ('Location', {
            'fields': ('location', 'venue_details')
        }),
        ('Organizer', {
            'fields': ('created_by',)
        }),
        ('Visibility', {
            'fields': ('target_audience', 'is_public')
        }),
        ('Attachments', {
            'fields': ('image', 'attachment'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_cancelled')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# ==================== NOTIFICATION ADMIN ====================

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'recipient_name', 'notification_type', 'title', 
        'is_read', 'created_at'
    ]
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = [
        'title', 'message', 
        'recipient__first_name', 'recipient__last_name'
    ]
    readonly_fields = ['created_at', 'read_at']
    
    fieldsets = (
        ('Recipient', {
            'fields': ('recipient',)
        }),
        ('Notification', {
            'fields': ('notification_type', 'title', 'message', 'link_url')
        }),
        ('Status', {
            'fields': ('is_read', 'read_at', 'created_at')
        }),
    )
    
    def recipient_name(self, obj):
        return obj.recipient.get_full_name()
    recipient_name.short_description = 'Recipient'


# ==================== ACTIVITY ADMIN ====================

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = [
        'user_name', 'activity_type', 'description', 'timestamp'
    ]
    list_filter = ['activity_type', 'timestamp']
    search_fields = [
        'description', 'user__first_name', 'user__last_name'
    ]
    readonly_fields = ['timestamp']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Activity', {
            'fields': ('activity_type', 'description')
        }),
        ('Related Object', {
            'fields': ('related_object_id', 'related_object_type'),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('timestamp',)
        }),
    )
    
    def user_name(self, obj):
        return obj.user.get_full_name()
    user_name.short_description = 'User'