import os
from uuid import uuid4

# Dossier simulé pour le stockage local (tu peux changer)
MOCK_STORAGE = "media/mock_drive"

os.makedirs(MOCK_STORAGE, exist_ok=True)

def drive_upload(file_obj, module_title, user):
    """
    Simulation d’un upload vers Google Drive.
    En prod : utilisera l’API Drive (pydrive2 ou google-api-python-client).
    """
    # Génère un identifiant unique et un faux lien public
    file_id = str(uuid4())
    fake_url = f"https://drive.google.com/file/d/{file_id}/view"

    # Sauvegarde locale (mock)
    if hasattr(file_obj, "read"):
        safe_name = f"{file_id}_{getattr(file_obj, 'name', 'video.mp4')}"
        path = os.path.join(MOCK_STORAGE, safe_name)
        with open(path, "wb") as f:
            f.write(file_obj.read())

    print(f"[MOCK DRIVE] Upload: {module_title} by {user} -> {fake_url}")
    return {"id": file_id, "url": fake_url}

def drive_delete(drive_url):
    """
    Simulation de suppression depuis Google Drive.
    En prod : utilisera l’API Drive pour supprimer par fileId.
    """
    print(f"[MOCK DRIVE] Delete: {drive_url}")
    return True
