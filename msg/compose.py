from time import sleep
from log import log
from auth import auth
from docx import Document
from contacts.contacts import get_contacts_by_agency 
from msg.utils import agency_slug
from email.mime.text import MIMEText
import base64

### START CONFIG ###
foia_doc       = 'msg/payroll-foia2017.docx'
test           = False
test_recipient = 'mkiefer.bga@gmail.com'
interval       = 1 # seconds
subject        = 'Payroll FOIA | '
me             = 'me'
logtype        = 'msg'
### END CONFIG ###
service = auth.get_service()
drafts = service.users().drafts().list(userId='me',maxResults=2000).execute()
if 'drafts' in drafts.keys(): drafts = drafts['drafts']

def distribute(drafts=drafts,send=False):
    if not drafts: 
        pd = raw_input('No drafts found ... prep drafts now?[y/N]')
        if pd.lower() == 'y':
            drafts = prep_agency_drafts()
    if send and sanity_check(drafts):
        for draft in drafts:
            print('sending',draft) 
            sender(draft)

def prep_agency_drafts(contacts_by_agency=[]):
    """
    {agency:emailaddy}
    """
    if test: 
        contacts_by_agency = {'BGAtest':test_recipient}
    elif not contacts_by_agency: 
        contacts_by_agency = get_contacts_by_agency()
    foia_text = load_foia_text()
    drafts = []
    for agency in contacts_by_agency:
        slug = agency_slug(agency)
        body = foia_text + '\r\n\r\n' + slug
        slug_subject = subject + agency
        contacts = ','.join(contacts_by_agency[agency])
        draft = compose_draft(body,slug_subject,contacts)
        drafts.append(draft)
    print drafts
    return drafts

def sanity_check(drafts):
    """
    look before you leap
    """
    print drafts
    print('len(drafts)',len(drafts))
    verify = raw_input('Everything ready? [y/N]')
    return verify in ['Y','y']

def load_foia_text():
    return '\r\n'.join([p.text for p in Document(docx=foia_doc).paragraphs])    

def compose_draft(body,subject,contacts):
    try:
        message = compose_message(body,subject,contacts)
        #return service.users().drafts().create(userId=me, body=message).execute()    
        return service.users().drafts().create(userId=me,body={'message':message}).execute()
    except Exception, e:
        print e
        import ipdb; ipdb.set_trace()

def compose_message(body,subject,contacts):
    message            = MIMEText(body)
    message['subject'] = subject
    message['from']    = me
    message['to']      = test_recipient if test else contacts
    #return message
    return {'raw': base64.urlsafe_b64encode(message.as_string())}

def sender(draft):
    sent = service.users().drafts().send(userId='me',body={'id':draft['id']}).execute()
    print('sent',sent)
    sleep(interval)

def delete_drafts(draft_ids=[]):
    if not draft_ids:
        # check for existence of drafts
        draft_ids = [x['id'] for x in drafts if type(drafts) == 'list'] #hack
    print('len(draft_ids)',len(draft_ids))
    dd = raw_input('delete  drafts?[y/N]')
    if dd.lower() == 'y':
        print drafts 
        for draft_id in draft_ids:
            print 'deleting', draft_id
            service.users().drafts().delete(userId='me',id=draft_id).execute()
