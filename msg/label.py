"""
creates labels as config'd for initial startup,
handles labeling automation as scheduled
"""
import logging
from contacts import contacts
from auth import auth
import base64
import email
from msg.utils import agency_slug
from datetime import datetime

### START CONFIG ###
# acceptable types of attachment for labeling and shipping purposes
att_exts = ['txt', 'csv', 'xls', 'xlsx', 'pdf', 'xlsm', 'xlt', 'ods', 'xlsb']
statuses = ['*unidentified', '*responded', '*attachment', '*done', '*NA']
### END CONFIG ###

service = auth.get_service()
contacts_by_agency = contacts.get_contacts_by_agency()
agencies = [agency for agency in contacts_by_agency.keys()]
slugs = [agency_slug(agency) for agency in agencies]
labels = service.users().labels().list(userId='me').execute()['labels']
agency_label_ids = [x['id'] for x in labels if 'agency' in x['name']]


def msgs_job(msgs=None, date=None):
    """
    control function to handle label automation
    """
    if not msgs:
        msgs = select_unlabeled_msgs(date=date)
    msg_label_queue = []
    for msg in msgs:
        msg_label_queue.append(check_labels(msg))
    update_labels(msg_label_queue)


def select_unlabeled_msgs(date=None):
    """
    this is maybe misnamed. 
    selects all messages after specified date (at midnight).
    defaults to today's messages
    e.g. date: datetime.datetime.strptime('2018/04/13','%Y/%m/%d')
    """
    # if not date:
    # date = datetime.now()
    # date = date.strftime('%Y/%m/%d')
    # query = 'after:' + date
    query = 'has:nouserlabels'
    return service.users().messages().list(userId='me', q=query).execute()['messages']


def check_labels(msg):
    """
    given a message, checks:
    - request status
    - agency name
    ... and returns dict for labeling
    """
    try:
        msg = service.users().messages().get(
            id=msg['id'], userId='me').execute()
    except Exception as e:
        logging.exception(e)
    req_status = check_req_status(msg)
    agency = check_agency_status(msg)
    return {'msg': msg, 'req_status': req_status, 'agency': agency}


def check_req_status(msg):
    """
    for incoming messages, checks if
    it has an attachment or not,
    then returns as '*attachment' or '*responded'
    """
    em_from = [x for x in msg['payload']['headers']
               if x['name'] == 'From'][0]['value']
    if em_from.split('@')[-1] == 'bettergov.org':
        return
    if get_atts(msg):
        return '*attachment'
    return '*responded'


def get_atts(msg):
    """
    scans a message's attachments
    and checks if atts have acceptable extensions
    as configured.
    returns accepted atts
    """
    # list len evals to bool
    atts = []
    if 'parts' in msg['payload'].keys():
        for part in msg['payload']['parts']:
            if 'filename' in part.keys() and \
                    part['filename'].split('.')[-1].lower() in att_exts:
                atts.append(part)
    return atts


def check_agency_status(msg):
    """
    checks to see if message contains an agency slug
    (i.e., char string between two # hashtags)
    and, if so, looks up to see what if any agency it belongs to.
    returns agency name
    """
    slug = check_agency_hashtag(msg)
    # sender_agency = check_sender_agency(msg)
    return lookup_agency_by_slug(slug)


def lookup_agency_by_slug(slug):
    """
    returns the name of the agency
    belonging to the specified slug,
    if any match
    """
    candidates = [x for x in agencies if x.replace(' ', '') == slug]
    if candidates:
        return candidates[0]


def check_agency_hashtag(msg):
    """
    reads messages, scanning for hashtag-delimited slugs.
    supports multipart and non-multipart messages
    """
    try:
        msg = service.users().messages().get(
            id=msg['id'], userId='me', format='raw').execute()
        body = base64.urlsafe_b64decode(msg['raw'].encode('ASCII'))
        em = email.message_from_bytes(body)

        if em.get_content_maintype() == 'multipart':
            match = recursive_match_scan(em)
        else:
            match = split_and_check(em.get_payload())
        return match
    except Exception:
        pass


def recursive_match_scan(em):
    """
    i don't know how to properly do recursion
    but it seems to make sense to start the function
    at the point where you know it's multipart
    """
    for part in em.get_payload():
        if part.get_content_maintype() == 'multipart':
            match = recursive_match_scan(part)
        else:
            match = split_and_check(part.get_payload())
        if match:
            return match
            # this return should bubble up to the top layer of recursion


def split_and_check(text):
    """
    given a scannable string,
    looks for hashtag-delimited text
    and returns it
    """

    try:
        text = base64.urlsafe_b64decode(text)
    except:
        pass
    for chunk in text.split('#'):
        if '#' + chunk + '#' in slugs:
            return chunk


def update_labels(msg_queue):
    """
    labels messages by
    - agency
    - status
    as specified
    """
    for x in msg_queue:
        try:
            msg = x['msg']
            if x['agency']:
                label_agency(msg, x['agency'])
            else:
                if not get_thread_agency_label(msg):
                    label_agency(msg, '*unidentified')
            if x['req_status']:
                label_status(msg, x['req_status'])
            logging.info('\t'.join([
                'labels',
                x['msg']['id'],
                x['agency'],
                x['req_status']
            ]))
        except Exception as e:
            logging.exception(e)


def label_agency(msg, agency):
    """
    specifies agency msg should get (or *unidentified)
    and applies it
    """
    if agency == '*unidentified':
        label_id = lookup_label('*unidentified')
    else:
        # see https://github.com/mattkiefer/gm/issues/1
        label_id = lookup_label('agency/' + agency)
    # TODO 2nd check if agency lookup
    if label_id:
        service.users().messages().modify(userId='me', id=msg['id'], body={
            "addLabelIds": [label_id]}).execute()


def label_status(msg, status):
    """
    specifies status label msg should get
    and applies it
    """
    status_label = lookup_label(status)
    # TODO 3rd check if agency assigned,
    # and if status is correct
    # then step through and see if it assigns
    if status_label:
        service.users().messages().modify(userId='me', id=msg['id'], body={
            "addLabelIds": [status_label]}).execute()


def get_thread_agency_label(msg):
    """
    checks if thread has agency label
    on any messages,
    if so, returns it
    """
    t = service.users().threads().get(
        userId='me', id=msg['threadId']).execute()
    for m in t['messages']:
        for lid in m['labelIds']:
            if lid in agency_label_ids:
                return [label['name'] for label in labels if label['id'] == lid][0]


def lookup_label(label_text, labels=labels):
    """
    returns the label id
    given the label name
    for api lookup purposes
    """
    #matches = [label for label in labels if label['name'].replace(' ','') == label_text]
    matches = [label for label in labels if label['name'] == label_text]
    if matches:
        return matches[0]['id']


def delete_labels(label_ids=None):
    """
    deletes labels
    """
    if not label_ids:
        dal = input(
            'delete ALL user labels? *this is a first-time setup thing* [y/N]')
        if dal.lower() == 'y':
            labels = service.users().labels().list(userId='me').execute()
            print(labels)
            label_ids = [x['id']
                         for x in labels['labels'] if x['type'] == 'user']
    for label_id in label_ids:
        print('deleting label', label_id)
        # TODO comment out
        service.users().labels().delete(userId='me', id=label_id).execute()


def create_labels(labels=[]):
    """
    creates labels based on 
    - agencies (defined by contacts)
    - statuses (defined in configs)
    """
    if not labels:
        labels += ['agency']
        # see https://github.com/mattkiefer/gm/issues/1
        labels += ['agency/' + agency for agency in agencies]
        labels += statuses
    for label in labels:
        print('creating label', label)
        service.users().labels().create(userId='me', body=make_label(label)).execute()


def make_label(label_text):
    """
    returns a label object
    conforming to api specs
    given a name
    """
    return {'messageListVisibility': 'show',
            'name': label_text,
            'labelListVisibility': 'labelShow'}
