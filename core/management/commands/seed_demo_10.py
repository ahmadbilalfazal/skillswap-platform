from datetime import timedelta
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import (
    Badge, ChallengeSubmission, ExchangeSession, Favorite, GrowthEvent,
    Notification, PeerChallenge, Profile, ProofArtifact, Review, Skill,
    SkillSwapRequest, UserBadge, UserReport, UserSkill, WeeklyChallenge
)


DEMO_PASSWORD = "SkillSwap@123"


class Command(BaseCommand):
    help = "Create 10 professional demo users and demo activity for SkillSwap."

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Creating 10-user SkillSwap demo data..."))

        users_data = [
            ("ahmad", "Ahmad", "Bilal", "ahmad@example.com", "AI student learning Django, databases, and real web product development.", "evenings", "Lahore"),
            ("sara", "Sara", "Khan", "sara@example.com", "Graphic designer teaching Canva, branding, and social media design.", "weekends", "Islamabad"),
            ("hamza", "Hamza", "Ali", "hamza@example.com", "Video editor focused on reels, YouTube shorts, and content storytelling.", "flexible", "Karachi"),
            ("ayesha", "Ayesha", "Noor", "ayesha@example.com", "Excel tutor and public speaking learner interested in confidence building.", "weekdays", "Multan"),
            ("zain", "Zain", "Malik", "zain@example.com", "Beginner web developer building portfolio projects and learning UI design.", "evenings", "Rawalpindi"),
            ("fatima", "Fatima", "Raza", "fatima@example.com", "UI/UX learner who enjoys wireframes, landing pages, and design feedback.", "weekends", "Faisalabad"),
            ("usman", "Usman", "Tariq", "usman@example.com", "Data analysis learner with interest in Excel dashboards and Python automation.", "flexible", "Peshawar"),
            ("maria", "Maria", "Sheikh", "maria@example.com", "English communication mentor helping learners improve speaking confidence.", "evenings", "Quetta"),
            ("hassan", "Hassan", "Javed", "hassan@example.com", "Frontend learner practicing HTML, CSS, JavaScript, and portfolio building.", "weekdays", "Sialkot"),
            ("nimra", "Nimra", "Awan", "nimra@example.com", "Digital marketing learner interested in copywriting, content planning, and branding.", "weekends", "Gujranwala"),
        ]

        users = {}
        for username, first_name, last_name, email, bio, availability, location in users_data:
            user, _ = User.objects.get_or_create(username=username)
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.set_password(DEMO_PASSWORD)
            user.save()

            profile, _ = Profile.objects.get_or_create(user=user)
            profile.bio = bio
            profile.availability = availability
            profile.location = location
            if username in ["sara", "maria", "ahmad"]:
                profile.is_verified_peer = True
            profile.save()

            users[username] = user

        skills_data = [
            ("Python", "programming"),
            ("Django", "programming"),
            ("Web Development", "programming"),
            ("HTML/CSS", "programming"),
            ("JavaScript", "programming"),
            ("Graphic Design", "design"),
            ("Canva", "design"),
            ("UI/UX Design", "design"),
            ("Video Editing", "video"),
            ("Content Creation", "video"),
            ("Public Speaking", "communication"),
            ("Communication Skills", "communication"),
            ("English Speaking", "language"),
            ("Excel", "business"),
            ("Data Analysis", "business"),
            ("Digital Marketing", "business"),
            ("Copywriting", "business"),
        ]

        skills = {}
        for name, category in skills_data:
            skill, _ = Skill.objects.get_or_create(name=name)
            skill.category = category
            skill.save()
            skills[name] = skill

        def add_skill(username, skill_name, skill_type, level):
            UserSkill.objects.get_or_create(
                user=users[username],
                skill=skills[skill_name],
                type=skill_type,
                defaults={"level": level},
            )

        skill_plan = {
            "ahmad": {
                "have": [("Python", "intermediate"), ("Django", "beginner")],
                "want": [("Graphic Design", "beginner"), ("Video Editing", "beginner")]
            },
            "sara": {
                "have": [("Graphic Design", "advanced"), ("Canva", "advanced")],
                "want": [("Python", "beginner"), ("Web Development", "beginner")]
            },
            "hamza": {
                "have": [("Video Editing", "advanced"), ("Content Creation", "intermediate")],
                "want": [("Communication Skills", "beginner"), ("UI/UX Design", "beginner")]
            },
            "ayesha": {
                "have": [("Excel", "intermediate"), ("Public Speaking", "intermediate")],
                "want": [("Data Analysis", "beginner"), ("Video Editing", "beginner")]
            },
            "zain": {
                "have": [("HTML/CSS", "beginner"), ("Web Development", "beginner")],
                "want": [("UI/UX Design", "beginner"), ("English Speaking", "beginner")]
            },
            "fatima": {
                "have": [("UI/UX Design", "intermediate"), ("Canva", "intermediate")],
                "want": [("JavaScript", "beginner"), ("Django", "beginner")]
            },
            "usman": {
                "have": [("Excel", "advanced"), ("Data Analysis", "intermediate")],
                "want": [("Python", "beginner"), ("Digital Marketing", "beginner")]
            },
            "maria": {
                "have": [("English Speaking", "advanced"), ("Communication Skills", "advanced")],
                "want": [("Content Creation", "beginner"), ("Canva", "beginner")]
            },
            "hassan": {
                "have": [("JavaScript", "intermediate"), ("HTML/CSS", "advanced")],
                "want": [("Django", "beginner"), ("Public Speaking", "beginner")]
            },
            "nimra": {
                "have": [("Digital Marketing", "intermediate"), ("Copywriting", "intermediate")],
                "want": [("Video Editing", "beginner"), ("Graphic Design", "beginner")]
            },
        }

        for username, plan in skill_plan.items():
            for skill_name, level in plan["have"]:
                add_skill(username, skill_name, UserSkill.HAVE, level)
            for skill_name, level in plan["want"]:
                add_skill(username, skill_name, UserSkill.WANT, level)

        badges_data = [
            ("First Swap", "Completed the first skill exchange session.", "??"),
            ("Trusted Peer", "Received excellent reviews from exchange partners.", "?"),
            ("Proof Builder", "Submitted meaningful learning proof.", "??"),
            ("Peer Challenger", "Created or completed peer-to-peer challenges.", "??"),
            ("Community Starter", "Actively contributed to the SkillSwap community.", "??"),
            ("Verified Mentor", "Recognized as a reliable peer mentor.", "?"),
        ]

        badges = {}
        for name, description, icon in badges_data:
            badge, _ = Badge.objects.get_or_create(name=name)
            badge.description = description
            badge.icon = icon
            badge.save()
            badges[name] = badge

        badge_plan = {
            "ahmad": ["First Swap", "Peer Challenger"],
            "sara": ["Trusted Peer", "Verified Mentor", "Proof Builder"],
            "hamza": ["Community Starter"],
            "ayesha": ["Trusted Peer"],
            "zain": ["Proof Builder"],
            "fatima": ["Community Starter", "First Swap"],
            "usman": ["Proof Builder"],
            "maria": ["Verified Mentor", "Trusted Peer"],
            "hassan": ["First Swap"],
            "nimra": ["Peer Challenger"],
        }

        for username, badge_names in badge_plan.items():
            for badge_name in badge_names:
                UserBadge.objects.get_or_create(user=users[username], badge=badges[badge_name])

        def make_request(sender, receiver, teach, learn, message, completed=False, days_ago=3):
            request = SkillSwapRequest.objects.filter(
                sender=users[sender],
                receiver=users[receiver],
                teach_skill=skills[teach],
                learn_skill=skills[learn],
            ).first()

            if not request:
                request = SkillSwapRequest.objects.create(
                    sender=users[sender],
                    receiver=users[receiver],
                    teach_skill=skills[teach],
                    learn_skill=skills[learn],
                    message=message,
                    status=SkillSwapRequest.ACCEPTED,
                )
            else:
                request.status = SkillSwapRequest.ACCEPTED
                request.message = message
                request.save()

            session, _ = ExchangeSession.objects.update_or_create(
                request=request,
                defaults={
                    "scheduled_at": timezone.now() - timedelta(days=days_ago),
                    "duration_minutes": 60,
                    "session_notes": f"Skill exchange between {sender} and {receiver} covering {teach} and {learn}.",
                    "mini_assignment": "Create a small practical task and share it before the next meeting.",
                    "learner_reflection": "Both users reflected on what they learned and how they can improve.",
                    "is_completed": completed,
                    "completed_at": timezone.now() - timedelta(days=days_ago - 1) if completed else None,
                },
            )
            return session

        completed_sessions = [
            make_request("ahmad", "sara", "Python", "Graphic Design", "Python basics in exchange for design feedback.", True, 8),
            make_request("hamza", "maria", "Video Editing", "Communication Skills", "Video editing help in exchange for speaking practice.", True, 6),
            make_request("zain", "fatima", "HTML/CSS", "UI/UX Design", "Frontend layout help in exchange for UI feedback.", True, 5),
            make_request("usman", "hassan", "Excel", "JavaScript", "Excel dashboard help in exchange for JS basics.", True, 4),
            make_request("nimra", "ayesha", "Digital Marketing", "Public Speaking", "Marketing content help in exchange for presentation practice.", True, 3),
        ]

        pending_session = make_request("fatima", "ahmad", "UI/UX Design", "Django", "UI structure support in exchange for Django guidance.", False, 1)

        review_pairs = [
            (completed_sessions[0], "ahmad", "sara", 5, "Excellent design explanation with practical visual examples."),
            (completed_sessions[0], "sara", "ahmad", 5, "Very clear Python teaching. Easy to follow for beginners."),
            (completed_sessions[1], "hamza", "maria", 5, "Great communication coaching and confidence-building tips."),
            (completed_sessions[1], "maria", "hamza", 4, "Helpful video editing guidance with clear workflow steps."),
            (completed_sessions[2], "zain", "fatima", 5, "Strong UI feedback. My layout improved a lot."),
            (completed_sessions[2], "fatima", "zain", 4, "Good HTML/CSS support and patient explanation."),
            (completed_sessions[3], "usman", "hassan", 5, "JavaScript explanation was practical and beginner-friendly."),
            (completed_sessions[3], "hassan", "usman", 5, "Excellent Excel dashboard guidance."),
            (completed_sessions[4], "nimra", "ayesha", 4, "Useful public speaking practice and feedback."),
            (completed_sessions[4], "ayesha", "nimra", 5, "Creative digital marketing ideas and clear content tips."),
        ]

        for session, reviewer, reviewed, rating, comment in review_pairs:
            Review.objects.update_or_create(
                session=session,
                reviewer=users[reviewer],
                reviewed_user=users[reviewed],
                defaults={"rating": rating, "comment": comment},
            )

        for idx, session in enumerate(completed_sessions, start=1):
            ProofArtifact.objects.get_or_create(
                session=session,
                title=f"Demo Session Proof {idx}",
                added_by=session.request.sender,
                defaults={
                    "description": "Demo proof artifact showing completed learning activity.",
                    "link": "https://example.com/demo-proof",
                },
            )

        favorite_pairs = [
            ("ahmad", "sara"), ("sara", "ahmad"), ("zain", "fatima"), ("fatima", "zain"),
            ("hamza", "maria"), ("maria", "hamza"), ("usman", "hassan"), ("nimra", "ayesha"),
        ]

        for owner, saved in favorite_pairs:
            Favorite.objects.get_or_create(owner=users[owner], saved_user=users[saved])

        weekly_1, _ = WeeklyChallenge.objects.get_or_create(
            title="Build a One-Page Portfolio",
            defaults={
                "description": "Create a simple portfolio page introducing your skills, projects, and learning goals.",
                "starts_at": timezone.now() - timedelta(days=5),
                "ends_at": timezone.now() + timedelta(days=5),
                "is_active": True,
            },
        )

        weekly_2, _ = WeeklyChallenge.objects.get_or_create(
            title="Create a 30-Second Skill Intro Video",
            defaults={
                "description": "Create a short video introducing one skill you can teach on SkillSwap.",
                "starts_at": timezone.now() - timedelta(days=3),
                "ends_at": timezone.now() + timedelta(days=7),
                "is_active": True,
            },
        )

        submissions = [
            (weekly_1, "zain", "Zain Portfolio Draft", "I learned how to structure a portfolio page.", 86),
            (weekly_1, "sara", "Creative Designer Portfolio", "I focused on spacing, hierarchy, and visual style.", 94),
            (weekly_1, "fatima", "UX Portfolio Concept", "I practiced layout planning and section flow.", 90),
            (weekly_2, "hamza", "Video Editing Intro Reel", "I explained my editing process in a short reel.", 91),
            (weekly_2, "maria", "Speaking Confidence Intro", "I practiced presenting one skill confidently.", 88),
        ]

        for challenge, username, title, reflection, score in submissions:
            ChallengeSubmission.objects.update_or_create(
                challenge=challenge,
                user=users[username],
                defaults={
                    "title": title,
                    "link": "https://example.com/demo-submission",
                    "reflection": reflection,
                    "score": score,
                },
            )

        peer_challenges = [
            ("ahmad", "hamza", "Create a 20-second app promo reel", "Create a short reel concept for promoting SkillSwap.", "Video Editing", PeerChallenge.SHARED, PeerChallenge.ACCEPTED, 7),
            ("ayesha", "zain", "Explain one Excel formula with a real example", "Prepare a small explanation of one useful Excel formula.", "Excel", PeerChallenge.SOLO, PeerChallenge.COMPLETED, -1),
            ("nimra", "sara", "Design a social media post concept", "Create a post concept for a learning community.", "Graphic Design", PeerChallenge.SHARED, PeerChallenge.ACCEPTED, 5),
            ("maria", "hassan", "Record a 1-minute speaking practice", "Practice confident speaking about a technical topic.", "Public Speaking", PeerChallenge.SOLO, PeerChallenge.PENDING, 4),
        ]

        for creator, target, title, description, focus, mode, status, due_days in peer_challenges:
            challenge = PeerChallenge.objects.filter(
                creator=users[creator],
                target=users[target],
                title=title,
            ).first()

            if not challenge:
                challenge = PeerChallenge.objects.create(
                    creator=users[creator],
                    target=users[target],
                    title=title,
                    description=description,
                    skill_focus=focus,
                    mode=mode,
                    due_at=timezone.now() + timedelta(days=due_days),
                    status=status,
                )
            else:
                challenge.description = description
                challenge.skill_focus = focus
                challenge.mode = mode
                challenge.due_at = timezone.now() + timedelta(days=due_days)
                challenge.status = status
                challenge.save()

            if status == PeerChallenge.COMPLETED:
                challenge.target_proof_title = "Completed peer challenge proof"
                challenge.target_reflection = "I completed the task and learned from the feedback."
                challenge.target_completed_at = timezone.now() - timedelta(hours=12)
                challenge.completed_at = timezone.now() - timedelta(hours=12)
                challenge.save()

        growth_events = [
            ("ahmad", "join", "Joined SkillSwap", "Started a verified peer-learning journey.", "?"),
            ("ahmad", "session", "Completed Python/design exchange", "Completed a practical exchange session with Sara.", "?"),
            ("sara", "review", "Received 5-star review", "Recognized for clear graphic design guidance.", "?"),
            ("hamza", "skill", "Added Video Editing skill", "Available to teach reels and short-form editing.", "??"),
            ("maria", "badge", "Earned Verified Mentor badge", "Recognized as a strong communication mentor.", "?"),
            ("zain", "challenge", "Submitted portfolio challenge", "Submitted a portfolio page for weekly challenge.", "??"),
            ("fatima", "session", "Completed UI/UX exchange", "Helped improve frontend design decisions.", "??"),
            ("usman", "proof", "Added Excel dashboard proof", "Uploaded evidence from a completed learning session.", "??"),
            ("ayesha", "challenge", "Created Excel peer challenge", "Helped another user practice with a real example.", "??"),
            ("nimra", "request", "Started marketing/design exchange", "Sent a collaborative skill challenge to Sara.", "??"),
        ]

        for username, event_type, title, description, icon in growth_events:
            GrowthEvent.objects.get_or_create(
                user=users[username],
                title=title,
                defaults={
                    "event_type": event_type,
                    "description": description,
                    "icon": icon,
                },
            )

        notifications = [
            ("sara", "You received a 5-star review", "Ahmad reviewed your graphic design guidance.", "/profile/sara/"),
            ("hamza", "New peer challenge received", "Ahmad challenged you to create a short promo reel.", "/peer-challenges/"),
            ("zain", "Challenge completed", "Your Excel explanation challenge was marked completed.", "/peer-challenges/"),
            ("fatima", "New skill swap request accepted", "Your UI/UX exchange session is ready.", "/dashboard/"),
            ("maria", "Verified mentor badge awarded", "Your profile now shows verified mentor status.", "/profile/maria/"),
        ]

        for username, title, message, url in notifications:
            Notification.objects.get_or_create(
                user=users[username],
                title=title,
                defaults={"message": message, "url": url},
            )

        UserReport.objects.get_or_create(
            reporter=users["ahmad"],
            reported_user=users["hassan"],
            reason="other",
            defaults={
                "details": "Demo moderation report for testing the admin moderation center.",
                "is_resolved": False,
            },
        )

        self.stdout.write(self.style.SUCCESS("10-user demo data created successfully."))
        self.stdout.write(self.style.SUCCESS(f"Demo password for all demo users: {DEMO_PASSWORD}"))
