# SkillSwap Final Phase Update

This update adds the final product-level features:

- Less congested Explore Users filter bar
- Session chat inside accepted skill-swap sessions
- Chat inbox page
- Verification request workflow
- Admin moderation dashboard
- Report resolving
- Verification approve/reject workflow
- Challenge leaderboard
- Improved profile verification display
- Updated navigation

## Copy files

From the extracted `skillswap_final` folder, copy these into your existing `skillswap_starter` project:

```powershell
Copy-Item ..\skillswap_final\core\models.py .\core\models.py -Force
Copy-Item ..\skillswap_final\core\forms.py .\core\forms.py -Force
Copy-Item ..\skillswap_final\core\views.py .\core\views.py -Force
Copy-Item ..\skillswap_final\core\urls.py .\core\urls.py -Force
Copy-Item ..\skillswap_final\core\admin.py .\core\admin.py -Force
Copy-Item ..\skillswap_final\core\services.py .\core\services.py -Force
Copy-Item ..\skillswap_final\templates\base.html .\templates\base.html -Force
Copy-Item ..\skillswap_final\core\templates\core\explore.html .\core\templates\core\explore.html -Force
Copy-Item ..\skillswap_final\core\templates\core\session_detail.html .\core\templates\core\session_detail.html -Force
Copy-Item ..\skillswap_final\core\templates\core\profile_detail.html .\core\templates\core\profile_detail.html -Force
Copy-Item ..\skillswap_final\core\templates\core\challenges.html .\core\templates\core\challenges.html -Force
Copy-Item ..\skillswap_final\core\templates\core\chat_inbox.html .\core\templates\core\chat_inbox.html -Force
Copy-Item ..\skillswap_final\core\templates\core\moderation_center.html .\core\templates\core\moderation_center.html -Force
Copy-Item ..\skillswap_final\core\templates\core\challenge_leaderboard.html .\core\templates\core\challenge_leaderboard.html -Force
```

## Run database commands

```powershell
python manage.py makemigrations core
python manage.py migrate
python manage.py runserver
```

## Test order

1. Login as normal user.
2. Go to Explore Users and check the new filter layout.
3. Send a request to another user.
4. Login as the other user and accept the request.
5. Open Sessions and test the new chat box.
6. Add proof, mark complete, and review.
7. Go to Profile and request verification.
8. Login as admin/superuser.
9. Open `/moderation/` and approve verification.
10. Open Challenges and test challenge leaderboard.

## Important

If you see `no such table: core_chatmessage` or `no such table: core_verificationrequest`, run:

```powershell
python manage.py makemigrations core
python manage.py migrate
```
