"""
authentication tools for:
- contacts
- gmail
- sheets
- drive
that allow all other modules to work
via wrapper functions
"""
import os
from pathlib import Path
from decouple import config
import httplib2
import sys
import json
from googleapiclient.discovery import build
from oauth2client import tools
from oauth2client.file import Storage
from oauth2client.client import AccessTokenRefreshError
from oauth2client.client import OAuth2WebServerFlow
import atom.data
import gdata.data
import gdata.contacts.client
import gdata.contacts.data

### START CONFIG ###
BASE_DIR = Path(__file__).parent.parent.absolute()
client_id_path = os.path.join(BASE_DIR, config(
    'AUTH_CLIENT_SECRET_PATH'))
credential_path = os.path.join(BASE_DIR, config(
    'AUTH_CREDENTIALS_PATH'))
# some of these may be redundant
scopes = (
    'https://www.googleapis.com/auth/gmail.labels',
    'https://www.google.com/m8/feeds',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://mail.google.com/',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
)
debug = config('DEBUG', default=False, cast=bool)
### END CONFIG ###

# setup
storage = Storage(credential_path)
client_json = json.load(open(client_id_path))['installed']
client_id, client_secret = client_json['client_id'], client_json['client_secret']
project_id = client_json['project_id']


def get_cred():
    """
    triggers authorization workflow
    to get credentials for scopes as configured
    if they aren't already stored locally.
    follow cli instructions for first-time setup
    """
    credentials = storage.get()
    if credentials is None or credentials.invalid or \
            sorted([x for x in credentials.scopes]) != sorted([x for x in scopes]):
        flow = OAuth2WebServerFlow(client_id, client_secret, scopes)
        credentials = tools.run_flow(
            flow, storage, tools.argparser.parse_args(['--noauth_local_webserver']))
    return credentials


def get_service(credentials=get_cred(), type='gmail'):
    """
    uses credentials to get an http service object for
    - gmail
    - sheets
    - drive
    """
    http = credentials.authorize(httplib2.Http(
        disable_ssl_certificate_validation=True))
    if type == 'gmail':
        return build('gmail', 'v1', http=http)
    elif type == 'sheets':
        return build('sheets', 'v4', http=http)
    elif type == 'drive':
        return build('drive', 'v3', http=http)


def get_gd_client(credentials=get_cred()):
    """
    uses credentials to get a gd_client service object for
    - contacts
    """
    gd_client = gdata.contacts.client.ContactsClient(source=project_id)
    gd_token = gdata.gauth.OAuth2TokenFromCredentials(credentials)
    gd_client.auth_token = gd_token
    gd_token.authorize(gd_client)
    return gd_client


def test_cred(credentials=get_cred()):
    """
    a test function to verify auth/functionality of:
    - contacts
    - gmail
    - drive
    - sheets
    some of these tests may ned to be reviewed
    """
    # contacts
    gd_client = get_gd_client(credentials)
    if gd_client:
        print('contact success')
    else:
        print('contact fail')

    # gmail
    service = get_service(credentials)
    results = service.users().labels().list(userId='me').execute().get('labels', [])
    if results:
        print('gmail success')
    else:
        print('gmail fail')

    # drive
    drive_service = get_service(type='drive')
    results = drive_service.files().list(
        pageSize=10, fields="nextPageToken, files(id, name)").execute()
    if results.get('files'):
        print('drive success')
    else:
        print('drive fail')

    # sheets
    sheets_service = get_service(type='sheets')
    if sheets_service:
        print('sheets success')
    else:
        print('sheets fail')
