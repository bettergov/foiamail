"""
creates and sends
foia messages
"""
from time import sleep
from log import log
from auth import auth
from docx import Document
from contacts.contacts import get_contacts_by_agency
from msg.utils import agency_slug
from msg.label import label_agency
from email.mime.text import MIMEText
import base64

### START CONFIG ###
foia_doc = 'msg/payroll-foia-2018.docx'
interval = 1  # seconds
subject = 'Payroll FOIA | '
me = 'me'
logtype = 'msg'
### END CONFIG ###
service = auth.get_service()


def distribute(send=False):
    """
    prepares drafts for each agency
    and sends if specified and tests pass

    due to potential for sending failure,
    this function will attempt to retry
    sending unsent drafts under the following conditions:
    - unsent agencies exist
    - previous attempts successfully sent 1 or more drafts
    *** retry logic is untested ***
    """
    retry = True
    drafts = prep_agency_drafts()
    if send and sanity_check(drafts):
        ready = input(
            'drafts created. inspect and type "send" to distribute')
        if ready.lower() == 'send':
            while retry:
                original_draft_len = len(drafts)
                for draft in drafts:
                    print('sending', draft)
                    sender(draft)
                # make sure everything sent, or else retry
                drafts = prep_agency_drafts()
                if drafts and len(drafts) < original_draft_len:
                    print(len(drafts), 'drafts remaining ... retrying')
                    continue
                elif not drafts:
                    retry = False
                    print('distribution complete.')
                elif drafts and len(drafts) == original_draft_len:
                    # drafts aren't sending, it's a lost cause. avoid infinite loop
                    retry = False
                    print('distribution incomplete:', len(drafts), 'unsent')
                else:
                    retry = False
        else:
            print('aborting')


def unsent_agency_contacts():
    """
    gets 
    contacts by agency
    for all unsent agencies
    """
    from report.response import get_threads
    contacts_by_agency = get_contacts_by_agency()
    return dict((agency, contacts_by_agency[agency]) for agency
                in contacts_by_agency if not get_threads(agency))


def prep_agency_drafts(contacts_by_agency=[]):
    """
    preps drafts for unsent agencies, with: 
    - agency name appended to subject
    - agency slug appended to body
    - agency name attached to draft list for labeling

    a draft is a dict containing
    - the gmail draft object
    - the name of the agency (for labeling)
    i.e.:
    draft = [{'agency': agency_name,'draft': draft}]

    """
    if not contacts_by_agency:
        contacts_by_agency = unsent_agency_contacts()
    # first delete existing drafts
    delete_drafts()
    # then create new drafts
    print('agencies to be prepped:', contacts_by_agency.keys())
    pd = input('prep drafts now? [y/N]')
    if pd.lower() == 'y':
        foia_text = load_foia_text()
        drafts = []
        for agency in contacts_by_agency:
            slug = agency_slug(agency)
            body = foia_text + '\r\n\r\n' + slug
            slug_subject = subject + agency
            contacts = ','.join(contacts_by_agency[agency])
            draft = {'agency': agency, 'draft': compose_draft(
                body, slug_subject, contacts)}
            # TODO label the draft here not when you send so you can verify thanks
            drafts.append(draft)
            print(draft)
        # TODO verify all agencies have a draft ... some get skipped i.e. service errors
        return drafts
    else:
        print('skipping')


def sanity_check(drafts):
    """
    look before you leap
    """
    print(drafts)
    print('len(drafts)', len(drafts))
    verify = input('Everything ready? [y/N]')
    return verify in ['Y', 'y']


def load_foia_text():
    """
    reads foia template from docx file as config'd
    """
    return '\r\n'.join([p.text for p in Document(docx=foia_doc).paragraphs])


def compose_draft(body, subject, contacts):
    """
    creates draft
    from message object
    and returns it
    """
    try:
        message = compose_message(body, subject, contacts)
        # return service.users().drafts().create(userId=me, body=message).execute()
        draft_id = service.users().drafts().create(
            userId='me', body={'message': message}).execute()['id']
        draft = service.users().drafts().get(userId='me', id=draft_id).execute()
        return draft
    except Exception as e:
        print(e)


def compose_message(body, subject, contacts):
    """
    composes message
    using message text, subject, contacts
    and returns it encoded
    """
    message = MIMEText(body)
    message['subject'] = subject
    message['from'] = me
    message['to'] = contacts
    # return message
    return {'raw': base64.urlsafe_b64encode(message.as_string())}


def sender(draft):
    """
    sends drafts with specified sleep interval,
    logs exceptions
    """
    agency = draft['agency']
    draft = draft['draft']
    try:
        sent = service.users().drafts().send(
            userId='me', body={'id': draft['id']}).execute()
        thread = service.users().threads().get(
            userId='me', id=sent['threadId']).execute()
        msg = thread['messages'][0]
        label_agency(msg, agency)
        print('sent', sent)
    except Exception as e:
        print('draft.id', draft['id'], 'raised exception: ', e)
        log.log_data(
            'msg', [{'draft_id': draft['id'], 'agency':agency, 'exception':e}])
    sleep(interval)


def delete_drafts(draft_ids=[]):
    """
    this can be handled via UI
    """
    if not draft_ids:
        # check for existence of drafts
        drafts = get_drafts()
        draft_ids = [x['id'] for x in drafts if type(drafts) == list]  # hack
    print('len(draft_ids)', len(draft_ids))
    dd = input('existing drafts found ... delete ?[y/N]')
    if dd.lower() == 'y':
        print(drafts)
        for draft_id in draft_ids:
            print('deleting', draft_id)
            service.users().drafts().delete(userId='me', id=draft_id).execute()


def get_drafts():
    """
    gets all drafts.
    only called by delete_drafts, may be unnecessary
    """
    drafts = service.users().drafts().list(userId='me', maxResults=2000).execute()
    if 'drafts' in drafts.keys():
        drafts = drafts['drafts']
    return drafts
