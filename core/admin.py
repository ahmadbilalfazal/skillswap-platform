from django.contrib import admin
from .models import (
    Profile, Skill, UserSkill, SkillSwapRequest, ExchangeSession, Review,
    Favorite, ProofArtifact, Badge, UserBadge, WeeklyChallenge,
    ChallengeSubmission, UserReport, Notification, GrowthEvent, ChatMessage, VerificationRequest, PeerChallenge
)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'availability', 'location', 'is_verified_peer', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'bio')
    list_filter = ('availability', 'is_verified_peer')


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'slug')
    search_fields = ('name',)
    list_filter = ('category',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    list_display = ('user', 'skill', 'type', 'level')
    search_fields = ('user__username', 'skill__name')
    list_filter = ('type', 'level')


@admin.register(SkillSwapRequest)
class SkillSwapRequestAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'teach_skill', 'learn_skill', 'status', 'created_at')
    list_filter = ('status', 'teach_skill', 'learn_skill')
    search_fields = ('sender__username', 'receiver__username', 'message')


@admin.register(ExchangeSession)
class ExchangeSessionAdmin(admin.ModelAdmin):
    list_display = ('request', 'scheduled_at', 'duration_minutes', 'is_completed', 'video_room_slug')
    list_filter = ('is_completed',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('reviewer', 'reviewed_user', 'rating', 'created_at')
    list_filter = ('rating',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__username', 'title', 'message')


@admin.register(GrowthEvent)
class GrowthEventAdmin(admin.ModelAdmin):
    list_display = ('user', 'event_type', 'title', 'created_at')
    list_filter = ('event_type', 'created_at')
    search_fields = ('user__username', 'title', 'description')


admin.site.register(Favorite)
admin.site.register(ProofArtifact)
admin.site.register(Badge)
admin.site.register(UserBadge)
admin.site.register(WeeklyChallenge)
admin.site.register(ChallengeSubmission)
admin.site.register(UserReport)


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('session', 'sender', 'created_at')
    search_fields = ('sender__username', 'message')
    list_filter = ('created_at',)


@admin.register(VerificationRequest)
class VerificationRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'headline', 'status', 'reviewed_by', 'created_at')
    search_fields = ('user__username', 'headline', 'proof_links', 'motivation')
    list_filter = ('status', 'created_at')


@admin.register(PeerChallenge)
class PeerChallengeAdmin(admin.ModelAdmin):
    list_display = ('title', 'creator', 'target', 'mode', 'status', 'due_at', 'created_at')
    search_fields = ('title', 'description', 'creator__username', 'target__username')
    list_filter = ('status', 'mode', 'created_at')
