import httplib2, sys, json

from apiclient.discovery import build
from oauth2client import tools
from oauth2client.file import Storage
from oauth2client.client import AccessTokenRefreshError
from oauth2client.client import OAuth2WebServerFlow

import atom.data
import gdata.data
import gdata.contacts.client
import gdata.contacts.data


### START CONFIG ###
client_id_path = 'auth/client_id_2017.json'
credential_path = 'auth/credentials.dat'
scopes = (
            'https://www.googleapis.com/auth/gmail.labels',
            'https://www.google.com/m8/feeds',
            'https://www.googleapis.com/auth/gmail.compose',
            'https://mail.google.com/',
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive',
         )
debug = True
### END CONFIG ###


# setup
storage = Storage(credential_path)
client_json = json.load(open(client_id_path))['installed']
client_id, client_secret = client_json['client_id'], client_json['client_secret']
project_id = client_json['project_id']


def get_cred():
    credentials = storage.get()
    if credentials is None or credentials.invalid or \
            sorted([x for x in credentials.scopes]) != sorted([x for x in scopes]):
        flow = OAuth2WebServerFlow(client_id, client_secret, scopes)
        credentials = tools.run_flow(flow, storage, tools.argparser.parse_args(['--noauth_local_webserver']))
    return credentials


def get_service(credentials=get_cred(),type='gmail'):
    http = credentials.authorize(httplib2.Http(disable_ssl_certificate_validation=True))
    if type == 'gmail':
        return build('gmail','v1',http=http)
    elif type == 'sheets':
        return build('sheets','v4',http=http)
    elif type == 'drive':
        return build('drive', 'v3', http=http)

def get_gd_client(credentials=get_cred()):
    gd_client = gdata.contacts.client.ContactsClient(source=project_id)
    gd_token = gdata.gauth.OAuth2TokenFromCredentials(credentials)
    gd_client.auth_token = gd_token
    gd_token.authorize(gd_client)
    return gd_client


def test_cred(credentials=get_cred()):
    # contacts
    gd_client = get_gd_client(credentials)
    if gd_client: print 'contact success'
    else: print 'contact fail'

    # gmail
    service = get_service(credentials)
    results = service.users().labels().list(userId='me').execute().get('labels',[])
    if results: print 'gmail success'
    else: print 'gmail fail'

    # drive
    drive_service = get_service(type='drive')
    results = drive_service.files().list(pageSize=10,fields="nextPageToken, files(id, name)").execute()
    if results.get('files'): print 'drive success'
    else: print 'drive fail'

    # sheets
    sheets_service = get_service(type='sheets')
    if sheets_service: print 'sheets success'
    else: print 'sheets fail'
