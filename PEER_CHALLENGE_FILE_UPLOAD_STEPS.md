# Peer Challenge File Upload Update

This update replaces the peer challenge proof link with a required proof file upload.

Users can upload images, PDFs, documents, coding files such as `.py`, `.html`, `.css`, `.js`, notebooks, ZIP files, and similar proof files.

Uploaded files are stored locally in:

```text
media/peer_challenge_proofs/
```

## Copy files

Run these from your main project folder:

```powershell
Copy-Item ..\skillswap_peer_file_update\core\models.py .\core\models.py -Force
Copy-Item ..\skillswap_peer_file_update\core\forms.py .\core\forms.py -Force
Copy-Item ..\skillswap_peer_file_update\core\views.py .\core\views.py -Force
Copy-Item ..\skillswap_peer_file_update\core\templates\core\peer_challenge_detail.html .\core\templates\core\peer_challenge_detail.html -Force
Copy-Item ..\skillswap_peer_file_update\config\settings.py .\config\settings.py -Force
Copy-Item ..\skillswap_peer_file_update\config\urls.py .\config\urls.py -Force
```

## Migrate database

```powershell
python manage.py makemigrations core
python manage.py migrate
python manage.py runserver
```
