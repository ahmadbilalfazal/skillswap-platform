from django.conf import settings
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Avg
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
import uuid


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Profile(TimeStampedModel):
    AVAILABILITY_CHOICES = [
        ('weekdays', 'Weekdays'),
        ('weekends', 'Weekends'),
        ('evenings', 'Evenings'),
        ('flexible', 'Flexible'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True)
    availability = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default='flexible')
    location = models.CharField(max_length=120, blank=True)
    avatar_url = models.URLField(blank=True)
    is_verified_peer = models.BooleanField(default=False)

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    @property
    def average_rating(self):
        value = self.user.received_reviews.aggregate(avg=Avg('rating'))['avg']
        return round(value or 0, 1)

    @property
    def completed_sessions_count(self):
        return ExchangeSession.objects.filter(
            is_completed=True,
            request__status=SkillSwapRequest.ACCEPTED,
        ).filter(
            models.Q(request__sender=self.user) | models.Q(request__receiver=self.user)
        ).count()


class Skill(TimeStampedModel):
    CATEGORY_CHOICES = [
        ('programming', 'Programming'),
        ('design', 'Design'),
        ('video', 'Video Editing'),
        ('communication', 'Communication'),
        ('business', 'Business'),
        ('language', 'Language'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=80, unique=True)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='other')
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class UserSkill(TimeStampedModel):
    HAVE = 'have'
    WANT = 'want'
    SKILL_TYPE_CHOICES = [
        (HAVE, 'I can teach this'),
        (WANT, 'I want to learn this'),
    ]
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_skills')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='user_skills')
    type = models.CharField(max_length=10, choices=SKILL_TYPE_CHOICES)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner')

    class Meta:
        unique_together = ('user', 'skill', 'type')
        ordering = ['type', 'skill__name']

    def __str__(self):
        return f'{self.user.username} - {self.skill.name} ({self.type})'


class SkillSwapRequest(TimeStampedModel):
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'
    CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (ACCEPTED, 'Accepted'),
        (REJECTED, 'Rejected'),
        (CANCELLED, 'Cancelled'),
    ]

    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_swap_requests')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_swap_requests')
    teach_skill = models.ForeignKey(Skill, on_delete=models.PROTECT, related_name='swap_requests_as_teach')
    learn_skill = models.ForeignKey(Skill, on_delete=models.PROTECT, related_name='swap_requests_as_learn')
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.sender} -> {self.receiver}: {self.status}'


class ExchangeSession(TimeStampedModel):
    request = models.OneToOneField(SkillSwapRequest, on_delete=models.CASCADE, related_name='session')
    scheduled_at = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(default=45)
    session_notes = models.TextField(blank=True)
    mini_assignment = models.TextField(blank=True)
    learner_reflection = models.TextField(blank=True)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    video_room_slug = models.SlugField(max_length=120, unique=True, blank=True)

    class Meta:
        ordering = ['-scheduled_at', '-created_at']

    def save(self, *args, **kwargs):
        if not self.video_room_slug:
            self.video_room_slug = f'skillswap-{uuid.uuid4().hex[:12]}'
        if self.is_completed and not self.completed_at:
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)

    def participants(self):
        return [self.request.sender, self.request.receiver]

    def other_user(self, user):
        return self.request.receiver if user == self.request.sender else self.request.sender

    def __str__(self):
        return f'Session for request {self.request_id}'


class Review(TimeStampedModel):
    session = models.ForeignKey(ExchangeSession, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_reviews')
    reviewed_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_reviews')
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)

    class Meta:
        unique_together = ('session', 'reviewer', 'reviewed_user')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.rating}/5 by {self.reviewer} for {self.reviewed_user}'


class Favorite(TimeStampedModel):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    saved_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_by')

    class Meta:
        unique_together = ('owner', 'saved_user')

    def __str__(self):
        return f'{self.owner} saved {self.saved_user}'


class ProofArtifact(TimeStampedModel):
    session = models.ForeignKey(ExchangeSession, on_delete=models.CASCADE, related_name='proof_artifacts')
    title = models.CharField(max_length=140)
    description = models.TextField(blank=True)
    link = models.URLField(blank=True)
    added_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='proof_artifacts')

    def __str__(self):
        return self.title


class Badge(TimeStampedModel):
    name = models.CharField(max_length=80, unique=True)
    description = models.TextField()
    icon = models.CharField(max_length=10, default='🏅')

    def __str__(self):
        return self.name


class UserBadge(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='users')
    awarded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='awarded_badges')

    class Meta:
        unique_together = ('user', 'badge')

    def __str__(self):
        return f'{self.user} - {self.badge}'


class WeeklyChallenge(TimeStampedModel):
    title = models.CharField(max_length=160)
    description = models.TextField()
    starts_at = models.DateTimeField(default=timezone.now)
    ends_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-starts_at']

    def __str__(self):
        return self.title


class ChallengeSubmission(TimeStampedModel):
    challenge = models.ForeignKey(WeeklyChallenge, on_delete=models.CASCADE, related_name='submissions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='challenge_submissions')
    title = models.CharField(max_length=140)
    link = models.URLField(blank=True)
    reflection = models.TextField(blank=True)
    score = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('challenge', 'user')
        ordering = ['-score', '-created_at']

    def __str__(self):
        return f'{self.user} - {self.challenge}'

class PeerChallenge(TimeStampedModel):
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'
    CANCELLED = 'cancelled'
    COMPLETED = 'completed'
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (ACCEPTED, 'Accepted'),
        (REJECTED, 'Rejected'),
        (CANCELLED, 'Cancelled'),
        (COMPLETED, 'Completed'),
    ]

    SOLO = 'solo'
    SHARED = 'shared'
    MODE_CHOICES = [
        (SOLO, 'Challenge them only'),
        (SHARED, 'Challenge both of us'),
    ]

    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_peer_challenges')
    target = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_peer_challenges')
    title = models.CharField(max_length=160)
    description = models.TextField()
    skill_focus = models.CharField(max_length=120, blank=True, help_text='Example: Python, UI design, video editing')
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default=SHARED)
    due_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)

    creator_proof_title = models.CharField(max_length=140, blank=True)
    creator_proof_file = models.FileField(upload_to='peer_challenge_proofs/', blank=True, null=True)
    creator_reflection = models.TextField(blank=True)
    creator_completed_at = models.DateTimeField(null=True, blank=True)

    target_proof_title = models.CharField(max_length=140, blank=True)
    target_proof_file = models.FileField(upload_to='peer_challenge_proofs/', blank=True, null=True)
    target_reflection = models.TextField(blank=True)
    target_completed_at = models.DateTimeField(null=True, blank=True)

    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} ({self.creator} → {self.target})'

    def other_user(self, user):
        return self.target if user == self.creator else self.creator

    def user_has_submitted(self, user):
        if user == self.creator:
            return bool(self.creator_completed_at)
        if user == self.target:
            return bool(self.target_completed_at)
        return False

    @property
    def required_completion_count(self):
        return 1 if self.mode == self.SOLO else 2

    @property
    def submitted_count(self):
        return int(bool(self.target_completed_at)) + int(bool(self.creator_completed_at))

    @property
    def progress_percent(self):
        return int((self.submitted_count / self.required_completion_count) * 100)

    def refresh_completion_status(self):
        target_done = bool(self.target_completed_at)
        creator_done = bool(self.creator_completed_at)
        if target_done and (self.mode == self.SOLO or creator_done):
            self.status = self.COMPLETED
            if not self.completed_at:
                self.completed_at = timezone.now()
            self.save(update_fields=['status', 'completed_at', 'updated_at'])
            return True
        return False


class UserReport(TimeStampedModel):
    REASON_CHOICES = [
        ('spam', 'Spam'),
        ('abuse', 'Abuse or harassment'),
        ('fake', 'Fake profile'),
        ('unsafe', 'Unsafe behavior'),
        ('other', 'Other'),
    ]
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_made')
    reported_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_received')
    reason = models.CharField(max_length=30, choices=REASON_CHOICES)
    details = models.TextField(blank=True)
    is_resolved = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.reporter} reported {self.reported_user}'


class Notification(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=160)
    message = models.TextField(blank=True)
    url = models.CharField(max_length=220, blank=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} - {self.title}'


class GrowthEvent(TimeStampedModel):
    EVENT_CHOICES = [
        ('join', 'Joined'),
        ('skill', 'Skill added'),
        ('request', 'Request sent'),
        ('session', 'Session completed'),
        ('proof', 'Proof added'),
        ('review', 'Review received'),
        ('badge', 'Badge earned'),
        ('challenge', 'Challenge submitted'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='growth_events')
    event_type = models.CharField(max_length=30, choices=EVENT_CHOICES, default='session')
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=10, default='✨')
    url = models.CharField(max_length=220, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} - {self.title}'


class ChatMessage(TimeStampedModel):
    session = models.ForeignKey(ExchangeSession, on_delete=models.CASCADE, related_name='chat_messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='session_chat_messages')
    message = models.TextField()

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.sender} in session {self.session_id}'


class VerificationRequest(TimeStampedModel):
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_requests')
    headline = models.CharField(max_length=160, default='Peer verification request')
    proof_links = models.TextField(help_text='Add links to portfolio, GitHub, LinkedIn, certificates, or previous work.', blank=True)
    motivation = models.TextField(help_text='Explain why this account should be marked as a verified peer.', blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verification_reviews')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_note = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} verification: {self.status}'
