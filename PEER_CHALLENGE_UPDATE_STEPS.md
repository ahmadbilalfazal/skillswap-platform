# SkillSwap Peer Challenge Update

This update adds direct peer challenges.

## What is added

- Challenge a user from their profile
- Choose challenge mode: challenge them only, or challenge both of you
- My Peer Challenges page
- Accept, reject, cancel challenge flow
- Submit proof link, proof title, and reflection
- Auto-complete challenge when required proof is submitted
- Notifications and growth timeline events
- Peer Challenger badge
- Challenge leaderboard now counts peer challenges too

## Install steps

1. Stop your Django server with CTRL + C.
2. Back up your project.
3. Copy the updated files from this folder into your existing project.
4. Run migrations:

```powershell
python manage.py makemigrations core
python manage.py migrate
```

5. Start the server again:

```powershell
python manage.py runserver
```

## Test flow

1. Login as User 1.
2. Go to Explore Users.
3. Open User 2 profile.
4. Click Challenge user.
5. Choose Challenge them only or Challenge both of us.
6. Send the challenge.
7. Login as User 2.
8. Open Peer Challenges.
9. Accept the challenge.
10. Submit proof.
11. If it is a shared challenge, User 1 also submits proof.
12. Check profile growth timeline and leaderboard.
