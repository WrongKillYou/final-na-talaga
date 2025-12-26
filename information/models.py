# information/models.py
# CLEANED - Removed redundant chat systems, kept only one unified approach

from django.db import models
from django.conf import settings
from django.utils import timezone
from users.models import User, Teacher, Parent, Child


# ========================================
# EVENTS
# ========================================
# models.py
from django.db import models
from django.utils import timezone

class Event(models.Model):
    """One-time school event"""

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # Event schedule
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField(null=True, blank=True)

    # Location
    location = models.CharField(max_length=200, blank=True)
    venue_details = models.TextField(blank=True)

    # Visibility
    is_public = models.BooleanField(default=True)
    target_audience = models.CharField(max_length=100, default='all')  # e.g., all, teacher, student

    # Organizer
    created_by = models.ForeignKey(
        'users.Teacher',  # adjust if your teacher model is elsewhere
        on_delete=models.SET_NULL,
        null=True
    )

    # Attachments
    image = models.ImageField(upload_to='events/', null=True, blank=True)
    attachment = models.FileField(upload_to='event_files/', null=True, blank=True)

    # Status
    is_active = models.BooleanField(default=True)
    is_cancelled = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_datetime']

    def __str__(self):
        return self.title

    def is_upcoming(self):
        """Check if the event is upcoming and not cancelled"""
        return self.start_datetime >= timezone.now() and not self.is_cancelled




# ========================================
# ANNOUNCEMENTS
# ========================================

class Announcement(models.Model):
    """General announcements for parents and teachers"""
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    CATEGORY_CHOICES = [
        ('academic', 'Academic'),
        ('administrative', 'Administrative'),
        ('health', 'Health & Safety'),
        ('event', 'Event'),
        ('general', 'General'),
    ]
    
    title = models.CharField(max_length=255)
    content = models.TextField()
    category = models.CharField(
        max_length=20, 
        choices=CATEGORY_CHOICES, 
        default='general'
    )
    priority = models.CharField(
        max_length=10, 
        choices=PRIORITY_CHOICES, 
        default='normal'
    )
    
    # Targeting
    target_audience = models.CharField(
        max_length=200, 
        default='all',
        help_text="all, parents, teachers"
    )
    
    # Author
    teacher = models.ForeignKey(
        Teacher, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='announcements'
    )
    
    # Attachments
    image = models.ImageField(
        upload_to='announcements/images/', 
        null=True, 
        blank=True, 
        help_text='Banner image for announcement'
    )
    attachment = models.FileField(
        upload_to='announcement_files/', 
        null=True, 
        blank=True
    )
    
    # Importance and Visibility
    is_important = models.BooleanField(
        default=False, 
        help_text='Mark as important announcement'
    )
    is_pinned = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Publishing
    publish_date = models.DateTimeField(default=timezone.now)
    scheduled_publish = models.DateTimeField(null=True, blank=True)
    expiry_date = models.DateTimeField(null=True, blank=True)
    
    # Engagement
    views_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_pinned', '-priority', '-publish_date']
        verbose_name = "Announcement"
        verbose_name_plural = "Announcements"
        indexes = [
            models.Index(fields=['-publish_date', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.priority}"
    
    def is_expired(self):
        if self.expiry_date:
            return timezone.now() > self.expiry_date
        return False
    
    def is_published(self):
        """Check if announcement should be visible"""
        if not self.is_active:
            return False
        if self.scheduled_publish and timezone.now() < self.scheduled_publish:
            return False
        if self.is_expired():
            return False
        return True


class AnnouncementRead(models.Model):
    """Track which users have read announcements"""
    announcement = models.ForeignKey(
        Announcement, 
        on_delete=models.CASCADE, 
        related_name='reads'
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['announcement', 'user']
        verbose_name = "Announcement Read"
        verbose_name_plural = "Announcement Reads"


# ========================================
# CHATBOT SYSTEM
# ========================================

class BotMessage(models.Model):
    """Predetermined chatbot responses for FAQs"""
    CATEGORY_CHOICES = [
        ('greeting', 'Greeting'),
        ('faq', 'Frequently Asked Questions'),
        ('enrollment', 'Enrollment'),
        ('records', 'Student Records'),
        ('attendance', 'Attendance'),
        ('schedule', 'Schedule'),
        ('contact', 'Contact Information'),
        ('general', 'General'),
    ]
    
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    
    # Trigger keywords (comma-separated)
    keywords = models.TextField(
        help_text="Comma-separated keywords that trigger this response"
    )
    
    # Response
    response_text = models.TextField()
    
    # Optional structured response
    has_buttons = models.BooleanField(default=False)
    button_options = models.JSONField(
        null=True, 
        blank=True,
        help_text="JSON array of button options"
    )
    
    # Priority (higher number = higher priority)
    priority = models.PositiveIntegerField(default=0)
    
    # Usage tracking
    usage_count = models.PositiveIntegerField(default=0)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-priority', 'category']
        verbose_name = "Bot Message"
        verbose_name_plural = "Bot Messages"
    
    def __str__(self):
        return f"{self.category} - {self.keywords[:50]}"
    
    def get_keywords_list(self):
        """Return list of keywords"""
        return [k.strip().lower() for k in self.keywords.split(',')]


# ========================================
# CHATROOM SYSTEM (Parent-Teacher Communication)
# ========================================

class ChatConversation(models.Model):
    """
    Chat conversation between parent and teacher
    Initiated when parent needs help beyond chatbot FAQs
    """
    STATUS_CHOICES = [
        ('waiting', 'Waiting for Teacher'),
        ('active', 'Active Conversation'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    parent = models.ForeignKey(
        Parent, 
        on_delete=models.CASCADE, 
        related_name='chat_conversations'
    )
    teacher = models.ForeignKey(
        Teacher, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='chat_conversations'
    )
    child = models.ForeignKey(
        Child, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='chat_conversations',
        help_text="Specific child this conversation is about"
    )
    
    subject = models.CharField(max_length=200)
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='waiting'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    assigned_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Track who's waiting for response
    parent_waiting = models.BooleanField(default=False)
    teacher_waiting = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = "Chat Conversation"
        verbose_name_plural = "Chat Conversations"
        indexes = [
            models.Index(fields=['parent', '-updated_at']),
            models.Index(fields=['teacher', 'status']),
        ]
    
    def __str__(self):
        teacher_name = self.teacher.user.get_full_name() if self.teacher else "Unassigned"
        return f"Chat: {self.subject} - {self.parent.user.get_full_name()} ↔ {teacher_name}"
    
    def get_last_message(self):
        """Get the most recent message"""
        return self.messages.order_by('-timestamp').first()
    
    def mark_as_read_by_teacher(self):
        """Mark all unread messages as read by teacher"""
        self.messages.filter(
            sender_role='parent', 
            is_read=False
        ).update(is_read=True, read_at=timezone.now())
        
        self.teacher_waiting = False
        self.parent_waiting = True
        self.save()
    
    def mark_as_read_by_parent(self):
        """Mark all unread messages as read by parent"""
        self.messages.filter(
            sender_role='teacher', 
            is_read=False
        ).update(is_read=True, read_at=timezone.now())
        
        self.parent_waiting = False
        self.teacher_waiting = True
        self.save()
    
    def get_unread_count_for_parent(self):
        """Get unread message count for parent"""
        return self.messages.filter(
            sender_role='teacher',
            is_read=False
        ).count()
    
    def get_unread_count_for_teacher(self):
        """Get unread message count for teacher"""
        return self.messages.filter(
            sender_role='parent',
            is_read=False
        ).count()


class ConversationMessage(models.Model):
    """Individual messages in a chat conversation"""
    SENDER_CHOICES = [
        ('parent', 'Parent'),
        ('teacher', 'Teacher'),
        ('system', 'System'),
        ('bot', 'Bot'),
    ]
    
    conversation = models.ForeignKey(
        ChatConversation, 
        on_delete=models.CASCADE, 
        related_name='messages'
    )
    sender_role = models.CharField(max_length=20, choices=SENDER_CHOICES)
    sender_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Attachments (optional)
    attachment = models.FileField(
        upload_to='chat_attachments/', 
        null=True, 
        blank=True
    )
    
    class Meta:
        ordering = ['timestamp']
        verbose_name = "Conversation Message"
        verbose_name_plural = "Conversation Messages"
        indexes = [
            models.Index(fields=['conversation', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.sender_role}: {self.message[:50]}"
    
    def mark_as_read(self):
        """Mark this message as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()


# ========================================
# NOTIFICATIONS
# ========================================

class Notification(models.Model):
    """Notification system for parents and teachers"""
    NOTIFICATION_TYPES = [
        ('competency_posted', 'Competency Record Posted'),
        ('attendance_alert', 'Attendance Alert'),
        ('new_announcement', 'New Announcement'),
        ('new_event', 'New Event'),
        ('new_message', 'New Message'),
        ('general', 'General'),
    ]
    
    recipient = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    notification_type = models.CharField(
        max_length=30, 
        choices=NOTIFICATION_TYPES
    )
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Link to related object (optional)
    link_url = models.CharField(max_length=500, blank=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['recipient', 'is_read']),
        ]
    
    def __str__(self):
        return f"{self.recipient.get_full_name()} - {self.title}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()


# ========================================
# ACTIVITY LOG
# ========================================

class Activity(models.Model):
    """Track user activities for recent activity feed"""
    ACTIVITY_TYPES = [
        ('competency', 'Competency Record Entry'),
        ('attendance', 'Attendance Record'),
        ('announcement', 'Announcement'),
        ('message', 'Message Sent'),
        ('event', 'Event'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='activities'
    )
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    description = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    
    # Optional link to related object
    related_object_id = models.IntegerField(null=True, blank=True)
    related_object_type = models.CharField(max_length=50, null=True, blank=True)
    
    class Meta:
        verbose_name_plural = 'Activities'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.activity_type} - {self.timestamp}"
    
    @classmethod
    def log_activity(cls, user, activity_type, description, related_id=None, related_type=None):
        """Helper method to log an activity"""
        return cls.objects.create(
            user=user,
            activity_type=activity_type,
            description=description,
            related_object_id=related_id,
            related_object_type=related_type
        )