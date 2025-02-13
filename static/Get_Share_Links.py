from googleapiclient.discovery import build
from google.oauth2 import service_account
import csv

# Load Google Drive API credentials
SERVICE_ACCOUNT_FILE = r"C:\VSC_Projects\LOCAL_OPSLENS_FILES\drive-api-access-450811-a7a5f8e102a2.json"  # Replace with your actual path
SCOPES = ["https://www.googleapis.com/auth/drive"]

# Authenticate and build the service
token_credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
drive_service = build("drive", "v3", credentials=token_credentials)

# Define the parent folder ID (STORE_SQLBACKUP folder)
PARENT_FOLDER_ID = "1d204HtICfjyknHON-kxd1O4p7pT2t7QT"  # The folder ID after "folders/" in the URL

# Function to list subfolders inside a folder
def list_subfolders(folder_id):
    query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    return {folder["name"]: folder["id"] for folder in results.get("files", [])}

# Function to list files inside a given folder
def list_files(folder_id):
    query = f"'{folder_id}' in parents and trashed=false"
    results = drive_service.files().list(q=query, fields="files(id, name, mimeType)").execute()
    files = results.get("files", [])
    
    file_links = []
    for file in files:
        if file["mimeType"] != "application/vnd.google-apps.folder":  # Skip folders
            file_id = file["id"]
            file_name = file["name"]

            # Make the file shareable
            permission = {"type": "anyone", "role": "reader"}
            drive_service.permissions().create(fileId=file_id, body=permission).execute()

            # Generate the public link
            file_link = f"https://drive.google.com/file/d/{file_id}/view"
            file_links.append((file_name, file_link))

    return file_links

# Step 1: Get all store folders inside STORE_SQLBACKUP
store_folders = list_subfolders(PARENT_FOLDER_ID)

# Step 2: Find OUTPUT folders inside each store
output_folders = {}
for store_name, store_id in store_folders.items():
    subfolders = list_subfolders(store_id)
    if "OUTPUT" in subfolders:
        output_folders[store_name] = subfolders["OUTPUT"]

# Step 3: Generate links for files inside each OUTPUT folder
all_file_links = []
for store_name, output_id in output_folders.items():
    files = list_files(output_id)
    for file_name, file_link in files:
        all_file_links.append((store_name, file_name, file_link))

# Step 4: Save to CSV
output_file = "google_drive_links.csv"
with open(output_file, "w", newline="") as csvfile:
    csv_writer = csv.writer(csvfile)
    csv_writer.writerow(["Store Name", "File Name", "Google Drive Link"])
    csv_writer.writerows(all_file_links)

print(f"Google Drive links saved to {output_file}")
