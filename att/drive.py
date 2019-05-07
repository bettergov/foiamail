"""
handles uploading files to Drive
"""
from googleapiclient.http import MediaFileUpload
from auth.auth import get_service
import logging

### START CONFIG ###
atts_drive_folder_name = 'agency_attachments'
buffer_path = '/tmp/'  # TODO put in a project config file, import in gm
### END CONFIG ###

drive_service = get_service(type='drive')


def get_or_create_atts_folder():
    """
    gets or creates the base attachment directory
    (where the agency folders will go)
    """
    atts_drive_folder_q = drive_service.files().list(
        q="name='" + atts_drive_folder_name + "'").execute().get('files')
    if atts_drive_folder_q:
        logging.info(f'found {atts_drive_folder_name}')
        return atts_drive_folder_q[0]
    else:
        logging.info(f'creating {atts_drive_folder_name}')
        return drive_service.files().create(body={'name': atts_drive_folder_name,
                                                  'mimeType': 'application/vnd.google-apps.folder'}).execute()


def check_if_drive(agency):
    """
    checks if the specified agency
    has a folder in the atts folder on Drive
    """

    return drive_service.files().list(q=f"name='{agency}'").execute().get('files')


def get_or_create_drive_folder(agency, atts_drive_folder):
    """
    Gets or creates a folder on Drive with the specified name within the
    specified folder
    """

    # check if folder exists
    results = drive_service.files().list(
        corpora='user',
        q=f'name="{agency}" and mimeType contains "google-apps.folder"'
    ).execute()

    # if folder exists, return it
    if results['files']:
        return drive_service.files().get(
            fileId=results['files'][0]['id']
        ).execute()

    # otherwise create folder
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

    file_name = att['file_name']
    parent_id = drive_folder['id']

    # check if the file already exists
    results = drive_service.files().list(
        q=f'name="{file_name}" and "{parent_id}" in parents').execute()

    if results['files']:
        logging.info(f'{file_name} already uploaded')

    # if not, upload the file
    else:
        logging.info(f'uploading {file_name}')
        body = {'name': file_name, 'parents': [parent_id]}
        media_body = MediaFileUpload(buffer_path + file_name)
        drive_service.files().create(
            body=body, media_body=media_body).execute()
