import httplib2, sys, json
import atom.data
import gdata.data
import gdata.contacts.client
import gdata.contacts.data
from apiclient.discovery import build
from oauth2client import tools
from oauth2client.file import Storage
from oauth2client.client import AccessTokenRefreshError
from oauth2client.client import OAuth2WebServerFlow


client_json = json.load(open('client_id.json'))['installed']
client_id = client_json['client_id']
client_secret = client_json['client_secret']
scope = 'https://www.google.com/m8/feeds/'
flow = OAuth2WebServerFlow(client_id, client_secret, scope)

def main():
  storage = Storage('credentials-contacts.dat')
  credentials = storage.get()

  if credentials is None or credentials.invalid:
    credentials = tools.run_flow(flow, storage, tools.argparser.parse_args())

  http = httplib2.Http()
  http = credentials.authorize(http)
  service = build('gmail', 'v1', http=http)

  try:
    results = service.users().labels().list(userId='me').execute()
    for label in results.get('labels', []):
      print label['name']

  except AccessTokenRefreshError:
    print ('The credentials have been revoked or expired, please re-run'
           'the application to re-authorize')

if __name__ == '__main__':
  main()
