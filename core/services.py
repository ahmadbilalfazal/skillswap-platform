from django.contrib.auth.models import User
from django.db.models import Q
from django.urls import reverse
from .models import (
    UserSkill, Favorite, Review, ExchangeSession, SkillSwapRequest,
    Notification, GrowthEvent, Badge, UserBadge, ProofArtifact, ChallengeSubmission, PeerChallenge
)


def user_have_skills(user):
    return set(UserSkill.objects.filter(user=user, type=UserSkill.HAVE).values_list('skill_id', flat=True))


def user_want_skills(user):
    return set(UserSkill.objects.filter(user=user, type=UserSkill.WANT).values_list('skill_id', flat=True))


def calculate_match_score(current_user, candidate):
    current_have = user_have_skills(current_user)
    current_want = user_want_skills(current_user)
    candidate_have = user_have_skills(candidate)
    candidate_want = user_want_skills(candidate)

    can_teach_me = current_want.intersection(candidate_have)
    i_can_teach = current_have.intersection(candidate_want)
    reciprocal = bool(can_teach_me and i_can_teach)

    score = 0
    if reciprocal:
        score += 50
    elif can_teach_me:
        score += 30

    if current_user.profile.availability == candidate.profile.availability or candidate.profile.availability == 'flexible':
        score += 15

    score += min(candidate.profile.average_rating * 5, 25)
    score += min(candidate.profile.completed_sessions_count * 2, 10)

    return {
        'user': candidate,
        'score': int(score),
        'can_teach_me_count': len(can_teach_me),
        'i_can_teach_count': len(i_can_teach),
        'reciprocal': reciprocal,
    }


def get_weighted_matches(current_user, limit=20):
    candidates = User.objects.filter(is_active=True).exclude(id=current_user.id).select_related('profile')
    results = [calculate_match_score(current_user, candidate) for candidate in candidates]
    results = [item for item in results if item['score'] > 0]
    return sorted(results, key=lambda item: item['score'], reverse=True)[:limit]


def leaderboard_rows(limit=20):
    users = User.objects.filter(is_active=True).select_related('profile')
    rows = []
    for user in users:
        rows.append({
            'user': user,
            'rating': user.profile.average_rating,
            'completed': user.profile.completed_sessions_count,
            'badges': user.badges.count(),
            'score': (user.profile.completed_sessions_count * 10) + int(user.profile.average_rating * 8) + (user.badges.count() * 5),
        })
    return sorted(rows, key=lambda row: row['score'], reverse=True)[:limit]


def notify_user(user, title, message='', url=''):
    if user and user.is_authenticated:
        Notification.objects.create(user=user, title=title, message=message, url=url)


def add_growth_event(user, event_type, title, description='', icon='✨', url=''):
    if user and user.is_authenticated:
        GrowthEvent.objects.create(
            user=user,
            event_type=event_type,
            title=title,
            description=description,
            icon=icon,
            url=url,
        )


def _award_badge(user, name, description, icon='🏅'):
    badge, _ = Badge.objects.get_or_create(
        name=name,
        defaults={'description': description, 'icon': icon},
    )
    user_badge, created = UserBadge.objects.get_or_create(user=user, badge=badge)
    if created:
        add_growth_event(
            user=user,
            event_type='badge',
            title=f'Earned {name}',
            description=description,
            icon=icon,
            url=reverse('profile_detail', args=[user.username]),
        )
        notify_user(user, f'Badge earned: {name}', description, reverse('profile_detail', args=[user.username]))
    return created


def award_badges_for_user(user):
    completed = user.profile.completed_sessions_count
    avg_rating = user.profile.average_rating
    review_count = Review.objects.filter(reviewed_user=user).count()
    proof_count = ProofArtifact.objects.filter(added_by=user).count()
    peer_challenge_count = PeerChallenge.objects.filter(status=PeerChallenge.COMPLETED).filter(Q(creator=user) | Q(target=user)).count()
    challenge_count = ChallengeSubmission.objects.filter(user=user).count() + peer_challenge_count

    if completed >= 1:
        _award_badge(user, 'First Skill Swap', 'Completed your first verified skill exchange session.', '🚀')
    if completed >= 5:
        _award_badge(user, 'Consistent Swapper', 'Completed five skill exchange sessions.', '🔥')
    if avg_rating >= 4.5 and review_count >= 3:
        _award_badge(user, 'Trusted Peer', 'Maintained a strong rating across multiple reviews.', '⭐')
    if proof_count >= 3:
        _award_badge(user, 'Proof Builder', 'Added three pieces of learning proof.', '📌')
    if challenge_count >= 1:
        _award_badge(user, 'Challenge Starter', 'Submitted your first weekly or peer challenge.', '🏆')
    if peer_challenge_count >= 1:
        _award_badge(user, 'Peer Challenger', 'Completed a direct challenge with another peer.', '⚡')


def challenge_leaderboard_rows(limit=20):
    users = User.objects.filter(is_active=True).select_related('profile')
    rows = []
    for user in users:
        submissions = ChallengeSubmission.objects.filter(user=user)
        submission_count = submissions.count()
        peer_count = PeerChallenge.objects.filter(status=PeerChallenge.COMPLETED).filter(Q(creator=user) | Q(target=user)).count()
        total_score = sum(item.score for item in submissions)
        if submission_count or peer_count or user.profile.completed_sessions_count:
            rows.append({
                'user': user,
                'submissions': submission_count + peer_count,
                'challenge_score': total_score + (peer_count * 20),
                'completed': user.profile.completed_sessions_count,
                'rating': user.profile.average_rating,
                'score': total_score + (submission_count * 15) + (peer_count * 20) + (user.profile.completed_sessions_count * 5) + int(user.profile.average_rating * 5),
            })
    return sorted(rows, key=lambda row: row['score'], reverse=True)[:limit]
