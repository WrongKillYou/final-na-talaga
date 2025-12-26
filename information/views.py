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
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Event
from datetime import date

@login_required
def event_list(request):
    """List all upcoming one-time events"""
    # Get active, non-cancelled events that start today or later
    events = Event.objects.filter(
        is_active=True,
        is_cancelled=False,
        start_datetime__date__gte=date.today()
    ).order_by('start_datetime')
    
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
    """Show full details of an event."""
    event = get_object_or_404(Event, id=event_id, is_active=True)
    return render(request, 'information/event_detail.html', {'event': event})

@login_required
@teacher_required
def event_edit(request, event_id):
    """Edit an event."""
    event = get_object_or_404(Event, id=event_id, is_active=True)
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, 'Event updated successfully!')
            return redirect('users:teacher_dashboard')
    else:
        form = EventForm(instance=event)
    return render(request, 'information/event_form.html', {'form': form, 'event': event})

@login_required
@teacher_required
def event_delete(request, event_id):
    """Soft delete an event."""
    event = get_object_or_404(Event, id=event_id, is_active=True)
    if request.method == 'POST':
        event.is_active = False
        event.save()
        messages.success(request, 'Event deleted successfully!')
        return redirect('users:teacher_dashboard')
    return render(request, 'information/event_confirm_delete.html', {'event': event})



from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import EventForm
from .models import Event
@login_required
@teacher_required
def create_event(request):
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
            return redirect('users:teacher_dashboard')
        else:
            messages.error(request, "⚠️ There was a problem with your submission. Please check the form.")
    else:
        form = EventForm()

    return render(request, 'information/create_event.html', {'form': form, 'teacher': teacher})





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
        return redirect('users:teacher_dashboard')
    
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



@login_required
@parent_required
def parent_announcement_detail(request, pk):
    announcement = get_object_or_404(
        Announcement,
        id=pk,
        is_active=True
    )

    return render(
        request,
        'information/parent_announcement_detail.html',
        {'announcement': announcement}
    )


@login_required
@parent_required
def parent_event_detail(request, pk):
    event = get_object_or_404(
        Event,
        id=pk,
        is_active=True
    )

    return render(
        request,
        'information/parent_event_detail.html',
        {'event': event}
    )


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
