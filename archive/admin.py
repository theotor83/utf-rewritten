from django.contrib import admin
from django.db.models import Count, Q, Prefetch, Sum, Avg, Max, Min
from django.db.models.functions import Length
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.contrib.admin import SimpleListFilter
from django.utils import timezone
from datetime import datetime, timedelta
import re
from . import models

# Custom filters for enhanced admin functionality

class MessageCountFilter(SimpleListFilter):
    title = 'Message Count Range'
    parameter_name = 'messages'

    def lookups(self, request, model_admin):
        return (
            ('0-10', '0-10 messages'),
            ('11-50', '11-50 messages'),
            ('51-100', '51-100 messages'),
            ('101-500', '101-500 messages'),
            ('500+', '500+ messages'),
        )

    def queryset(self, request, queryset):
        if self.value() == '0-10':
            return queryset.filter(archiveprofile__messages_count__lte=10)
        elif self.value() == '11-50':
            return queryset.filter(archiveprofile__messages_count__range=(11, 50))
        elif self.value() == '51-100':
            return queryset.filter(archiveprofile__messages_count__range=(51, 100))
        elif self.value() == '101-500':
            return queryset.filter(archiveprofile__messages_count__range=(101, 500))
        elif self.value() == '500+':
            return queryset.filter(archiveprofile__messages_count__gt=500)

class TopicActivityFilter(SimpleListFilter):
    title = 'Topic Activity'
    parameter_name = 'activity'

    def lookups(self, request, model_admin):
        return (
            ('active', 'Active (last 30 days)'),
            ('recent', 'Recent (last 7 days)'),
            ('old', 'Old (>90 days)'),
            ('no_replies', 'No replies'),
            ('hot', 'Hot (>10 replies)'),
        )

    def queryset(self, request, queryset):
        now = timezone.now()
        if self.value() == 'active':
            return queryset.filter(last_message_time__gte=now - timedelta(days=30))
        elif self.value() == 'recent':
            return queryset.filter(last_message_time__gte=now - timedelta(days=7))
        elif self.value() == 'old':
            return queryset.filter(last_message_time__lt=now - timedelta(days=90))
        elif self.value() == 'no_replies':
            return queryset.filter(total_replies__lte=0)
        elif self.value() == 'hot':
            return queryset.filter(total_replies__gt=10)

class UserActivityFilter(SimpleListFilter):
    title = 'User Activity'
    parameter_name = 'user_activity'

    def lookups(self, request, model_admin):
        return (
            ('new', 'New users (last 7 days)'),
            ('active', 'Active (has posts)'),
            ('inactive', 'Inactive (no posts)'),
            ('staff', 'Staff members'),
        )

    def queryset(self, request, queryset):
        now = timezone.now()
        if self.value() == 'new':
            return queryset.filter(date_joined__gte=now - timedelta(days=7))
        elif self.value() == 'active':
            return queryset.filter(archive_posts__isnull=False).distinct()
        elif self.value() == 'inactive':
            return queryset.filter(archive_posts__isnull=True)
        elif self.value() == 'staff':
            return queryset.filter(archiveprofile__groups__is_staff_group=True).distinct()

# Enhanced inline classes

class ArchivePostInline(admin.TabularInline):
    model = models.ArchivePost
    extra = 0
    fields = ('text_preview', 'created_time', 'update_count')
    readonly_fields = ('text_preview', 'created_time', 'update_count')
    show_change_link = True
    max_num = 10
    
    def text_preview(self, obj):
        if obj.text:
            clean_text = obj.get_raw_text if hasattr(obj, 'get_raw_text') else obj.text
            return clean_text[:100] + '...' if len(clean_text) > 100 else clean_text
        return 'No content'
    text_preview.short_description = 'Preview'

class ArchiveTopicInline(admin.TabularInline):
    model = models.ArchiveTopic
    extra = 0
    fields = ('title', 'total_replies', 'total_views', 'is_sub_forum', 'is_locked')
    readonly_fields = ('total_replies', 'total_views')
    show_change_link = True
    max_num = 5

# Custom admin configurations for efficient handling of large datasets

class ArchivePollOptionVotersInline(admin.TabularInline):
    model = models.ArchivePollOptionVoters
    extra = 0
    raw_id_fields = ('user',)
    readonly_fields = ('get_user_info',)
    
    def get_user_info(self, obj):
        if obj.user and hasattr(obj.user, 'archiveprofile'):
            profile = obj.user.archiveprofile
            return f"{obj.user.username} ({profile.messages_count} messages)"
        return obj.user.username if obj.user else '-'
    get_user_info.short_description = 'User Info'
    
class ArchiveSmileyCategory_smileysInline(admin.TabularInline):
    model = models.ArchiveSmileyCategory_smileys
    extra = 0
    raw_id_fields = ('smileytag',)
    readonly_fields = ('smiley_preview',)
    
    def smiley_preview(self, obj):
        if obj.smileytag and hasattr(obj.smileytag, 'image_url'):
            return format_html('<img src="{}" style="max-height: 20px;"/>', obj.smileytag.image_url)
        return '-'
    smiley_preview.short_description = 'Preview'

@admin.register(models.FakeUser)
class FakeUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username_with_status', 'email', 'join_date_formatted', 'activity_status',
                   'has_profile', 'profile_messages', 'profile_groups', 'content_summary', 
                   'last_activity', 'user_rank')
    list_filter = ('is_staff', 'is_active', 'date_joined', 'is_authenticated', MessageCountFilter, UserActivityFilter)
    search_fields = ('username', 'email', 'archiveprofile__display_username')
    readonly_fields = ('date_joined', 'activity_status', 'has_profile', 'profile_messages', 'profile_groups',
                      'topics_count', 'posts_count', 'user_statistics', 'activity_timeline',
                      'content_breakdown', 'user_rank', 'engagement_score', 'last_activity')
    list_per_page = 100
    ordering = ('-date_joined',)
    inlines = [ArchivePostInline, ArchiveTopicInline]
    
    fieldsets = (
        ('User Info', {
            'fields': ('id', 'username', 'email', 'date_joined')
        }),
        ('Status', {
            'fields': ('is_staff', 'is_active', 'is_authenticated', 'activity_status')
        }),
        ('Profile Info', {
            'fields': ('has_profile', 'profile_messages', 'profile_groups', 'user_rank')
        }),
        ('Content Stats', {
            'fields': ('topics_count', 'posts_count', 'engagement_score')
        }),
        ('Detailed Analytics', {
            'fields': ('user_statistics', 'content_breakdown', 'activity_timeline'),
            'classes': ('collapse',)
        })
    )
    
    def username_with_status(self, obj):
        status_color = obj.archiveprofile.get_group_color
        staff_icon = ' 👑' if obj.is_staff else ''
        profile_icon = ' 📋' if hasattr(obj, 'archiveprofile') else ''
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>{}{}',
            status_color, obj.username or f'User-{obj.id}', staff_icon, profile_icon
        )
    username_with_status.short_description = 'Username'
    username_with_status.admin_order_field = 'username'
    
    def join_date_formatted(self, obj):
        if obj.date_joined:
            days_ago = (timezone.now() - obj.date_joined).days
            if days_ago == 0:
                date_info = 'Today'
            elif days_ago == 1:
                date_info = 'Yesterday'
            elif days_ago < 7:
                date_info = f'{days_ago} days ago'
            elif days_ago < 30:
                date_info = f'{days_ago//7} weeks ago'
            else:
                date_info = f'{days_ago//30} months ago'
            
            return format_html(
                '<span title="{}">{}<br/><small style="color: #666;">{}</small></span>',
                obj.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
                obj.date_joined.strftime('%m/%d/%Y'),
                date_info
            )
        return '-'
    join_date_formatted.short_description = 'Joined'
    join_date_formatted.admin_order_field = 'date_joined'
    
    def activity_status(self, obj):
        if hasattr(obj, 'archiveprofile'):
            last_login = obj.archiveprofile.last_login
            if last_login:
                days_since = (timezone.now() - last_login).days
                if days_since <= 1:
                    return format_html('<span style="color: green; font-weight: bold;">🟢 Active</span>')
                elif days_since <= 7:
                    return format_html('<span style="color: orange;">🟡 Recent</span>')
                elif days_since <= 30:
                    return format_html('<span style="color: #666;">⚪ Inactive</span>')
                else:
                    return format_html('<span style="color: red;">🔴 Long Inactive</span>')
        return format_html('<span style="color: gray;">❓ Unknown</span>')
    activity_status.short_description = 'Activity'
    
    def has_profile(self, obj):
        has_prof = hasattr(obj, 'archiveprofile')
        if has_prof:
            profile = obj.archiveprofile
            age = profile.get_user_age if hasattr(profile, 'get_user_age') else 'N/A'
            return format_html(
                '<span style="color: green;">[+] Yes</span><br/><small>Age: {}</small>',
                age
            )
        return format_html('<span style="color: red;">[x] No</span>')
    has_profile.short_description = 'Profile'
    
    def profile_messages(self, obj):
        if hasattr(obj, 'archiveprofile'):
            count = obj.archiveprofile.messages_count
            if count == 0:
                color = '#999'
            elif count < 10:
                color = '#666'
            elif count < 100:
                color = '#0066cc'
            else:
                color = '#cc6600'
            
            return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, count)
        return '-'
    profile_messages.short_description = 'Messages'
    
    def profile_groups(self, obj):
        if hasattr(obj, 'archiveprofile'):
            groups = obj.archiveprofile.groups.all()[:2]  # Show first 2 groups
            if groups:
                group_html = []
                for group in groups:
                    group_html.append(format_html(
                        '<span style="background: {}; color: white; padding: 1px 4px; border-radius: 2px; font-size: 11px;">{}</span>',
                        group.color or '#666',
                        group.name[:8] + ('...' if len(group.name) > 8 else '')
                    ))
                
                result = ' '.join(group_html)
                if obj.archiveprofile.groups.count() > 2:
                    result += f'<br/><small>+{obj.archiveprofile.groups.count() - 2} more</small>'
                return format_html(result)
            return 'No groups'
        return '-'
    profile_groups.short_description = 'Groups'
    
    def content_summary(self, obj):
        topics = obj.archive_topics.count()
        posts = obj.archive_posts.count()
        
        return format_html(
            '📝 {} topics<br/>💬 {} posts',
            topics, posts
        )
    content_summary.short_description = 'Content'
    
    def last_activity(self, obj):
        # Get the most recent post or topic
        latest_post = obj.archive_posts.order_by('-created_time').first()
        latest_topic = obj.archive_topics.order_by('-created_time').first()
        
        latest = None
        activity_type = None
        
        if latest_post and latest_topic:
            if latest_post.created_time > latest_topic.created_time:
                latest = latest_post.created_time
                activity_type = 'post'
            else:
                latest = latest_topic.created_time
                activity_type = 'topic'
        elif latest_post:
            latest = latest_post.created_time
            activity_type = 'post'
        elif latest_topic:
            latest = latest_topic.created_time
            activity_type = 'topic'
        
        if latest:
            days_ago = (timezone.now() - latest).days
            time_str = f'{days_ago}d ago' if days_ago > 0 else 'Today'
            icon = '💬' if activity_type == 'post' else '📝'
            return format_html('{} {}', icon, time_str)
        
        return format_html('<span style="color: #999;">No activity</span>')
    last_activity.short_description = 'Last Activity'
    
    def user_rank(self, obj):
        if hasattr(obj, 'archiveprofile'):
            messages = obj.archiveprofile.messages_count
            if messages >= 1000:
                return format_html('<span style="color: gold;">🏆 Expert</span>')
            elif messages >= 500:
                return format_html('<span style="color: silver;">🥈 Advanced</span>')
            elif messages >= 100:
                return format_html('<span style="color: #cd7f32;">🥉 Intermediate</span>')
            elif messages >= 10:
                return format_html('<span style="color: green;">📚 Beginner</span>')
            else:
                return format_html('<span style="color: #999;">🌱 Newbie</span>')
        return '-'
    user_rank.short_description = 'Rank'
    
    def topics_count(self, obj):
        count = obj.archive_topics.count()
        if count == 0:
            return format_html('<span style="color: #999;">0</span>')
        
        # Show breakdown by topic type
        subforums = obj.archive_topics.filter(is_sub_forum=True).count()
        regular = count - subforums
        
        return format_html(
            '<strong>{}</strong><br/><small>{} regular, {} subforums</small>',
            count, regular, subforums
        )
    topics_count.short_description = 'Topics Created'
    
    def posts_count(self, obj):
        count = obj.archive_posts.count()
        if count == 0:
            return format_html('<span style="color: #999;">0</span>')
        
        # Calculate average post length - use fresh queryset to avoid annotation conflicts
        post_queryset = models.ArchivePost.objects.filter(author=obj)
        avg_length = post_queryset.aggregate(
            avg_len=Avg(Length('text'))
        )['avg_len'] or 0
        
        return format_html(
            '<strong>{}</strong><br/><small>Avg: {} chars</small>',
            count, int(avg_length)
        )
    posts_count.short_description = 'Posts Created'
    
    def engagement_score(self, obj):
        # Calculate a simple engagement score
        topics = obj.archive_topics.count()
        posts = obj.archive_posts.count()
        
        if hasattr(obj, 'archiveprofile'):
            days_since_join = (timezone.now() - obj.date_joined).days or 1
            score = (topics * 3 + posts) / days_since_join
            
            if score >= 1:
                color = 'green'
                level = 'High'
            elif score >= 0.5:
                color = 'orange'
                level = 'Medium'
            else:
                color = 'red'
                level = 'Low'
            
            return format_html(
                '<span style="color: {};">{}</span><br/><small>{:.2f}/day</small>',
                color, level, score
            )
        return '-'
    engagement_score.short_description = 'Engagement'
    
    def _get_user_content_stats(self, obj):
        if hasattr(obj, '_content_stats_cache'):
            return obj._content_stats_cache

        from django.db.models import Count, Sum, Avg, Max
        from django.db.models.functions import Length
        from datetime import timedelta

        # Post statistics
        post_queryset = models.ArchivePost.objects.filter(author=obj)
        post_stats = post_queryset.aggregate(
            avg_length=Avg(Length('text')),
            total_chars=Sum(Length('text')),
            max_updates=Max('update_count'),
            count=Count('id')
        )
        post_stats['count'] = post_stats.get('count', 0)

        post_cats = post_queryset.values('topic__category__name').annotate(
            count=Count('id')
        ).order_by('-count')[:5]

        # Topic statistics
        topic_queryset = models.ArchiveTopic.objects.filter(author=obj)
        topic_stats = topic_queryset.aggregate(
            total_replies_sum=Sum('total_replies'),
            total_views_sum=Sum('total_views'),
            avg_replies=Avg('total_replies'),
            count=Count('id')
        )
        topic_stats['count'] = topic_stats.get('count', 0)
        
        subforums_count = topic_queryset.filter(is_sub_forum=True).count()

        topic_cats = topic_queryset.values('category__name').annotate(
            count=Count('id')
        ).order_by('-count')[:5]

        # Activity timeline
        thirty_days_ago = timezone.now() - timedelta(days=30)
        weeks = []
        for i in range(4):
            week_start = thirty_days_ago + timedelta(weeks=i)
            week_end = week_start + timedelta(weeks=1)
            
            posts = post_queryset.filter(
                created_time__range=(week_start, week_end)
            ).count()
            
            topics = topic_queryset.filter(
                created_time__range=(week_start, week_end)
            ).count()
            
            weeks.append({'posts': posts, 'topics': topics, 'week': i+1})

        stats = {
            'post_stats': post_stats,
            'topic_stats': topic_stats,
            'posts_count': post_stats['count'],
            'topics_count': topic_stats['count'],
            'subforums_count': subforums_count,
            'post_cats': list(post_cats),
            'topic_cats': list(topic_cats),
            'activity_weeks': weeks,
        }
        obj._content_stats_cache = stats
        return stats

    def user_statistics(self, obj):
        stats = self._get_user_content_stats(obj)
        topics = stats['topics_count']
        posts = stats['posts_count']
        
        if topics == 0 and posts == 0:
            return 'No content created yet'
        
        post_stats = stats['post_stats']
        topic_stats = stats['topic_stats']
        
        stats_html = f"""
        <table style="width: 100%; border-collapse: collapse;">
            <tr><th colspan="2" style="text-align: left; padding: 4px; border-bottom: 1px solid #ddd;">Content Statistics</th></tr>
            <tr><td style="padding: 2px 4px;">Total Posts:</td><td style="padding: 2px 4px;"><strong>{posts}</strong></td></tr>
            <tr><td style="padding: 2px 4px;">Avg Post Length:</td><td style="padding: 2px 4px;"><strong>{int(post_stats['avg_length'] or 0)} chars</strong></td></tr>
            <tr><td style="padding: 2px 4px;">Total Characters:</td><td style="padding: 2px 4px;"><strong>{post_stats['total_chars'] or 0:,}</strong></td></tr>
            <tr><td style="padding: 2px 4px;">Max Post Edits:</td><td style="padding: 2px 4px;"><strong>{post_stats['max_updates'] or 0}</strong></td></tr>
            
            <tr><th colspan="2" style="text-align: left; padding: 4px; border-bottom: 1px solid #ddd; padding-top: 10px;">Topic Statistics</th></tr>
            <tr><td style="padding: 2px 4px;">Total Topics:</td><td style="padding: 2px 4px;"><strong>{topics}</strong></td></tr>
            <tr><td style="padding: 2px 4px;">Total Replies Received:</td><td style="padding: 2px 4px;"><strong>{topic_stats['total_replies_sum'] or 0}</strong></td></tr>
            <tr><td style="padding: 2px 4px;">Total Views:</td><td style="padding: 2px 4px;"><strong>{topic_stats['total_views_sum'] or 0:,}</strong></td></tr>
            <tr><td style="padding: 2px 4px;">Avg Replies/Topic:</td><td style="padding: 2px 4px;"><strong>{float(topic_stats['avg_replies'] or 0):.1f}</strong></td></tr>
        </table>
        """
        
        return format_html(stats_html)
    user_statistics.short_description = 'Detailed Statistics'
    
    def content_breakdown(self, obj):
        stats = self._get_user_content_stats(obj)
        topic_cats = stats['topic_cats']
        post_cats = stats['post_cats']
        
        breakdown_html = '<div style="display: flex; gap: 20px;">'
        
        # Topics breakdown
        breakdown_html += '<div><strong>Topics by Category:</strong><ul style="margin: 5px 0;">'
        if topic_cats:
            for cat in topic_cats:
                cat_name = cat['category__name'] or 'Uncategorized'
                breakdown_html += f'<li>{cat_name}: {cat["count"]}</li>'
        else:
            breakdown_html += '<li>No topics</li>'
        breakdown_html += '</ul></div>'
        
        # Posts breakdown
        breakdown_html += '<div><strong>Posts by Category:</strong><ul style="margin: 5px 0;">'
        if post_cats:
            for cat in post_cats:
                cat_name = cat['topic__category__name'] or 'Uncategorized'
                breakdown_html += f'<li>{cat_name}: {cat["count"]}</li>'
        else:
            breakdown_html += '<li>No posts</li>'
        breakdown_html += '</ul></div>'
        
        breakdown_html += '</div>'
        
        return format_html(breakdown_html)
    content_breakdown.short_description = 'Content Breakdown'
    
    def activity_timeline(self, obj):
        stats = self._get_user_content_stats(obj)
        weeks = stats['activity_weeks']
        
        timeline_html = '<div style="display: flex; gap: 10px; align-items: end; height: 60px;">'
        max_activity = max((w['posts'] + w['topics'] for w in weeks), default=1)
        
        for week in weeks:
            total = week['posts'] + week['topics']
            height = int((total / max_activity) * 40) if max_activity > 0 else 1
            
            timeline_html += f'''
            <div style="display: flex; flex-direction: column; align-items: center;">
                <div style="width: 20px; height: {height}px; background: linear-gradient(to top, #007cba {height//2}px, #00a86b {height//2}px); border-radius: 2px;" title="Week {week['week']}: {week['topics']} topics, {week['posts']} posts"></div>
                <small>W{week['week']}</small>
            </div>
            '''
        
        timeline_html += '</div><small style="color: #666;">Last 4 weeks activity (blue=topics, green=posts)</small>'
        
        return format_html(timeline_html)
    activity_timeline.short_description = 'Activity Timeline'
    
    def get_queryset(self, request):
        # Optimize queryset for large datasets
        return super().get_queryset(request).select_related(
            'archiveprofile',
        ).prefetch_related(
            'archiveprofile__groups', 'archive_topics', 'archive_posts'
        ).annotate(
            total_posts=Count('archive_posts'),
            total_topics=Count('archive_topics')
        )


@admin.register(models.ArchiveForumGroup)
class ArchiveForumGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'priority', 'color_display', 'is_staff_group', 'is_messages_group', 
                   'is_hidden', 'minimum_messages', 'member_count', 'created_at', 'icon_preview')
    list_filter = ('is_staff_group', 'is_messages_group', 'is_hidden', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('-priority',)
    readonly_fields = ('created_at', 'member_count', 'eligible_users_count', 'icon_preview')
    list_per_page = 50
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'description', 'priority', 'created_at')
        }),
        ('Appearance', {
            'fields': ('color', 'icon', 'icon_preview')
        }),
        ('Settings', {
            'fields': ('is_staff_group', 'is_messages_group', 'is_hidden', 'minimum_messages')
        }),
        ('Statistics', {
            'fields': ('member_count', 'eligible_users_count')
        })
    )
    
    def color_display(self, obj):
        if obj.color:
            return format_html(
                '<span style="color: {}; font-weight: bold; background: {}; padding: 2px 6px; border-radius: 3px;">{}</span>',
                '#ffffff' if obj.color in ['#000000', '#000'] else '#000000',
                obj.color, 
                obj.color
            )
        return '-'
    color_display.short_description = 'Color'
    
    def icon_preview(self, obj):
        if obj.icon:
            return format_html('<img src="{}" style="max-height: 30px; max-width: 30px;"/>', obj.icon.url)
        return '-'
    icon_preview.short_description = 'Icon Preview'
    
    def member_count(self, obj):
        count = obj.archive_users.count()
        return format_html('<strong>{}</strong>', count)
    member_count.short_description = 'Members'
    
    def eligible_users_count(self, obj):
        if obj.is_messages_group and obj.minimum_messages > 0:
            from django.db.models import Q
            eligible = models.ArchiveProfile.objects.filter(
                messages_count__gte=obj.minimum_messages
            ).exclude(groups=obj).count()
            return format_html('<span style="color: orange;">{} eligible</span>', eligible)
        return '-'
    eligible_users_count.short_description = 'Eligible for Promotion'
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related(
            Prefetch('archive_users', queryset=models.ArchiveProfile.objects.select_related('user'))
        )


@admin.register(models.ArchiveCategory)
class ArchiveCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'is_hidden', 'topic_count', 'subforum_count', 
                   'index_topic_count', 'latest_activity')
    list_filter = ('is_hidden',)
    search_fields = ('name', 'slug')
    readonly_fields = ('slug', 'topic_count', 'subforum_count', 'index_topic_count', 
                      'latest_activity', 'total_posts', 'most_active_topic')
    list_per_page = 50
    filter_horizontal = ('index_topics',)
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('id', 'name', 'slug', 'is_hidden')
        }),
        ('Topics', {
            'fields': ('index_topics',)
        }),
        ('Statistics', {
            'fields': ('topic_count', 'subforum_count', 'index_topic_count', 
                      'total_posts', 'latest_activity', 'most_active_topic')
        })
    )
    
    def topic_count(self, obj):
        count = obj.archivetopic_set.count()
        return format_html('<strong>{}</strong>', count)
    topic_count.short_description = 'Total Topics'
    
    def subforum_count(self, obj):
        count = obj.archivetopic_set.filter(is_sub_forum=True).count()
        return count
    subforum_count.short_description = 'Subforums'
    
    def index_topic_count(self, obj):
        count = obj.index_topics.count()
        return count
    index_topic_count.short_description = 'Index Topics'
    
    def latest_activity(self, obj):
        latest_topic = obj.archivetopic_set.order_by('-last_message_time').first()
        if latest_topic and latest_topic.last_message_time:
            return format_html(
                '<span title="{}">{}</span>',
                latest_topic.last_message_time.strftime('%Y-%m-%d %H:%M:%S'),
                latest_topic.last_message_time.strftime('%m/%d %H:%M')
            )
        return '-'
    latest_activity.short_description = 'Latest Activity'
    
    def total_posts(self, obj):
        from django.db.models import Sum
        total = obj.archivetopic_set.aggregate(
            total_posts=Sum('total_replies')
        )['total_posts'] or 0
        return total + obj.archivetopic_set.count()  # Add topics themselves
    total_posts.short_description = 'Total Posts'
    
    def most_active_topic(self, obj):
        most_active = obj.archivetopic_set.order_by('-total_replies').first()
        if most_active:
            url = reverse('admin:archive_archivetopic_change', args=[most_active.pk])
            title = most_active.title[:30] + '...' if len(most_active.title) > 30 else most_active.title
            return format_html(
                '<a href="{}">{}</a> <span style="color: #666;">({} replies)</span>',
                url, title, most_active.total_replies
            )
        return '-'
    most_active_topic.short_description = 'Most Active Topic'
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('index_topics', 'archivetopic_set')


@admin.register(models.ArchiveTopic)
class ArchiveTopicAdmin(admin.ModelAdmin):
    list_display = ('id', 'title_with_status', 'author_link', 'category_link', 'parent_link', 
                   'topic_type_display', 'engagement_metrics', 'activity_indicator',
                   'created_time', 'last_message_time')
    list_filter = ('is_sub_forum', 'is_locked', 'is_pinned', 'is_announcement', 
                  'is_index_topic', 'category', 'created_time', TopicActivityFilter)
    search_fields = ('title', 'description', 'author__username')
    readonly_fields = ('slug', 'created_time', 'last_message_time', 'latest_message', 
                      'total_children', 'get_depth', 'topic_analytics', 'engagement_stats',
                      'reply_distribution', 'topic_health', 'performance_metrics')
    list_per_page = 100
    ordering = ('-created_time',)
    raw_id_fields = ('author', 'parent', 'latest_message')
    inlines = [ArchivePostInline]
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('title', 'description', 'author', 'category', 'parent', 'slug')
        }),
        ('Content Metrics', {
            'fields': ('icon', 'total_replies', 'total_views', 'total_children')
        }),
        ('Topic Settings', {
            'fields': ('is_sub_forum', 'is_locked', 'is_pinned', 'is_announcement', 
                      'is_index_topic', 'has_subforum_children', 'moved')
        }),
        ('Display Settings', {
            'fields': ('display_id', 'display_children', 'display_replies', 'display_views')
        }),
        ('Timestamps', {
            'fields': ('created_time', 'last_message_time', 'latest_message')
        }),
        ('Hierarchy', {
            'fields': ('get_depth',)
        }),
        ('Analytics', {
            'fields': ('topic_analytics', 'engagement_stats', 'reply_distribution', 
                      'topic_health', 'performance_metrics'),
            'classes': ('collapse',)
        })
    )
    
    def title_with_status(self, obj):
        title = obj.title[:40] + '...' if obj.title and len(obj.title) > 40 else (obj.title or 'No Title')
        
        # Status indicators
        indicators = []
        if obj.is_sub_forum:
            indicators.append('📁')
        if obj.is_locked:
            indicators.append('🔒')
        if obj.is_pinned:
            indicators.append('📌')
        if obj.is_announcement:
            indicators.append('📢')
        if obj.moved:
            indicators.append('↗️')
        
        status_str = ' '.join(indicators)
        
        return format_html(
            '<strong>{}</strong><br/><small style="color: #666;">{}</small>',
            title, status_str if status_str else 'Regular Topic'
        )
    title_with_status.short_description = 'Title & Status'
    title_with_status.admin_order_field = 'title'
    
    def topic_type_display(self, obj):
        if obj.is_sub_forum:
            color = '#0066cc'
            type_name = 'Subforum'
            icon = '📁'
        elif obj.is_announcement:
            color = '#cc0000'
            type_name = 'Announcement'
            icon = '📢'
        elif obj.is_pinned:
            color = '#cc6600'
            type_name = 'Pinned'
            icon = '📌'
        elif obj.is_locked:
            color = '#666666'
            type_name = 'Locked'
            icon = '🔒'
        else:
            color = '#009900'
            type_name = 'Regular'
            icon = '💬'
        
        return format_html(
            '<span style="color: {};">{} {}</span>',
            color, icon, type_name
        )
    topic_type_display.short_description = 'Type'
    
    def engagement_metrics(self, obj):
        # Use display_replies and display_views for archive data, with safe defaults
        try:
            replies = getattr(obj, 'display_replies', 0) or 0
            views = getattr(obj, 'display_views', 0) or 0
            
            # Convert to native Python types
            replies = int(replies)
            views = int(views)
        except (ValueError, TypeError):
            replies = 0
            views = 0
        
        # Calculate engagement rate
        if views > 0:
            engagement_rate = (replies / views) * 100
        else:
            engagement_rate = 0
        
        # Determine engagement level
        if engagement_rate >= 10:
            color = '#009900'
            level = 'High'
        elif engagement_rate >= 5:
            color = '#cc6600'
            level = 'Medium'
        else:
            color = '#cc0000'
            level = 'Low'
        
        # Format numbers manually to avoid SafeString issues
        views_str = str(views)
        if len(views_str) > 3:
            # Add commas for thousands
            views_with_commas = ''
            for i, digit in enumerate(reversed(views_str)):
                if i > 0 and i % 3 == 0:
                    views_with_commas = ',' + views_with_commas
                views_with_commas = digit + views_with_commas
        else:
            views_with_commas = views_str
        
        # Format engagement rate manually to avoid SafeString issues
        engagement_rate_str = f"{engagement_rate:.1f}"
        
        return format_html(
            '<div>💬 <strong>{}</strong> replies</div>'
            '<div>👁️ <strong>{}</strong> views</div>'
            '<div><span style="color: {};">📊 {} ({}%)</span></div>',
            replies, views_with_commas, color, level, engagement_rate_str
        )
    engagement_metrics.short_description = 'Engagement'
    
    def activity_indicator(self, obj):
        if not obj.last_message_time:
            return format_html('<span style="color: #999;">🔇 No activity</span>')
        
        days_since = (timezone.now() - obj.last_message_time).days
        
        if days_since <= 1:
            return format_html('<span style="color: green;">🔥 Very Active</span>')
        elif days_since <= 7:
            return format_html('<span style="color: orange;">⚡ Active</span>')
        elif days_since <= 30:
            return format_html('<span style="color: #666;">⏰ Recent</span>')
        elif days_since <= 90:
            return format_html('<span style="color: #999;">💤 Quiet</span>')
        else:
            return format_html('<span style="color: red;">☠️ Dead</span>')
    activity_indicator.short_description = 'Activity'
    
    def author_link(self, obj):
        if obj.author:
            url = reverse('admin:archive_fakeuser_change', args=[obj.author.pk])
            
            # Add author stats
            author_topics = obj.author.archive_topics.count()
            author_posts = obj.author.archive_posts.count()
            
            return format_html(
                '<a href="{}">{}</a><br/><small style="color: #666;">{} topics, {} posts</small>',
                url, obj.author.username, author_topics, author_posts
            )
        return '-'
    author_link.short_description = 'Author'
    
    def category_link(self, obj):
        if obj.category:
            url = reverse('admin:archive_archivecategory_change', args=[obj.category.pk])
            
            # Add category stats
            cat_topics = obj.category.archivetopic_set.count()
            
            return format_html(
                '<a href="{}">{}</a><br/><small style="color: #666;">{} total topics</small>',
                url, obj.category.name, cat_topics
            )
        return '-'
    category_link.short_description = 'Category'
    
    def parent_link(self, obj):
        if obj.parent:
            url = reverse('admin:archive_archivetopic_change', args=[obj.parent.pk])
            title = obj.parent.title[:20] + '...' if obj.parent.title and len(obj.parent.title) > 20 else (obj.parent.title or f'Topic {obj.parent.id}')
            
            # Add parent stats
            parent_children = obj.parent.archive_children.count()
            
            return format_html(
                '<a href="{}">{}</a><br/><small style="color: #666;">{} children</small>',
                url, title, parent_children
            )
        return '-'
    parent_link.short_description = 'Parent'
    
    def topic_analytics(self, obj):
        # Comprehensive topic analytics
        from datetime import timedelta
        
        # Time-based statistics
        age_days = (timezone.now() - obj.created_time).days
        
        # Calculate averages - use display values for archive data
        total_replies = obj.display_replies if hasattr(obj, 'display_replies') and obj.display_replies is not None else 0
        total_views = obj.display_views if hasattr(obj, 'display_views') and obj.display_views is not None else 0
        
        avg_replies_per_day = total_replies / max(age_days, 1)
        avg_views_per_day = total_views / max(age_days, 1)
        
        # Get post frequency data
        posts = obj.archive_replies.all()
        if posts.exists():
            first_post = posts.order_by('created_time').first()
            last_post = posts.order_by('-created_time').first()
            post_span_days = (last_post.created_time - first_post.created_time).days or 1
            post_frequency = len(posts) / post_span_days
        else:
            post_frequency = 0
            post_span_days = 0
        
        analytics_html = f"""
        <table style="width: 100%; border-collapse: collapse;">
            <tr><th colspan="2" style="text-align: left; padding: 4px; border-bottom: 1px solid #ddd;">Topic Analytics</th></tr>
            <tr><td style="padding: 2px 4px;">Topic Age:</td><td style="padding: 2px 4px;"><strong>{age_days} days</strong></td></tr>
            <tr><td style="padding: 2px 4px;">Avg Replies/Day:</td><td style="padding: 2px 4px;"><strong>{avg_replies_per_day:.2f}</strong></td></tr>
            <tr><td style="padding: 2px 4px;">Avg Views/Day:</td><td style="padding: 2px 4px;"><strong>{avg_views_per_day:.2f}</strong></td></tr>
            <tr><td style="padding: 2px 4px;">Post Frequency:</td><td style="padding: 2px 4px;"><strong>{post_frequency:.2f}/day</strong></td></tr>
            <tr><td style="padding: 2px 4px;">Active Period:</td><td style="padding: 2px 4px;"><strong>{post_span_days} days</strong></td></tr>
            <tr><td style="padding: 2px 4px;">Views per Reply:</td><td style="padding: 2px 4px;"><strong>{total_views / max(total_replies, 1):.1f}</strong></td></tr>
        </table>
        """
        
        return format_html(analytics_html)
    topic_analytics.short_description = 'Topic Analytics'
    
    def engagement_stats(self, obj):
        # Detailed engagement statistics
        posts = obj.archive_replies.all()
        
        if not posts.exists():
            return 'No posts yet'
        
        # Participant analysis
        unique_authors = posts.values('author').distinct().count()
        total_posts = posts.count()
        
        # Author contribution breakdown
        author_stats = posts.values('author__username').annotate(
            post_count=Count('id')
        ).order_by('-post_count')[:5]
        
        # Calculate engagement metrics
        participation_rate = unique_authors / max(obj.total_views, 1) * 100
        posts_per_participant = total_posts / max(unique_authors, 1)
        
        stats_html = f"""
        <table style="width: 100%; border-collapse: collapse;">
            <tr><th colspan="2" style="text-align: left; padding: 4px; border-bottom: 1px solid #ddd;">Engagement Statistics</th></tr>
            <tr><td style="padding: 2px 4px;">Unique Participants:</td><td style="padding: 2px 4px;"><strong>{unique_authors}</strong></td></tr>
            <tr><td style="padding: 2px 4px;">Participation Rate:</td><td style="padding: 2px 4px;"><strong>{participation_rate:.2f}%</strong></td></tr>
            <tr><td style="padding: 2px 4px;">Posts per Participant:</td><td style="padding: 2px 4px;"><strong>{posts_per_participant:.1f}</strong></td></tr>
            
            <tr><th colspan="2" style="text-align: left; padding: 4px; border-bottom: 1px solid #ddd; padding-top: 10px;">Top Contributors</th></tr>
        """
        
        for stat in author_stats:
            username = stat['author__username'] or 'Anonymous'
            stats_html += f'<tr><td style="padding: 2px 4px;">{username}:</td><td style="padding: 2px 4px;"><strong>{stat["post_count"]} posts</strong></td></tr>'
        
        stats_html += '</table>'
        
        return format_html(stats_html)
    engagement_stats.short_description = 'Engagement Stats'
    
    def reply_distribution(self, obj):
        # Analyze reply distribution over time
        posts = obj.archive_replies.all()
        
        if not posts.exists():
            return 'No posts to analyze'
        
        # Group posts by month
        from django.db.models.functions import TruncMonth
        monthly_posts = posts.annotate(
            month=TruncMonth('created_time')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')
        
        # Create a simple visual representation
        if monthly_posts:
            max_posts = max(mp['count'] for mp in monthly_posts)
            
            distribution_html = '<div style="display: flex; gap: 2px; align-items: end; height: 40px; margin: 5px 0;">'
            
            for mp in monthly_posts[-12:]:  # Last 12 months
                height = int((mp['count'] / max_posts) * 30)
                month_str = mp['month'].strftime('%m/%y')
                
                distribution_html += f'''
                <div style="display: flex; flex-direction: column; align-items: center;">
                    <div style="width: 15px; height: {height}px; background: #007cba; border-radius: 1px;" title="{month_str}: {mp['count']} posts"></div>
                    <small style="font-size: 9px; transform: rotate(-45deg); margin-top: 5px;">{month_str}</small>
                </div>
                '''
            
            distribution_html += '</div><small style="color: #666;">Post distribution by month</small>'
            
            return format_html(distribution_html)
        
        return 'No distribution data'
    reply_distribution.short_description = 'Reply Distribution'
    
    def topic_health(self, obj):
        # Calculate topic health score
        age_days = (timezone.now() - obj.created_time).days
        
        # Use display values for archive data
        total_replies = obj.display_replies if hasattr(obj, 'display_replies') and obj.display_replies is not None else 0
        total_views = obj.display_views if hasattr(obj, 'display_views') and obj.display_views is not None else 0
        
        # Health factors
        recent_activity = 1 if obj.last_message_time and (timezone.now() - obj.last_message_time).days <= 30 else 0
        has_replies = 1 if total_replies > 0 else 0
        good_engagement = 1 if total_views > 0 and (total_replies / total_views * 100) >= 2 else 0
        active_discussion = 1 if total_replies >= 5 else 0
        
        health_score = (recent_activity + has_replies + good_engagement + active_discussion) * 25
        
        if health_score >= 75:
            color = 'green'
            status = 'Healthy'
            icon = '💚'
        elif health_score >= 50:
            color = 'orange'
            status = 'Fair'
            icon = '💛'
        else:
            color = 'red'
            status = 'Poor'
            icon = '❤️'
        
        factors = []
        if recent_activity:
            factors.append('[+] Recent activity')
        else:
            factors.append('[x] No recent activity')
            
        if has_replies:
            factors.append('[+] Has replies')
        else:
            factors.append('[x] No replies')
            
        if good_engagement:
            factors.append('[+] Good engagement')
        else:
            factors.append('[x] Low engagement')
            
        if active_discussion:
            factors.append('[+] Active discussion')
        else:
            factors.append('[x] Limited discussion')
        
        return format_html(
            '<div style="color: {};">{} <strong>{}</strong> ({}%)</div><small>{}</small>',
            color, icon, status, health_score, '<br/>'.join(factors)
        )
    topic_health.short_description = 'Topic Health'
    
    def performance_metrics(self, obj):
        # Performance comparison with similar topics - use fresh queryset
        similar_topics = models.ArchiveTopic.objects.filter(
            category=obj.category,
            is_sub_forum=obj.is_sub_forum
        ).exclude(id=obj.id)
        
        if similar_topics.exists():
            avg_replies = similar_topics.aggregate(avg=Avg('total_replies'))['avg'] or 0
            avg_views = similar_topics.aggregate(avg=Avg('total_views'))['avg'] or 0
            
            # Convert to float to avoid SafeString formatting issues
            avg_replies = float(avg_replies)
            avg_views = float(avg_views)
            
            # Use display values for archive data
            obj_replies = obj.display_replies if hasattr(obj, 'display_replies') and obj.display_replies is not None else 0
            obj_views = obj.display_views if hasattr(obj, 'display_views') and obj.display_views is not None else 0
            
            reply_performance = ((obj_replies - avg_replies) / max(avg_replies, 1)) * 100
            view_performance = ((obj_views - avg_views) / max(avg_views, 1)) * 100
            
            metrics_html = f"""
            <table style="border-collapse: collapse;">
                <tr><th colspan="2" style="text-align: left; padding: 4px; border-bottom: 1px solid #ddd;">Performance vs Similar Topics</th></tr>
                <tr><td style="padding: 2px 4px;">Reply Performance:</td><td style="padding: 2px 4px;"><strong>{reply_performance:+.1f}%</strong></td></tr>
                <tr><td style="padding: 2px 4px;">View Performance:</td><td style="padding: 2px 4px;"><strong>{view_performance:+.1f}%</strong></td></tr>
                <tr><td style="padding: 2px 4px;">Category Average Replies:</td><td style="padding: 2px 4px;"><strong>{avg_replies:.1f}</strong></td></tr>
                <tr><td style="padding: 2px 4px;">Category Average Views:</td><td style="padding: 2px 4px;"><strong>{avg_views:.1f}</strong></td></tr>
            </table>
            """
            
            return format_html(metrics_html)
        
        return 'No similar topics for comparison'
    performance_metrics.short_description = 'Performance Metrics'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'author', 'category', 'parent', 'latest_message'
        ).prefetch_related('archive_children', 'archive_replies')


@admin.register(models.ArchivePost)
class ArchivePostAdmin(admin.ModelAdmin):
    list_display = ('id', 'author_link', 'topic_link', 'text_preview', 'created_time', 
                   'updated_time', 'update_count', 'word_count', 'is_first_post')
    list_filter = ('created_time', 'updated_time', 'topic__category', 'topic__is_sub_forum')
    search_fields = ('text', 'author__username', 'topic__title')
    readonly_fields = ('created_time', 'get_page_number', 'get_relative_id', 'get_raw_text',
                      'word_count', 'char_count', 'is_first_post', 'bbcode_tags_used')
    list_per_page = 100
    ordering = ('-created_time',)
    raw_id_fields = ('author', 'topic')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('author', 'topic', 'text')
        }),
        ('Timestamps', {
            'fields': ('created_time', 'updated_time', 'update_count')
        }),
        ('Position Info', {
            'fields': ('get_page_number', 'get_relative_id', 'is_first_post')
        }),
        ('Content Analysis', {
            'fields': ('get_raw_text', 'word_count', 'char_count', 'bbcode_tags_used')
        })
    )
    
    def text_preview(self, obj):
        if obj.text:
            # Remove BBCode for preview
            clean_text = obj.get_raw_text
            if len(clean_text) > 100:
                return clean_text[:100] + '...'
            return clean_text
        return 'No Content'
    text_preview.short_description = 'Text Preview'
    
    def author_link(self, obj):
        if obj.author:
            url = reverse('admin:archive_fakeuser_change', args=[obj.author.pk])
            return format_html('<a href="{}">{}</a>', url, obj.author.username)
        return '-'
    author_link.short_description = 'Author'
    
    def topic_link(self, obj):
        if obj.topic:
            url = reverse('admin:archive_archivetopic_change', args=[obj.topic.pk])
            return format_html('<a href="{}">{}</a>', url, obj.topic.title or f'Topic {obj.topic.id}')
        return '-'
    topic_link.short_description = 'Topic'
    
    def word_count(self, obj):
        if obj.text:
            # Count words in raw text
            words = len(obj.get_raw_text.split())
            return format_html('<span style="color: #666;">{} words</span>', words)
        return 0
    word_count.short_description = 'Words'
    
    def char_count(self, obj):
        return len(obj.text) if obj.text else 0
    char_count.short_description = 'Characters'
    
    def is_first_post(self, obj):
        if obj.topic:
            first_post = obj.topic.get_first_post
            is_first = first_post and first_post.id == obj.id
            color = 'green' if is_first else 'gray'
            return format_html('<span style="color: {};">{}</span>', color, 'Yes' if is_first else 'No')
        return '-'
    is_first_post.short_description = 'First Post'
    
    def bbcode_tags_used(self, obj):
        if obj.text:
            import re
            # Find BBCode tags
            tags = re.findall(r'\[(\w+)(?:=.*?)?\]', obj.text)
            unique_tags = list(set(tags))
            if unique_tags:
                return ', '.join(unique_tags[:5])  # Show first 5 unique tags
            return 'None'
        return '-'
    bbcode_tags_used.short_description = 'BBCode Tags'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('author', 'topic', 'topic__category')


@admin.register(models.ArchiveForum)
class ArchiveForumAdmin(admin.ModelAdmin):
    list_display = ('name', 'total_users', 'total_messages', 'online_record', 'online_record_date',
                   'announcement_count', 'latest_user_info')
    readonly_fields = ('total_users', 'total_messages', 'online_record', 'online_record_date',
                      'announcement_count', 'latest_user_info', 'forum_statistics')
    filter_horizontal = ('announcement_topics',)
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name',)
        }),
        ('Statistics', {
            'fields': ('total_users', 'total_messages', 'online_record', 'online_record_date')
        }),
        ('Announcements', {
            'fields': ('announcement_topics', 'announcement_count')
        }),
        ('Latest Activity', {
            'fields': ('latest_user_info',)
        }),
        ('Detailed Statistics', {
            'fields': ('forum_statistics',),
            'classes': ('collapse',)
        })
    )
    
    def announcement_count(self, obj):
        count = obj.announcement_topics.count()
        return format_html('<strong>{}</strong>', count)
    announcement_count.short_description = 'Announcements'
    
    def latest_user_info(self, obj):
        latest_user = obj.get_latest_user
        if latest_user:
            url = reverse('admin:archive_fakeuser_change', args=[latest_user.pk])
            return format_html(
                '<a href="{}">{}</a> <span style="color: #666;">(joined {})</span>',
                url, latest_user.username, latest_user.date_joined.strftime('%m/%d/%Y')
            )
        return 'No users'
    latest_user_info.short_description = 'Latest User'
    
    def forum_statistics(self, obj):
        # Get comprehensive forum statistics
        from django.db.models import Count, Q
        
        stats = []
        
        # User statistics
        active_users = models.FakeUser.objects.filter(is_active=True).count()
        staff_users = models.ArchiveProfile.objects.filter(groups__is_staff_group=True).distinct().count()
        
        # Topic statistics
        total_topics = models.ArchiveTopic.objects.count()
        subforums = models.ArchiveTopic.objects.filter(is_sub_forum=True).count()
        locked_topics = models.ArchiveTopic.objects.filter(is_locked=True).count()
        pinned_topics = models.ArchiveTopic.objects.filter(is_pinned=True).count()
        
        # Post statistics
        total_posts = models.ArchivePost.objects.count()
        
        stats_html = f"""
        <table style="width: 100%; border-collapse: collapse;">
            <tr><th style="text-align: left; padding: 4px; border-bottom: 1px solid #ddd;">Users</th></tr>
            <tr><td style="padding: 2px 4px;">Active Users: <strong>{active_users}</strong></td></tr>
            <tr><td style="padding: 2px 4px;">Staff Users: <strong>{staff_users}</strong></td></tr>
            
            <tr><th style="text-align: left; padding: 4px; border-bottom: 1px solid #ddd; padding-top: 10px;">Topics</th></tr>
            <tr><td style="padding: 2px 4px;">Total Topics: <strong>{total_topics}</strong></td></tr>
            <tr><td style="padding: 2px 4px;">Subforums: <strong>{subforums}</strong></td></tr>
            <tr><td style="padding: 2px 4px;">Locked Topics: <strong>{locked_topics}</strong></td></tr>
            <tr><td style="padding: 2px 4px;">Pinned Topics: <strong>{pinned_topics}</strong></td></tr>
            
            <tr><th style="text-align: left; padding: 4px; border-bottom: 1px solid #ddd; padding-top: 10px;">Posts</th></tr>
            <tr><td style="padding: 2px 4px;">Total Posts: <strong>{total_posts}</strong></td></tr>
            <tr><td style="padding: 2px 4px;">Avg Posts/User: <strong>{total_posts/max(obj.total_users, 1):.1f}</strong></td></tr>
        </table>
        """
        
        return format_html(stats_html)
    forum_statistics.short_description = 'Detailed Statistics'
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('announcement_topics')


@admin.register(models.ArchiveTopicReadStatus)
class ArchiveTopicReadStatusAdmin(admin.ModelAdmin):
    list_display = ('user', 'topic_link', 'last_read')
    list_filter = ('last_read',)
    search_fields = ('user__username', 'topic__title')
    raw_id_fields = ('user', 'topic')
    list_per_page = 100
    ordering = ('-last_read',)
    
    def topic_link(self, obj):
        if obj.topic:
            url = reverse('admin:archive_archivetopic_change', args=[obj.topic.pk])
            return format_html('<a href="{}">{}</a>', url, obj.topic.title or f'Topic {obj.topic.id}')
        return '-'
    topic_link.short_description = 'Topic'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'topic')


@admin.register(models.ArchiveSmileyCategory)
class ArchiveSmileyCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'smiley_count')
    search_fields = ('name',)
    # Cannot use filter_horizontal with ManyToManyField that has custom through model
    inlines = [ArchiveSmileyCategory_smileysInline]
    
    def smiley_count(self, obj):
        return obj.smileys.count()
    smiley_count.short_description = 'Smileys'
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('smileys')


@admin.register(models.ArchivePoll)
class ArchivePollAdmin(admin.ModelAdmin):
    list_display = ('question_short', 'topic_link', 'created_at', 'max_choices_per_user', 
                   'days_to_vote', 'is_active_display', 'total_votes')
    list_filter = ('created_at', 'max_choices_per_user', 'days_to_vote')
    search_fields = ('question', 'topic__title')
    readonly_fields = ('created_at', 'is_active_display', 'total_votes', 'allow_multiple_choices')
    raw_id_fields = ('topic',)
    list_per_page = 50
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('topic', 'question', 'created_at')
        }),
        ('Settings', {
            'fields': ('max_choices_per_user', 'days_to_vote', 'can_change_vote')
        }),
        ('Status', {
            'fields': ('is_active_display', 'allow_multiple_choices', 'total_votes')
        })
    )
    
    def question_short(self, obj):
        if obj.question and len(obj.question) > 60:
            return obj.question[:60] + '...'
        return obj.question
    question_short.short_description = 'Question'
    
    def topic_link(self, obj):
        if obj.topic:
            url = reverse('admin:archive_archivetopic_change', args=[obj.topic.pk])
            return format_html('<a href="{}">{}</a>', url, obj.topic.title or f'Topic {obj.topic.id}')
        return '-'
    topic_link.short_description = 'Topic'
    
    def is_active_display(self, obj):
        is_active = obj.is_active
        color = 'green' if is_active else 'red'
        return format_html('<span style="color: {};">{}</span>', color, 'Active' if is_active else 'Inactive')
    is_active_display.short_description = 'Status'
    
    def total_votes(self, obj):
        return obj.get_total_vote_count
    total_votes.short_description = 'Total Votes'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('topic').prefetch_related('archive_options')


@admin.register(models.ArchivePollOption)
class ArchivePollOptionAdmin(admin.ModelAdmin):
    list_display = ('text_short', 'poll_link', 'vote_count', 'percentage')
    search_fields = ('text', 'poll__question')
    raw_id_fields = ('poll',)
    # Cannot use filter_horizontal with ManyToManyField that has custom through model
    inlines = [ArchivePollOptionVotersInline]
    list_per_page = 100
    
    def text_short(self, obj):
        if obj.text and len(obj.text) > 50:
            return obj.text[:50] + '...'
        return obj.text
    text_short.short_description = 'Option Text'
    
    def poll_link(self, obj):
        if obj.poll:
            url = reverse('admin:archive_archivepoll_change', args=[obj.poll.pk])
            question = obj.poll.question[:30] + '...' if len(obj.poll.question) > 30 else obj.poll.question
            return format_html('<a href="{}">{}</a>', url, question)
        return '-'
    poll_link.short_description = 'Poll'
    
    def vote_count(self, obj):
        return obj.get_vote_count
    vote_count.short_description = 'Votes'
    
    def percentage(self, obj):
        percentage_val = obj.get_percentage
        return str(percentage_val) + "%"
    percentage.short_description = 'Percentage'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('poll').prefetch_related('voters')


@admin.register(models.ArchivePollOptionVoters)
class ArchivePollOptionVotersAdmin(admin.ModelAdmin):
    list_display = ('option_text', 'user_link', 'poll_question')
    search_fields = ('archivepolloption__text', 'user__username', 'archivepolloption__poll__question')
    raw_id_fields = ('archivepolloption', 'user')
    list_per_page = 100
    
    def option_text(self, obj):
        if obj.archivepolloption and obj.archivepolloption.text:
            text = obj.archivepolloption.text
            return text[:40] + '...' if len(text) > 40 else text
        return '-'
    option_text.short_description = 'Option'
    
    def user_link(self, obj):
        if obj.user:
            url = reverse('admin:archive_fakeuser_change', args=[obj.user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        return '-'
    user_link.short_description = 'User'
    
    def poll_question(self, obj):
        if obj.archivepolloption and obj.archivepolloption.poll:
            question = obj.archivepolloption.poll.question
            return question[:30] + '...' if len(question) > 30 else question
        return '-'
    poll_question.short_description = 'Poll Question'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'archivepolloption', 'archivepolloption__poll', 'user'
        )


@admin.register(models.ArchiveSmileyCategory_smileys)
class ArchiveSmileyCategory_smileysAdmin(admin.ModelAdmin):
    list_display = ('category_name', 'smiley_info', 'smiley_preview')
    list_filter = ('archivesmileycategory',)
    search_fields = ('archivesmileycategory__name', 'smileytag__tag')
    raw_id_fields = ('archivesmileycategory', 'smileytag')
    list_per_page = 100
    
    def category_name(self, obj):
        if obj.archivesmileycategory:
            url = reverse('admin:archive_archivesmileycategory_change', args=[obj.archivesmileycategory.pk])
            return format_html('<a href="{}">{}</a>', url, obj.archivesmileycategory.name)
        return '-'
    category_name.short_description = 'Category'
    
    def smiley_info(self, obj):
        if obj.smileytag:
            tag_value = str(obj.smileytag.tag) if hasattr(obj.smileytag, 'tag') else 'Smiley'
            return tag_value
        return '-'
    smiley_info.short_description = 'Smiley Tag'
    
    def smiley_preview(self, obj):
        if obj.smileytag and hasattr(obj.smileytag, 'image_url'):
            return format_html('<img src="{}" style="max-height: 25px; max-width: 25px;"/>', obj.smileytag.image_url)
        return '-'
    smiley_preview.short_description = 'Preview'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('archivesmileycategory', 'smileytag')


@admin.register(models.ArchiveSubforum)
class ArchiveSubforumAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'description_short', 'is_hidden', 'parent_count', 'related_topics')
    list_filter = ('is_hidden',)
    search_fields = ('title', 'description')
    filter_horizontal = ('parent',)
    readonly_fields = ('parent_count', 'related_topics', 'subforum_stats')
    list_per_page = 50
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('id', 'title', 'description', 'is_hidden')
        }),
        ('Relationships', {
            'fields': ('parent', 'parent_count', 'related_topics')
        }),
        ('Statistics', {
            'fields': ('subforum_stats',)
        })
    )
    
    def description_short(self, obj):
        if obj.description and len(obj.description) > 60:
            return obj.description[:60] + '...'
        return obj.description or '-'
    description_short.short_description = 'Description'
    
    def parent_count(self, obj):
        return obj.parent.count()
    parent_count.short_description = 'Parent Count'
    
    def related_topics(self, obj):
        # Count related topics (assuming relationship exists)
        try:
            # This would depend on your model relationships
            count = obj.archivetopic_set.count() if hasattr(obj, 'archivetopic_set') else 0
            return count
        except:
            return 0
    related_topics.short_description = 'Related Topics'
    
    def subforum_stats(self, obj):
        stats_html = f"""
        <table style="border-collapse: collapse;">
            <tr><th colspan="2" style="text-align: left; padding: 4px; border-bottom: 1px solid #ddd;">Subforum Statistics</th></tr>
            <tr><td style="padding: 2px 4px;">Parent Count:</td><td style="padding: 2px 4px;"><strong>{obj.parent.count()}</strong></td></tr>
            <tr><td style="padding: 2px 4px;">Is Hidden:</td><td style="padding: 2px 4px;"><strong>{'Yes' if obj.is_hidden else 'No'}</strong></td></tr>
        </table>
        """
        return format_html(stats_html)
    subforum_stats.short_description = 'Statistics'
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('parent')


# Keep the existing ArchiveProfileAdmin
@admin.register(models.ArchiveProfile)
class ArchiveProfileAdmin(admin.ModelAdmin):
    list_display = ('user_link', 'display_username', 'profile_summary', 'top_group_display', 
                   'activity_summary', 'profile_completion', 'last_login')
    list_filter = ('type', 'gender', 'zodiac_sign', 'email_is_public', 'is_hidden', 
                  'last_login', 'groups', MessageCountFilter)
    search_fields = ('user__username', 'display_username', 'desc', 'localisation', 'loisirs')
    readonly_fields = ('messages_count', 'upload_size', 'get_user_age', 'is_user_staff', 
                      'get_group_color', 'get_top_group', 'profile_analytics', 'social_metrics',
                      'content_quality_score', 'forum_influence', 'profile_completion_details')
    filter_horizontal = ('groups',)
    raw_id_fields = ('user', 'top_group')
    list_per_page = 100
    ordering = ('-last_login',)
    actions = ['promote_users', 'update_group_colors', 'generate_profile_report']
    
    fieldsets = (
        ('User Info', {
            'fields': ('user', 'display_id', 'display_username', 'profile_picture')
        }),
        ('Personal Info', {
            'fields': ('desc', 'localisation', 'loisirs', 'birthdate', 'get_user_age', 
                      'type', 'favorite_games', 'zodiac_sign', 'gender')
        }),
        ('Contact Info', {
            'fields': ('website', 'skype', 'email_is_public')
        }),
        ('Forum Info', {
            'fields': ('groups', 'top_group', 'get_top_group', 'messages_count', 
                      'signature', 'name_color', 'get_group_color')
        }),
        ('Settings', {
            'fields': ('upload_size', 'is_hidden', 'last_login', 'is_user_staff')
        }),
        ('Analytics', {
            'fields': ('profile_analytics', 'social_metrics', 'content_quality_score', 
                      'forum_influence', 'profile_completion_details'),
            'classes': ('collapse',)
        })
    )
    
    def profile_summary(self, obj):
        age = obj.get_user_age if hasattr(obj, 'get_user_age') else 'N/A'
        location = obj.localisation[:20] + '...' if obj.localisation and len(obj.localisation) > 20 else (obj.localisation or 'Not specified')
        
        return format_html(
            '<strong>{}</strong> messages<br/>📍 {}<br/>🎂 {} years',
            obj.messages_count, location, age
        )
    profile_summary.short_description = 'Profile Summary'
    
    def activity_summary(self, obj):
        if obj.last_login:
            days_since = (timezone.now() - obj.last_login).days
            
            if days_since <= 1:
                status = format_html('<span style="color: green;">🟢 Online recently</span>')
            elif days_since <= 7:
                status = format_html('<span style="color: orange;">🟡 Active this week</span>')
            elif days_since <= 30:
                status = format_html('<span style="color: #666;">⚪ Active this month</span>')
            else:
                status = format_html('<span style="color: red;">🔴 Inactive</span>')
            
            return format_html(
                '{}<br/><small>{} days ago</small>',
                status, days_since
            )
        
        return format_html('<span style="color: gray;">❓ Never logged in</span>')
    activity_summary.short_description = 'Activity'
    
    def profile_completion(self, obj):
        # Calculate profile completion percentage
        fields = [
            obj.desc, obj.localisation, obj.loisirs, obj.birthdate,
            obj.favorite_games, obj.zodiac_sign, obj.gender, obj.website,
            obj.skype, obj.signature, obj.profile_picture
        ]
        
        completed = sum(1 for field in fields if field)
        completion_rate = (completed / len(fields)) * 100
        
        if completion_rate >= 80:
            color = 'green'
            icon = '[+]'
        elif completion_rate >= 50:
            color = 'orange'
            icon = '⚠️'
        else:
            color = 'red'
            icon = '[x]'
        
        return format_html(
            '<span style="color: {};">{} {:.0f}%</span><br/><small>{}/{} fields</small>',
            color, icon, completion_rate, completed, len(fields)
        )
    profile_completion.short_description = 'Completion'
    
    def user_link(self, obj):
        if obj.user:
            url = reverse('admin:archive_fakeuser_change', args=[obj.user.pk])
            
            # Add user status indicators
            indicators = []
            if obj.user.is_staff:
                indicators.append('👑')
            if obj.is_user_staff:
                indicators.append('⭐')
            if obj.is_hidden:
                indicators.append('👻')
            
            status_str = ' '.join(indicators)
            
            return format_html(
                '<a href="{}">{}</a> {}',
                url, obj.user.username, status_str
            )
        return '-'
    user_link.short_description = 'User'
    
    def top_group_display(self, obj):
        top_group = obj.get_top_group
        if top_group:
            # Show group with priority and member count
            member_count = top_group.archive_users.count()
            
            return format_html(
                '<span style="color: {}; font-weight: bold; background: {}; padding: 2px 6px; border-radius: 3px; color: white;">{}</span>'
                '<br/><small style="color: #666;">Priority: {} | {} members</small>',
                '#ffffff' if top_group.color in ['#000000', '#000'] else '#000000',
                top_group.color or '#666666',
                top_group.name,
                top_group.priority,
                member_count
            )
        return '-'
    top_group_display.short_description = 'Top Group'
    
    def profile_analytics(self, obj):
        # Comprehensive profile analytics
        user_topics = obj.user.archive_topics.count() if obj.user else 0
        user_posts = obj.user.archive_posts.count() if obj.user else 0
        
        # Calculate engagement metrics
        if obj.user:
            # Topic engagement - use fresh querysets to avoid annotation conflicts
            user_topic_queryset = models.ArchiveTopic.objects.filter(author=obj.user)
            total_replies = user_topic_queryset.aggregate(
                total=Sum('total_replies')
            )['total'] or 0
            
            total_views = user_topic_queryset.aggregate(
                total=Sum('total_views')
            )['total'] or 0
            
            # Average post length - use fresh queryset to avoid annotation conflicts
            user_post_queryset = models.ArchivePost.objects.filter(author=obj.user)
            avg_post_length = user_post_queryset.aggregate(
                avg_len=Avg(Length('text'))
            )['avg_len'] or 0
            
            # Account age and activity rate
            account_age = (timezone.now() - obj.user.date_joined).days or 1
            activity_rate = (user_topics + user_posts) / account_age
            
            analytics_html = f"""
            <table style="width: 100%; border-collapse: collapse;">
                <tr><th colspan="2" style="text-align: left; padding: 4px; border-bottom: 1px solid #ddd;">Profile Analytics</th></tr>
                <tr><td style="padding: 2px 4px;">Account Age:</td><td style="padding: 2px 4px;"><strong>{account_age} days</strong></td></tr>
                <tr><td style="padding: 2px 4px;">Activity Rate:</td><td style="padding: 2px 4px;"><strong>{activity_rate:.2f} actions/day</strong></td></tr>
                <tr><td style="padding: 2px 4px;">Topics Created:</td><td style="padding: 2px 4px;"><strong>{user_topics}</strong></td></tr>
                <tr><td style="padding: 2px 4px;">Posts Created:</td><td style="padding: 2px 4px;"><strong>{user_posts}</strong></td></tr>
                <tr><td style="padding: 2px 4px;">Replies Received:</td><td style="padding: 2px 4px;"><strong>{total_replies}</strong></td></tr>
                <tr><td style="padding: 2px 4px;">Total Views:</td><td style="padding: 2px 4px;"><strong>{total_views:,}</strong></td></tr>
                <tr><td style="padding: 2px 4px;">Avg Post Length:</td><td style="padding: 2px 4px;"><strong>{int(avg_post_length)} chars</strong></td></tr>
                <tr><td style="padding: 2px 4px;">Content Ratio:</td><td style="padding: 2px 4px;"><strong>{user_posts/max(user_topics, 1):.1f} posts/topic</strong></td></tr>
            </table>
            """
            
            return format_html(analytics_html)
        
        return 'No analytics available'
    profile_analytics.short_description = 'Profile Analytics'
    
    def social_metrics(self, obj):
        # Social interaction metrics
        if not obj.user:
            return 'No user data'
        
        # Get topics with high engagement
        popular_topics = obj.user.archive_topics.filter(
            total_replies__gt=5
        ).count()
        
        # Get groups information
        total_groups = obj.groups.count()
        staff_groups = obj.groups.filter(is_staff_group=True).count()
        
        # Calculate influence score
        influence_factors = {
            'messages': min(obj.messages_count / 100, 10),  # Max 10 points
            'topics': min(obj.user.archive_topics.count() / 10, 5),  # Max 5 points
            'popular_topics': min(popular_topics * 2, 10),  # Max 10 points
            'groups': min(total_groups, 5),  # Max 5 points
            'staff': 10 if staff_groups > 0 else 0,  # 10 points if staff
        }
        
        total_influence = sum(influence_factors.values())
        
        metrics_html = f"""
        <table style="border-collapse: collapse;">
            <tr><th colspan="2" style="text-align: left; padding: 4px; border-bottom: 1px solid #ddd;">Social Metrics</th></tr>
            <tr><td style="padding: 2px 4px;">Popular Topics:</td><td style="padding: 2px 4px;"><strong>{popular_topics}</strong></td></tr>
            <tr><td style="padding: 2px 4px;">Total Groups:</td><td style="padding: 2px 4px;"><strong>{total_groups}</strong></td></tr>
            <tr><td style="padding: 2px 4px;">Staff Groups:</td><td style="padding: 2px 4px;"><strong>{staff_groups}</strong></td></tr>
            <tr><td style="padding: 2px 4px;">Influence Score:</td><td style="padding: 2px 4px;"><strong>{total_influence:.1f}/40</strong></td></tr>
        </table>
        """
        
        return format_html(metrics_html)
    social_metrics.short_description = 'Social Metrics'
    
    def content_quality_score(self, obj):
        # Calculate content quality based on various factors
        if not obj.user:
            return 'No user data'
        
        posts = obj.user.archive_posts.all()
        topics = obj.user.archive_topics.all()
        
        if not posts.exists() and not topics.exists():
            return 'No content to analyze'
        
        # Quality factors
        quality_score = 0
        factors = []
        
        # Average post length (good content usually has reasonable length)
        if posts.exists():
            post_queryset = models.ArchivePost.objects.filter(author=obj.user) if obj.user else models.ArchivePost.objects.none()
            avg_length = post_queryset.aggregate(avg=Avg(Length('text')))['avg'] or 0
            if 100 <= avg_length <= 1000:  # Sweet spot
                quality_score += 25
                factors.append('[+] Good post length')
            else:
                factors.append('[x] Poor post length')
        
        # Topic engagement - use fresh queryset to avoid annotation conflicts
        if topics.exists():
            topic_queryset = models.ArchiveTopic.objects.filter(author=obj.user) if obj.user else models.ArchiveTopic.objects.none()
            avg_replies = topic_queryset.aggregate(avg=Avg('total_replies'))['avg'] or 0
            if avg_replies >= 3:
                quality_score += 25
                factors.append('[+] Engaging topics')
            else:
                factors.append('[x] Low engagement topics')
        
        # Consistency (regular posting)
        if posts.exists():
            post_queryset_span = models.ArchivePost.objects.filter(author=obj.user) if obj.user else models.ArchivePost.objects.none()
            post_span = post_queryset_span.aggregate(
                min_date=Min('created_time'),
                max_date=Max('created_time')
            )
            if post_span['min_date'] and post_span['max_date']:
                span_days = (post_span['max_date'] - post_span['min_date']).days or 1
                consistency = posts.count() / span_days
                if consistency >= 0.1:  # At least 1 post per 10 days
                    quality_score += 25
                    factors.append('[+] Consistent posting')
                else:
                    factors.append('[x] Inconsistent posting')
        
        # Profile completion bonus
        if self.profile_completion(obj):  # If profile is well filled
            quality_score += 25
            factors.append('[+] Complete profile')
        else:
            factors.append('[x] Incomplete profile')
        
        return format_html(
            '<strong>{}%</strong><br/><small>{}</small>',
            quality_score, '<br/>'.join(factors)
        )
    content_quality_score.short_description = 'Content Quality'
    
    def forum_influence(self, obj):
        # Calculate forum influence
        if not obj.user:
            return 'No user data'
        
        # Influence indicators - use fresh querysets to avoid annotation conflicts
        user_topic_queryset = models.ArchiveTopic.objects.filter(author=obj.user)
        total_views = user_topic_queryset.aggregate(
            total=Sum('total_views')
        )['total'] or 0
        
        total_replies = user_topic_queryset.aggregate(
            total=Sum('total_replies')
        )['total'] or 0
        
        # Rank among all users by message count
        users_with_more_messages = models.ArchiveProfile.objects.filter(
            messages_count__gt=obj.messages_count
        ).count()
        
        total_users = models.ArchiveProfile.objects.count()
        percentile = ((total_users - users_with_more_messages) / max(total_users, 1)) * 100
        
        influence_html = f"""
        <table style="border-collapse: collapse;">
            <tr><th colspan="2" style="text-align: left; padding: 4px; border-bottom: 1px solid #ddd;">Forum Influence</th></tr>
            <tr><td style="padding: 2px 4px;">Total Content Views:</td><td style="padding: 2px 4px;"><strong>{total_views:,}</strong></td></tr>
            <tr><td style="padding: 2px 4px;">Replies Generated:</td><td style="padding: 2px 4px;"><strong>{total_replies}</strong></td></tr>
            <tr><td style="padding: 2px 4px;">User Rank:</td><td style="padding: 2px 4px;"><strong>Top {100-percentile:.1f}%</strong></td></tr>
            <tr><td style="padding: 2px 4px;">Position:</td><td style="padding: 2px 4px;"><strong>#{users_with_more_messages + 1} of {total_users}</strong></td></tr>
        </table>
        """
        
        return format_html(influence_html)
    forum_influence.short_description = 'Forum Influence'
    
    def profile_completion_details(self, obj):
        # Detailed profile completion breakdown
        fields = {
            'Description': obj.desc,
            'Location': obj.localisation,
            'Hobbies': obj.loisirs,
            'Birthdate': obj.birthdate,
            'Favorite Games': obj.favorite_games,
            'Zodiac Sign': obj.zodiac_sign,
            'Gender': obj.gender,
            'Website': obj.website,
            'Skype': obj.skype,
            'Signature': obj.signature,
            'Profile Picture': obj.profile_picture,
        }
        
        completion_html = '<table style="border-collapse: collapse;">'
        completion_html += '<tr><th colspan="2" style="text-align: left; padding: 4px; border-bottom: 1px solid #ddd;">Profile Completion Details</th></tr>'
        
        for field_name, field_value in fields.items():
            status = '[+]' if field_value else '[x]'
            completion_html += f'<tr><td style="padding: 2px 4px;">{field_name}:</td><td style="padding: 2px 4px;">{status}</td></tr>'
        
        completion_html += '</table>'
        
        return format_html(completion_html)
    profile_completion_details.short_description = 'Completion Details'
    
    # Admin actions
    def promote_users(self, request, queryset):
        # Promote users based on message count
        promoted = 0
        for profile in queryset:
            # Find appropriate groups for promotion
            eligible_groups = models.ArchiveForumGroup.objects.filter(
                is_messages_group=True,
                minimum_messages__lte=profile.messages_count
            ).exclude(
                id__in=profile.groups.values_list('id', flat=True)
            )
            
            for group in eligible_groups:
                profile.groups.add(group)
                promoted += 1
        
        self.message_user(request, f'Promoted {promoted} users to new groups.')
    promote_users.short_description = 'Promote users based on message count'
    
    def update_group_colors(self, request, queryset):
        # Update name colors based on top group
        updated = 0
        for profile in queryset:
            top_group = profile.get_top_group
            if top_group and top_group.color:
                profile.name_color = top_group.color
                profile.save(update_fields=['name_color'])
                updated += 1
        
        self.message_user(request, f'Updated name colors for {updated} profiles.')
    update_group_colors.short_description = 'Update name colors from top group'
    
    def generate_profile_report(self, request, queryset):
        # Generate a summary report
        total_profiles = queryset.count()
        avg_messages = queryset.aggregate(avg=Avg('messages_count'))['avg'] or 0
        
        self.message_user(
            request, 
            f'Report: {total_profiles} profiles selected, average {float(avg_messages):.1f} messages per user.'
        )
    generate_profile_report.short_description = 'Generate profile report'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user', 'top_group'
        ).prefetch_related('groups')
    
    def save_model(self, request, obj, form, change):
        # Save the basic model fields first (excluding M2M)
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        # Save M2M fields now (including groups)
        super().save_related(request, form, formsets, change)

        # Now M2M fields are saved — we can safely update name_color
        user = form.instance
        top_group = user.get_top_group
        user.name_color = top_group.color if top_group and top_group.color else "#FFFFFF"
        user.save(update_fields=['name_color'])