"""
handles uploading files to Drive
"""
from __future__ import print_function
from apiclient.http import MediaFileUpload
from auth.auth import get_service
from config import config


buffer_path = config.data["att"]["buffer_path"]
atts_drive_folder_name = config.data["att"]["drive"]["atts_drive_folder_name"]

drive_service = get_service(type='drive')


def get_or_create_atts_folder():
    """
    gets or creates the base attachment directory
    (where the agency folders will go)
    """
    atts_drive_folder_q = drive_service.files().list(
        q="name='" + atts_drive_folder_name + "'").execute().get('files')
    if atts_drive_folder_q:
        print('found', atts_drive_folder_name)
        return atts_drive_folder_q[0]
    else:
        print('creating', atts_drive_folder_name)
        return drive_service.files().create(body={
            'name': atts_drive_folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }).execute()


def check_if_drive(agency):
    """
    checks if the specified agency
    has a folder in the atts folder on Drive
    """
    q = "name='" + agency + "'"
    return drive_service.files().list(q=q).execute().get('files')


def make_drive_folder(agency, atts_drive_folder):
    """
    makes a folder on Drive
    with the specified name
    within the specified folder
    """
    return drive_service.files().create(
        body={
            'name': agency,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [atts_drive_folder['id']]}
    ).execute()


def upload_to_drive(att, drive_folder):
    """
    uploads the specified att
    to the specified Drive folder
    """
    print('    ' + att['file_name'])
    body = {'name': att['file_name'], 'parents': [drive_folder['id']]}
    media_body = MediaFileUpload(buffer_path + att['file_name'])
    drive_service.files().create(
        body=body, media_body=media_body).execute()
