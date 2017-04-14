import httplib2
import sys
import json
    
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

storage = Storage('contacts-credentials.dat')
credentials = storage.get()

if credentials is None or credentials.invalid:
    credentials = tools.run_flow(flow, storage, tools.argparser.parse_args())

http = httplib2.Http()
http = credentials.authorize(http)




def create_contact():
    import atom.data
    import gdata.data
    import gdata.contacts.client
    import gdata.contacts.data

    gd_client = gdata.contacts.client.ContactsClient(source='payroll17-164122')
    gd_token = gdata.gauth.OAuth2TokenFromCredentials(credentials)
    gd_client.auth_token = gd_token

    new_contact = gdata.contacts.data.ContactEntry()
    new_contact.name = gdata.data.Name(full_name=gdata.data.FullName(text='FOO Officer'))
    new_contact.email.append(gdata.data.Email(address='foo2',primary='true'))
    e = new_contact.email[0]
    e.label = 'foo'

    contact_entry = gd_client.CreateContact(new_contact)


if __name__ == "__main__":
    create_contact()
