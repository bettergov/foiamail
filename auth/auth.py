"""
authentication tools for:
- gmail
- sheets
- drive
- people
that allow all other modules to work
via wrapper functions
"""
from __future__ import print_function
import sys
import httplib2
import json
from apiclient.discovery import build
from oauth2client import tools
from oauth2client.file import Storage
from oauth2client.client import AccessTokenRefreshError
from oauth2client.client import OAuth2WebServerFlow

from config import config


client_id_path = config.data["auth"]["client_id_path"]
credential_path = config.data["auth"]["credential_path"]
scopes = config.data["auth"]["scopes"]
debug = config.data["auth"]["debug"]

# setup
storage = Storage(credential_path)
try:
    client_json = json.load(open(client_id_path))['installed']
except FileNotFoundError:
    print("Error: %s not found. Make sure you've ran set up Google credentials correctly. Try running: ./mgr.py --get-cred" % (client_id_path))
    sys.exit(1)
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
    - people
    """
    http = credentials.authorize(httplib2.Http(
        disable_ssl_certificate_validation=True))
    if type == 'gmail':
        return build('gmail', 'v1', http=http)
    elif type == 'sheets':
        return build('sheets', 'v4', http=http)
    elif type == 'drive':
        return build('drive', 'v3', http=http)
    elif type == 'people':
        return build('people', 'v1', http=http)


def test_cred(credentials=get_cred()):
    """
    a test function to verify auth/functionality of:
    - gmail
    - drive
    - sheets
    - people
    some of these tests may ned to be reviewed
    """

    # gmail
    service = get_service(credentials)
    results = service.users().labels().list(userId='me').execute().get('labels', [])
    if results:
        print('gmail success')
    else:
        print('gmail fail')

    # drive
    drive_service = get_service(type='drive')
    results = drive_service.files().list(pageSize=10,fields="nextPageToken, files(id, name)").execute()
    if 'files' in results: print('drive success')
    else: print('drive fail')

    # sheets
    sheets_service = get_service(type='sheets')
    if sheets_service:
        print('sheets success')
    else:
        print('sheets fail')

    # people
    people_service = get_service(type="people")
    if people_service:
        print("people success")
    else:
        print("people fail")