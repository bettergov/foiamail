from time import sleep
from log import log
from auth import auth
from docx import Document
from contacts import contacts 
from msg import label

from email.mime.text import MIMEText
import base64

### START CONFIG ###
foia_doc       = 'msg/payroll-foia2017.docx'
test           = True
test_recipient = 'mkiefer.bga@gmail.com'
interval       = 1 # seconds
subject        = 'Payroll FOIA | '
me             = 'me'
logtype        = 'msg'
### END CONFIG ###

service = auth.get_service(auth.get_cred())

def distribute(drafts=[]):
    if not drafts: drafts = prep_agency_drafts()
    if sanity_check(drafts):
        for draft in drafts:
            print('sending',draft) 
            send(draft)

def prep_agency_drafts(contacts_by_agency=contacts.get_contacts_by_agency()):
    foia_text = load_foia_text()
    drafts = []
    for agency in contacts_by_agency:
        slug = agency_slug(agency)
        message = foia_text + '\r\n\r\n' + slug
        slug_subject = subject + slug
        contacts = ','.join(contacts_by_agency[agency])
        draft = compose_draft(message,slug_subject,contacts)
        drafts.append(draft)
    return drafts

def sanity_check(drafts):
    """
    look before you leap
    """
    print('len(drafts)',len(drafts))
    print('drafts[0].__dict__',drafts[0].__dict__)
    print('\r\n*Inspect drafts list, then press c to continue*\r\n')
    import ipdb; ipdb.set_trace()
    verify = raw_input('Everything ready? [y/N]')
    return verify in ['Y','y']

def load_foia_text():
    return '\r\n'.join([p.text for p in Document(docx=foia_doc).paragraphs])    

def agency_slug(agency_name):
    return '#' + ''.join(agency_name.split()) + '#'

def compose_draft(message,subject,contacts):
    try:
        message = compose_message(message,subject,contacts)
        return service.users().drafts().create(userId=me, body=message).execute()    
    except Exception, e:
        print e
        import ipdb; ipdb.set_trace()

def compose_message(message,subject,contacts):
    message            = MIMEText(message)
    message['subject'] = subject
    message['from']    = me
    message['to']      = test_recipient if test else contacts
    return message
    return {'raw': base64.urlsafe_b64encode(message.as_string())}

def send(draft):
    label.label_sent(draft)
    draft.send()
    log.log('msg',draft.__dict__)
    sleep(interval)
