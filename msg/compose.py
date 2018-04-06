from time import sleep
from log import log
from auth import auth
try: 
    from docx import Document 
except:
    pass
from contacts.contacts import get_contacts_by_agency 
from msg.utils import agency_slug
from msg.label import label_agency
from email.mime.text import MIMEText
import base64

### START CONFIG ###
foia_doc       = 'msg/payroll-foia2017.docx'
interval       = 1 # seconds
subject        = 'Payroll FOIA | '
me             = 'me'
logtype        = 'msg'
### END CONFIG ###
service = auth.get_service()

def distribute(send=False):
    """
    draft = [{'agency': agency_name,'draft': draft}]
    """
    #TODO: recovery function to get unsent drafts *by agency*
    drafts = prep_agency_drafts()
    if send and sanity_check(drafts):
    	ready = raw_input('drafts created. inspect and type "send" to distribute')
        if ready.lower() == 'send':
            for draft in drafts:
                print('sending',draft) 
                sender(draft)
            print('distribution complete.')
        else:
            print('aborting')

def prep_agency_drafts(contacts_by_agency=unsent_agency_contacts()):
    """
    contacts_by_agency = {agency:[email_addresses]}
    """
    # first delete existing drafts
    delete_drafts()
    # then create new drafts
    print('agencies to be prepped:', contacts_by_agency.keys())
    pd = raw_input('prep drafts now? [y/N]')
    if pd.lower() == 'y':
        foia_text = load_foia_text()
        drafts = []
        for agency in contacts_by_agency:
            slug = agency_slug(agency)
            body = foia_text + '\r\n\r\n' + slug
            slug_subject = subject + agency
            contacts = ','.join(contacts_by_agency[agency])
            draft = {'agency':agency,'draft':compose_draft(body,slug_subject,contacts)}
            #TODO label the draft here not when you send so you can verify thanks
            drafts.append(draft)
            print(draft)
        #TODO verify all agencies have a draft ... some get skipped i.e. service errors
        return drafts
    else:
        print('skipping')

def unsent_agency_contacts():
    from report.response import get_threads
    contacts_by_agency = get_contacts_by_agency
    return dict((agency, contacts_by_agency[agency]) for agency\
        in contacts_by_agency if not get_threads(agency))
      

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
        draft_id = service.users().drafts().create(userId='me',body={'message':message}).execute()['id']
        draft = service.users().drafts().get(userId='me',id=draft_id).execute()
        return draft
    except Exception, e:
        print e

def compose_message(body,subject,contacts):
    message            = MIMEText(body)
    message['subject'] = subject
    message['from']    = me
    message['to']      = contacts
    #return message
    return {'raw': base64.urlsafe_b64encode(message.as_string())}

def sender(draft):
    agency = draft['agency']
    draft = draft['draft']
    try:
        sent = service.users().drafts().send(userId='me',body={'id':draft['id']}).execute()
        thread = service.users().threads().get(userId='me',id=sent['threadId']).execute()
        msg = thread['messages'][0]
        label_agency(msg,agency)
    except Exception, e:
        print('draft.id',draft['id'],'raised exception')
        log.log_data('msg',[{'draft_id':draft['id'],'agency':agency,'exception':e}])
    print('sent',sent)
    sleep(interval)

def delete_drafts(draft_ids=[]):
    if not draft_ids:
        # check for existence of drafts
        drafts = get_drafts()
        draft_ids = [x['id'] for x in drafts if type(drafts) == 'list'] #hack
    print('len(draft_ids)',len(draft_ids))
    dd = raw_input('existing drafts found ... delete ?[y/N]')
    if dd.lower() == 'y':
        print drafts 
        for draft_id in draft_ids:
            print 'deleting', draft_id
            service.users().drafts().delete(userId='me',id=draft_id).execute()

def get_drafts():
    drafts = service.users().drafts().list(userId='me',maxResults=2000).execute()
    if 'drafts' in drafts.keys(): 
        drafts = drafts['drafts']
    return drafts

