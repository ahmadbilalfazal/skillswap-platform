from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .forms import (
    RegisterForm, ProfileForm, UserSkillForm, SkillSwapRequestForm,
    ExchangeSessionForm, ReviewForm, ProofArtifactForm, ChallengeSubmissionForm,
    UserReportForm, ChatMessageForm, VerificationRequestForm,
    PeerChallengeCreateForm, PeerChallengeProofForm
)
from .models import (
    UserSkill, Skill, SkillSwapRequest, ExchangeSession, Review, Favorite,
    WeeklyChallenge, ChallengeSubmission, UserReport, Notification, GrowthEvent,
    ChatMessage, VerificationRequest, PeerChallenge
)
from .services import (
    get_weighted_matches, leaderboard_rows, notify_user, add_growth_event,
    award_badges_for_user, challenge_leaderboard_rows
)


def home(request):
    return render(request, 'core/home.html')


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            add_growth_event(user, 'join', 'Joined SkillSwap', 'Started a verified peer-learning journey.', '👋')
            messages.success(request, 'Welcome to SkillSwap! Complete your profile and add your first skills.')
            return redirect('dashboard')
    else:
        form = RegisterForm()
    return render(request, 'core/form_page.html', {'form': form, 'title': 'Create your account', 'button': 'Register'})


@login_required
def dashboard(request):
    received_requests = SkillSwapRequest.objects.filter(receiver=request.user).select_related('sender', 'teach_skill', 'learn_skill')[:6]
    sent_requests = SkillSwapRequest.objects.filter(sender=request.user).select_related('receiver', 'teach_skill', 'learn_skill')[:6]
    sessions = ExchangeSession.objects.filter(
        Q(request__sender=request.user) | Q(request__receiver=request.user)
    ).select_related('request', 'request__sender', 'request__receiver')[:6]
    matches = get_weighted_matches(request.user, limit=6)
    proof_count = request.user.proof_artifacts.count()
    badge_count = request.user.badges.count()
    unread_chat_count = ChatMessage.objects.filter(
        session__request__status=SkillSwapRequest.ACCEPTED,
    ).filter(
        Q(session__request__sender=request.user) | Q(session__request__receiver=request.user)
    ).exclude(sender=request.user).count()

    profile_complete = 20
    if request.user.profile.bio:
        profile_complete += 20
    if request.user.profile.location:
        profile_complete += 10
    if UserSkill.objects.filter(user=request.user, type=UserSkill.HAVE).exists():
        profile_complete += 25
    if UserSkill.objects.filter(user=request.user, type=UserSkill.WANT).exists():
        profile_complete += 25
    context = {
        'have_count': UserSkill.objects.filter(user=request.user, type=UserSkill.HAVE).count(),
        'want_count': UserSkill.objects.filter(user=request.user, type=UserSkill.WANT).count(),
        'proof_count': proof_count,
        'badge_count': badge_count,
        'unread_chat_count': unread_chat_count,
        'profile_complete': min(profile_complete, 100),
        'received_requests': received_requests,
        'sent_requests': sent_requests,
        'sessions': sessions,
        'matches': matches,
    }
    return render(request, 'core/dashboard.html', context)


@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('dashboard')
    else:
        form = ProfileForm(instance=request.user.profile)
    return render(request, 'core/form_page.html', {'form': form, 'title': 'Edit profile', 'button': 'Save profile'})


@login_required
def manage_skills(request):
    if request.method == 'POST':
        form = UserSkillForm(request.POST)
        if form.is_valid():
            skill, created = Skill.objects.get_or_create(
                name=form.cleaned_data['skill_name'].strip().title(),
                defaults={'category': form.cleaned_data['category']},
            )
            user_skill, user_skill_created = UserSkill.objects.get_or_create(
                user=request.user,
                skill=skill,
                type=form.cleaned_data['type'],
                defaults={'level': form.cleaned_data['level']},
            )
            if user_skill_created:
                label = 'Can teach' if user_skill.type == UserSkill.HAVE else 'Wants to learn'
                add_growth_event(
                    request.user,
                    'skill',
                    f'{label}: {skill.name}',
                    f'Added {skill.name} to the profile skill map.',
                    '🧠',
                    f'/profile/{request.user.username}/'
                )
            messages.success(request, 'Skill saved.')
            return redirect('manage_skills')
    else:
        form = UserSkillForm()

    have_skills = UserSkill.objects.filter(user=request.user, type=UserSkill.HAVE).select_related('skill')
    want_skills = UserSkill.objects.filter(user=request.user, type=UserSkill.WANT).select_related('skill')
    return render(request, 'core/manage_skills.html', {'form': form, 'have_skills': have_skills, 'want_skills': want_skills})


@login_required
def delete_user_skill(request, userskill_id):
    userskill = get_object_or_404(UserSkill, id=userskill_id, user=request.user)
    if request.method == 'POST':
        userskill.delete()
        messages.success(request, 'Skill removed.')
    return redirect('manage_skills')


@login_required
def explore_users(request):
    teach = request.GET.get('teach', '').strip()
    learn = request.GET.get('learn', '').strip()
    availability = request.GET.get('availability', '').strip()

    users = User.objects.filter(is_active=True).exclude(id=request.user.id).select_related('profile').prefetch_related('user_skills__skill')
    if teach:
        users = users.filter(user_skills__type=UserSkill.HAVE, user_skills__skill__name__icontains=teach)
    if learn:
        users = users.filter(user_skills__type=UserSkill.WANT, user_skills__skill__name__icontains=learn)
    if availability:
        users = users.filter(profile__availability=availability)

    users = list(users.distinct()[:60])
    matches = {item['user'].id: item for item in get_weighted_matches(request.user, limit=100)}
    user_cards = [{'user': user, 'match': matches.get(user.id)} for user in users]
    return render(request, 'core/explore.html', {
        'user_cards': user_cards,
        'teach': teach,
        'learn': learn,
        'availability': availability,
    })


@login_required
def profile_detail(request, username):
    profile_user = get_object_or_404(User, username=username, is_active=True)
    have_skills = UserSkill.objects.filter(user=profile_user, type=UserSkill.HAVE).select_related('skill')
    want_skills = UserSkill.objects.filter(user=profile_user, type=UserSkill.WANT).select_related('skill')
    reviews = Review.objects.filter(reviewed_user=profile_user).select_related('reviewer')[:10]
    growth_events = GrowthEvent.objects.filter(user=profile_user)[:12]
    is_favorite = Favorite.objects.filter(owner=request.user, saved_user=profile_user).exists() if request.user.is_authenticated else False
    latest_verification = VerificationRequest.objects.filter(user=profile_user).first()
    return render(request, 'core/profile_detail.html', {
        'profile_user': profile_user,
        'have_skills': have_skills,
        'want_skills': want_skills,
        'reviews': reviews,
        'growth_events': growth_events,
        'is_favorite': is_favorite,
        'latest_verification': latest_verification,
    })


@login_required
def send_swap_request(request, username):
    receiver = get_object_or_404(User, username=username, is_active=True)
    if receiver == request.user:
        messages.error(request, 'You cannot send a request to yourself.')
        return redirect('profile_detail', username=username)

    if request.method == 'POST':
        form = SkillSwapRequestForm(request.POST, sender=request.user, receiver=receiver)
        if form.is_valid():
            swap_request = form.save(commit=False)
            swap_request.sender = request.user
            swap_request.receiver = receiver
            swap_request.save()
            notify_user(
                receiver,
                'New skill swap request',
                f'{request.user.username} wants to exchange {swap_request.teach_skill} for {swap_request.learn_skill}.',
                f'/request/{request.user.username}/'
            )
            add_growth_event(
                request.user,
                'request',
                f'Requested swap with {receiver.username}',
                f'{swap_request.teach_skill} ↔ {swap_request.learn_skill}',
                '🤝',
                f'/profile/{receiver.username}/'
            )
            messages.success(request, 'Skill exchange request sent.')
            return redirect('dashboard')
    else:
        form = SkillSwapRequestForm(sender=request.user, receiver=receiver)
    return render(request, 'core/form_page.html', {'form': form, 'title': f'Send request to {receiver.username}', 'button': 'Send request'})


@login_required
def accept_swap_request(request, request_id):
    swap_request = get_object_or_404(SkillSwapRequest, id=request_id, receiver=request.user, status=SkillSwapRequest.PENDING)
    if request.method == 'POST':
        swap_request.status = SkillSwapRequest.ACCEPTED
        swap_request.save()
        session, _ = ExchangeSession.objects.get_or_create(request=swap_request)
        ChatMessage.objects.get_or_create(
            session=session,
            sender=request.user,
            message='Session created. Use this space to agree timing, goals, and next steps.'
        )
        notify_user(
            swap_request.sender,
            'Request accepted',
            f'{request.user.username} accepted your skill swap request.',
            f'/sessions/{session.id}/'
        )
        add_growth_event(request.user, 'request', f'Accepted request from {swap_request.sender.username}', f'{swap_request.teach_skill} ↔ {swap_request.learn_skill}', '✅', f'/sessions/{session.id}/')
        add_growth_event(swap_request.sender, 'request', f'Request accepted by {request.user.username}', f'{swap_request.teach_skill} ↔ {swap_request.learn_skill}', '✅', f'/sessions/{session.id}/')
        messages.success(request, 'Request accepted. A session has been created.')
    return redirect('dashboard')


@login_required
def reject_swap_request(request, request_id):
    swap_request = get_object_or_404(SkillSwapRequest, id=request_id, receiver=request.user, status=SkillSwapRequest.PENDING)
    if request.method == 'POST':
        swap_request.status = SkillSwapRequest.REJECTED
        swap_request.save()
        notify_user(swap_request.sender, 'Request rejected', f'{request.user.username} rejected your skill swap request.', '/dashboard/')
        messages.info(request, 'Request rejected.')
    return redirect('dashboard')


@login_required
def cancel_swap_request(request, request_id):
    swap_request = get_object_or_404(SkillSwapRequest, id=request_id, sender=request.user, status=SkillSwapRequest.PENDING)
    if request.method == 'POST':
        swap_request.status = SkillSwapRequest.CANCELLED
        swap_request.save()
        notify_user(swap_request.receiver, 'Request cancelled', f'{request.user.username} cancelled a pending skill swap request.', '/dashboard/')
        messages.info(request, 'Request cancelled.')
    return redirect('dashboard')


@login_required
def sessions_list(request):
    sessions = ExchangeSession.objects.filter(
        Q(request__sender=request.user) | Q(request__receiver=request.user)
    ).select_related('request', 'request__sender', 'request__receiver')
    return render(request, 'core/sessions_list.html', {'sessions': sessions})


@login_required
def session_detail(request, session_id):
    session = get_object_or_404(
        ExchangeSession,
        Q(request__sender=request.user) | Q(request__receiver=request.user),
        id=session_id,
    )
    if request.method == 'POST':
        form = ExchangeSessionForm(request.POST, instance=session)
        if form.is_valid():
            form.save()
            other_user = session.other_user(request.user)
            notify_user(other_user, 'Session updated', f'{request.user.username} updated session details.', f'/sessions/{session.id}/')
            messages.success(request, 'Session details updated.')
            return redirect('session_detail', session_id=session.id)
    else:
        form = ExchangeSessionForm(instance=session)
    chat_form = ChatMessageForm()
    chat_messages = session.chat_messages.select_related('sender')[:100]
    return render(request, 'core/session_detail.html', {
        'session': session,
        'form': form,
        'chat_form': chat_form,
        'chat_messages': chat_messages,
    })


@login_required
def send_session_message(request, session_id):
    session = get_object_or_404(
        ExchangeSession,
        Q(request__sender=request.user) | Q(request__receiver=request.user),
        id=session_id,
    )
    if request.method == 'POST':
        form = ChatMessageForm(request.POST)
        if form.is_valid():
            chat = form.save(commit=False)
            chat.session = session
            chat.sender = request.user
            chat.save()
            other_user = session.other_user(request.user)
            notify_user(other_user, 'New session message', f'{request.user.username} sent a message in your session.', f'/sessions/{session.id}/')
    return redirect('session_detail', session_id=session.id)


@login_required
def chat_inbox(request):
    sessions = ExchangeSession.objects.filter(
        Q(request__sender=request.user) | Q(request__receiver=request.user)
    ).select_related('request', 'request__sender', 'request__receiver').prefetch_related('chat_messages')
    return render(request, 'core/chat_inbox.html', {'sessions': sessions})


@login_required
def complete_session(request, session_id):
    session = get_object_or_404(ExchangeSession, Q(request__sender=request.user) | Q(request__receiver=request.user), id=session_id)
    if request.method == 'POST':
        session.is_completed = True
        session.completed_at = timezone.now()
        session.save()
        other_user = session.other_user(request.user)
        notify_user(other_user, 'Session marked completed', f'{request.user.username} marked your session as completed.', f'/sessions/{session.id}/')
        add_growth_event(request.user, 'session', 'Completed a skill swap session', f'{session.request.teach_skill} ↔ {session.request.learn_skill}', '🎯', f'/sessions/{session.id}/')
        add_growth_event(other_user, 'session', 'Completed a skill swap session', f'{session.request.teach_skill} ↔ {session.request.learn_skill}', '🎯', f'/sessions/{session.id}/')
        award_badges_for_user(request.user)
        award_badges_for_user(other_user)
        messages.success(request, 'Session marked completed. Please leave a review.')
    return redirect('session_detail', session_id=session.id)


@login_required
def review_session(request, session_id):
    session = get_object_or_404(ExchangeSession, Q(request__sender=request.user) | Q(request__receiver=request.user), id=session_id, is_completed=True)
    reviewed_user = session.other_user(request.user)
    existing = Review.objects.filter(session=session, reviewer=request.user, reviewed_user=reviewed_user).first()
    if existing:
        messages.info(request, 'You already reviewed this session.')
        return redirect('session_detail', session_id=session.id)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.session = session
            review.reviewer = request.user
            review.reviewed_user = reviewed_user
            review.save()
            notify_user(reviewed_user, 'New review received', f'{request.user.username} rated you {review.rating}/5.', f'/profile/{reviewed_user.username}/')
            add_growth_event(reviewed_user, 'review', f'Received {review.rating}/5 review', review.comment[:140], '⭐', f'/profile/{reviewed_user.username}/')
            award_badges_for_user(reviewed_user)
            messages.success(request, 'Review added.')
            return redirect('profile_detail', username=reviewed_user.username)
    else:
        form = ReviewForm()
    return render(request, 'core/form_page.html', {'form': form, 'title': f'Review {reviewed_user.username}', 'button': 'Submit review'})


@login_required
def add_proof(request, session_id):
    session = get_object_or_404(ExchangeSession, Q(request__sender=request.user) | Q(request__receiver=request.user), id=session_id)
    if request.method == 'POST':
        form = ProofArtifactForm(request.POST)
        if form.is_valid():
            proof = form.save(commit=False)
            proof.session = session
            proof.added_by = request.user
            proof.save()
            other_user = session.other_user(request.user)
            notify_user(other_user, 'New proof added', f'{request.user.username} added proof to your shared session.', f'/sessions/{session.id}/')
            add_growth_event(request.user, 'proof', proof.title, proof.description[:160], '📌', f'/sessions/{session.id}/')
            award_badges_for_user(request.user)
            messages.success(request, 'Proof added to the session timeline.')
            return redirect('session_detail', session_id=session.id)
    else:
        form = ProofArtifactForm()
    return render(request, 'core/form_page.html', {'form': form, 'title': 'Add proof of learning', 'button': 'Add proof'})


@login_required
def favorites_list(request):
    favorites = Favorite.objects.filter(owner=request.user).select_related('saved_user', 'saved_user__profile')
    return render(request, 'core/favorites.html', {'favorites': favorites})


@login_required
def toggle_favorite(request, username):
    saved_user = get_object_or_404(User, username=username, is_active=True)
    if saved_user == request.user:
        return redirect('profile_detail', username=username)
    favorite, created = Favorite.objects.get_or_create(owner=request.user, saved_user=saved_user)
    if not created:
        favorite.delete()
        messages.info(request, 'Removed from favorites.')
    else:
        messages.success(request, 'Added to favorites.')
    return redirect('profile_detail', username=username)


@login_required
def leaderboard(request):
    return render(request, 'core/leaderboard.html', {'rows': leaderboard_rows(limit=30)})


@login_required
def challenges_list(request):
    challenges = WeeklyChallenge.objects.filter(is_active=True)
    rows = challenge_leaderboard_rows(limit=10)
    return render(request, 'core/challenges.html', {'challenges': challenges, 'rows': rows})


@login_required
def challenge_leaderboard(request):
    return render(request, 'core/challenge_leaderboard.html', {'rows': challenge_leaderboard_rows(limit=50)})


@login_required
def challenge_detail(request, challenge_id):
    challenge = get_object_or_404(WeeklyChallenge, id=challenge_id)
    submission = ChallengeSubmission.objects.filter(challenge=challenge, user=request.user).first()
    if request.method == 'POST' and not submission:
        form = ChallengeSubmissionForm(request.POST)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.challenge = challenge
            submission.user = request.user
            submission.save()
            add_growth_event(request.user, 'challenge', f'Completed challenge: {challenge.title}', submission.reflection[:160], '🏆', f'/challenges/{challenge.id}/')
            award_badges_for_user(request.user)
            messages.success(request, 'Challenge submission posted.')
            return redirect('challenge_detail', challenge_id=challenge.id)
    else:
        form = ChallengeSubmissionForm()
    submissions = challenge.submissions.select_related('user').all()
    return render(request, 'core/challenge_detail.html', {'challenge': challenge, 'form': form, 'submission': submission, 'submissions': submissions})


@login_required
def peer_challenges_list(request):
    challenges = PeerChallenge.objects.filter(
        Q(creator=request.user) | Q(target=request.user)
    ).select_related('creator', 'target')
    pending_received = challenges.filter(target=request.user, status=PeerChallenge.PENDING)
    active = challenges.filter(status=PeerChallenge.ACCEPTED)
    completed = challenges.filter(status=PeerChallenge.COMPLETED)
    sent = challenges.filter(creator=request.user).exclude(status=PeerChallenge.COMPLETED)
    return render(request, 'core/peer_challenges.html', {
        'pending_received': pending_received,
        'active': active,
        'completed': completed,
        'sent': sent,
    })


@login_required
def create_peer_challenge(request, username):
    target = get_object_or_404(User, username=username, is_active=True)
    if target == request.user:
        messages.error(request, 'You cannot challenge yourself from your own profile.')
        return redirect('profile_detail', username=username)

    if request.method == 'POST':
        form = PeerChallengeCreateForm(request.POST)
        if form.is_valid():
            challenge = form.save(commit=False)
            challenge.creator = request.user
            challenge.target = target
            challenge.status = PeerChallenge.PENDING
            challenge.save()
            notify_user(
                target,
                'New peer challenge',
                f'{request.user.username} challenged you: {challenge.title}',
                f'/peer-challenges/{challenge.id}/'
            )
            add_growth_event(
                request.user,
                'challenge',
                f'Created peer challenge for {target.username}',
                challenge.title,
                '⚡',
                f'/peer-challenges/{challenge.id}/'
            )
            messages.success(request, 'Challenge sent. Your friend can accept or reject it.')
            return redirect('peer_challenge_detail', challenge_id=challenge.id)
    else:
        form = PeerChallengeCreateForm()
    return render(request, 'core/form_page.html', {
        'form': form,
        'title': f'Challenge {target.username}',
        'button': 'Send challenge',
    })


@login_required
def peer_challenge_detail(request, challenge_id):
    challenge = get_object_or_404(
        PeerChallenge,
        Q(creator=request.user) | Q(target=request.user),
        id=challenge_id,
    )
    proof_form = PeerChallengeProofForm()
    user_has_submitted = challenge.user_has_submitted(request.user)
    can_submit_proof = (
        challenge.status == PeerChallenge.ACCEPTED
        and not user_has_submitted
        and not (challenge.mode == PeerChallenge.SOLO and request.user == challenge.creator)
    )
    can_cancel = challenge.creator == request.user and challenge.status in [PeerChallenge.PENDING, PeerChallenge.ACCEPTED]
    return render(request, 'core/peer_challenge_detail.html', {
        'challenge': challenge,
        'proof_form': proof_form,
        'user_has_submitted': user_has_submitted,
        'can_submit_proof': can_submit_proof,
        'can_cancel': can_cancel,
    })


@login_required
def accept_peer_challenge(request, challenge_id):
    challenge = get_object_or_404(PeerChallenge, id=challenge_id, target=request.user, status=PeerChallenge.PENDING)
    if request.method == 'POST':
        challenge.status = PeerChallenge.ACCEPTED
        challenge.save(update_fields=['status', 'updated_at'])
        notify_user(challenge.creator, 'Peer challenge accepted', f'{request.user.username} accepted: {challenge.title}', f'/peer-challenges/{challenge.id}/')
        add_growth_event(request.user, 'challenge', f'Accepted challenge from {challenge.creator.username}', challenge.title, '✅', f'/peer-challenges/{challenge.id}/')
        messages.success(request, 'Challenge accepted. Now submit proof when you complete it.')
    return redirect('peer_challenge_detail', challenge_id=challenge.id)


@login_required
def reject_peer_challenge(request, challenge_id):
    challenge = get_object_or_404(PeerChallenge, id=challenge_id, target=request.user, status=PeerChallenge.PENDING)
    if request.method == 'POST':
        challenge.status = PeerChallenge.REJECTED
        challenge.save(update_fields=['status', 'updated_at'])
        notify_user(challenge.creator, 'Peer challenge rejected', f'{request.user.username} rejected: {challenge.title}', '/peer-challenges/')
        messages.info(request, 'Challenge rejected.')
    return redirect('peer_challenges_list')


@login_required
def cancel_peer_challenge(request, challenge_id):
    challenge = get_object_or_404(PeerChallenge, id=challenge_id, creator=request.user)
    if request.method == 'POST' and challenge.status in [PeerChallenge.PENDING, PeerChallenge.ACCEPTED]:
        challenge.status = PeerChallenge.CANCELLED
        challenge.save(update_fields=['status', 'updated_at'])
        notify_user(challenge.target, 'Peer challenge cancelled', f'{request.user.username} cancelled: {challenge.title}', '/peer-challenges/')
        messages.info(request, 'Challenge cancelled.')
    return redirect('peer_challenges_list')


@login_required
def submit_peer_challenge_proof(request, challenge_id):
    challenge = get_object_or_404(
        PeerChallenge,
        Q(creator=request.user) | Q(target=request.user),
        id=challenge_id,
        status=PeerChallenge.ACCEPTED,
    )
    if challenge.mode == PeerChallenge.SOLO and request.user == challenge.creator:
        messages.error(request, 'This challenge is for the other user only. They need to submit the proof.')
        return redirect('peer_challenge_detail', challenge_id=challenge.id)
    if challenge.user_has_submitted(request.user):
        messages.info(request, 'You already submitted proof for this challenge.')
        return redirect('peer_challenge_detail', challenge_id=challenge.id)

    if request.method == 'POST':
        form = PeerChallengeProofForm(request.POST, request.FILES)
        if form.is_valid():
            if request.user == challenge.creator:
                challenge.creator_proof_title = form.cleaned_data['proof_title']
                challenge.creator_proof_file = form.cleaned_data['proof_file']
                challenge.creator_reflection = form.cleaned_data['reflection']
                challenge.creator_completed_at = timezone.now()
                update_fields = ['creator_proof_title', 'creator_proof_file', 'creator_reflection', 'creator_completed_at', 'updated_at']
            else:
                challenge.target_proof_title = form.cleaned_data['proof_title']
                challenge.target_proof_file = form.cleaned_data['proof_file']
                challenge.target_reflection = form.cleaned_data['reflection']
                challenge.target_completed_at = timezone.now()
                update_fields = ['target_proof_title', 'target_proof_file', 'target_reflection', 'target_completed_at', 'updated_at']
            challenge.save(update_fields=update_fields)
            other_user = challenge.other_user(request.user)
            notify_user(other_user, 'Challenge proof submitted', f'{request.user.username} submitted proof for: {challenge.title}', f'/peer-challenges/{challenge.id}/')
            add_growth_event(request.user, 'challenge', f'Submitted proof: {challenge.title}', form.cleaned_data['reflection'][:160], '📌', f'/peer-challenges/{challenge.id}/')
            completed_now = challenge.refresh_completion_status()
            if completed_now:
                notify_user(challenge.creator, 'Peer challenge completed', f'Completed: {challenge.title}', f'/peer-challenges/{challenge.id}/')
                notify_user(challenge.target, 'Peer challenge completed', f'Completed: {challenge.title}', f'/peer-challenges/{challenge.id}/')
                add_growth_event(challenge.creator, 'challenge', f'Completed peer challenge: {challenge.title}', challenge.description[:160], '🏁', f'/peer-challenges/{challenge.id}/')
                add_growth_event(challenge.target, 'challenge', f'Completed peer challenge: {challenge.title}', challenge.description[:160], '🏁', f'/peer-challenges/{challenge.id}/')
                award_badges_for_user(challenge.creator)
                award_badges_for_user(challenge.target)
                messages.success(request, 'Challenge completed! Both profiles now show this progress.')
            else:
                messages.success(request, 'Proof submitted. Waiting for the other required proof if this is a shared challenge.')
    return redirect('peer_challenge_detail', challenge_id=challenge.id)


@login_required
def report_user(request, username):
    reported_user = get_object_or_404(User, username=username, is_active=True)
    if request.method == 'POST':
        form = UserReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = request.user
            report.reported_user = reported_user
            report.save()
            messages.success(request, 'Report submitted for admin review.')
            return redirect('profile_detail', username=username)
    else:
        form = UserReportForm()
    return render(request, 'core/form_page.html', {'form': form, 'title': f'Report {reported_user.username}', 'button': 'Submit report'})


@login_required
def request_verification(request):
    existing_pending = VerificationRequest.objects.filter(user=request.user, status=VerificationRequest.PENDING).first()
    if existing_pending:
        messages.info(request, 'You already have a pending verification request.')
        return redirect('profile_detail', username=request.user.username)
    if request.method == 'POST':
        form = VerificationRequestForm(request.POST)
        if form.is_valid():
            verification = form.save(commit=False)
            verification.user = request.user
            verification.save()
            messages.success(request, 'Verification request submitted. Admin will review your proof.')
            return redirect('profile_detail', username=request.user.username)
    else:
        form = VerificationRequestForm()
    return render(request, 'core/form_page.html', {'form': form, 'title': 'Request peer verification', 'button': 'Submit verification request'})


@staff_member_required
def moderation_center(request):
    reports = UserReport.objects.filter(is_resolved=False).select_related('reporter', 'reported_user')[:20]
    verification_requests = VerificationRequest.objects.filter(status=VerificationRequest.PENDING).select_related('user')[:20]
    latest_users = User.objects.order_by('-date_joined')[:10]
    latest_sessions = ExchangeSession.objects.select_related('request', 'request__sender', 'request__receiver').order_by('-created_at')[:10]
    return render(request, 'core/moderation_center.html', {
        'reports': reports,
        'verification_requests': verification_requests,
        'latest_users': latest_users,
        'latest_sessions': latest_sessions,
    })


@staff_member_required
def resolve_report(request, report_id):
    report = get_object_or_404(UserReport, id=report_id)
    if request.method == 'POST':
        report.is_resolved = True
        report.save()
        messages.success(request, 'Report marked as resolved.')
    return redirect('moderation_center')


@staff_member_required
def approve_verification(request, verification_id):
    verification = get_object_or_404(VerificationRequest, id=verification_id)
    if request.method == 'POST':
        verification.status = VerificationRequest.APPROVED
        verification.reviewed_by = request.user
        verification.reviewed_at = timezone.now()
        verification.save()
        verification.user.profile.is_verified_peer = True
        verification.user.profile.save()
        notify_user(verification.user, 'Verification approved', 'Your profile is now marked as a verified peer.', f'/profile/{verification.user.username}/')
        add_growth_event(verification.user, 'badge', 'Became a verified peer', 'Admin reviewed the account proof and approved verification.', '✅', f'/profile/{verification.user.username}/')
        messages.success(request, 'Verification approved.')
    return redirect('moderation_center')


@staff_member_required
def reject_verification(request, verification_id):
    verification = get_object_or_404(VerificationRequest, id=verification_id)
    if request.method == 'POST':
        verification.status = VerificationRequest.REJECTED
        verification.reviewed_by = request.user
        verification.reviewed_at = timezone.now()
        verification.save()
        notify_user(verification.user, 'Verification rejected', 'Your verification request was not approved yet. Add stronger proof and try again.', f'/profile/{verification.user.username}/')
        messages.info(request, 'Verification rejected.')
    return redirect('moderation_center')


@login_required
def notifications_list(request):
    notifications = Notification.objects.filter(user=request.user)[:50]
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return render(request, 'core/notifications.html', {'notifications': notifications})


def custom_404(request, exception):
    return render(request, 'core/404.html', status=404)


def custom_500(request):
    return render(request, 'core/500.html', status=500)
