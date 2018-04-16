"""
todo:
    batch label creation
"""
from log import log
from contacts import contacts
from auth import auth
import base64, email
from msg.utils import agency_slug
from datetime import datetime

### START CONFIG ###
# TODO put these in a project config file
att_exts = ['txt','csv','xls','xlsx','pdf'] 
statuses = ['*unidentified','*responded','*attachment','*done','*NA']
### END CONFIG ###

service = auth.get_service()
contacts_by_agency = contacts.get_contacts_by_agency()
agencies = [agency for agency in contacts_by_agency.keys()]
slugs = [agency_slug(agency) for agency in agencies]
labels = service.users().labels().list(userId='me').execute()['labels'] 
agency_label_ids = [x['id'] for x in labels if 'agency' in x['name']]

def msgs_job(msgs=None,date=None):
    if not msgs:
        msgs = select_unlabeled_msgs(date=date)
    msg_label_queue = []
    for msg in msgs:
        msg_label_queue.append(check_labels(msg))
    update_labels(msg_label_queue)

def select_unlabeled_msgs(date=None):
    """
    e.g. date: datetime.datetime.strptime('2018/04/13','%Y/%m/%d')
    """
    if not date: 
        date = datetime.now()
    date = date.strftime('%Y/%m/%d')
    query = 'after:' + date
    return service.users().messages().list(userId='me',q=query).execute()['messages']

def check_labels(msg):
    try:
        msg = service.users().messages().get(id=msg['id'],userId='me').execute()
    except Exception, e:
        print e
        import ipdb; ipdb.set_trace()
    req_status = check_req_status(msg)
    agency = check_agency_status(msg)
    return {'msg':msg,'req_status':req_status,'agency':agency}

def check_req_status(msg):
    em_from = [x for x in msg['payload']['headers'] if x['name'] == 'From'][0]['value']
    if em_from.split('@')[-1] == 'bettergov.org':
        return
    if get_atts(msg):
        return '*attachment'
    return '*responded'

def get_atts(msg):
    # list len evals to bool
    atts = []
    if 'parts' in msg['payload'].keys():
        for part in msg['payload']['parts']:
            if 'filename' in part.keys() and \
                    part['filename'].split('.')[-1].lower() in att_exts:
                atts.append(part)
    return atts

def check_agency_status(msg):
    hashtag = check_agency_hashtag(msg)
    # sender_agency = check_sender_agency(msg)
    return hashtag


def check_sender_agency(msg):
    # deprecated
    return
    # todo: check for multiple matches ie double agents
    sender = [x for x in msg['payload']['headers'] if x['name'] == 'From'][0]['value'] 
    matching_agencies = [agency for agency in contacts_by_agency if sender in contacts_by_agency[agency]]
    if matching_agencies:
        return matching_agencies[0]

def check_agency_hashtag(msg):
    try:
        msg = service.users().messages().get(id=msg['id'],userId='me',format='raw').execute()
        body = base64.urlsafe_b64decode(msg['raw'].encode('ASCII'))
        em = email.message_from_string(body)
        if em.get_content_maintype() == 'multipart':
            match = recursive_match_scan(em)
        else:
            match = split_and_check(em.get_payload())
        return match 
    except Exception, e:
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
    try:
        text = base64.urlsafe_b64decode(text)
    except:
        pass
    for chunk in text.split('#'):
        if '#' + chunk + '#' in slugs:
            return chunk
    for chunk in text.split('#'):
        if '#' + chunk + '#' in slugs:
            return chunk

def update_labels(msg_queue):
    for x in msg_queue:
        try:
            msg = x['msg']
            if x['agency']:
                label_agency(msg,x['agency'])
            else:
                if not get_thread_agency_label(msg):
                    label_agency(msg,'*unidentified')
            if x['req_status']:
                label_status(msg,x['req_status'])
            print 'labels', x['msg']['id'],x['agency'],x['req_status']
            #log.log_data('label',[{'msg_id':msg['id'],'agency':x['agency'] if x['agency'] else 'unidentified','status':x['req_status']}])
        except Exception, e:
            print e
            #import ipdb; ipdb.set_trace()

def label_agency(msg,agency):
    if agency == '*unidentified':
        label_id = lookup_label('*unidentified')
    else:
        label_id = lookup_label('agency/' + agency) # see https://github.com/mattkiefer/gm/issues/1
    #TODO 2nd check if agency lookup
    if label_id:
        service.users().messages().modify(userId='me', id=msg['id'],body={"addLabelIds":[label_id]}).execute()

def label_status(msg,status):
    status_label = lookup_label(status)
    #TODO 3rd check if agency assigned,
    # and if status is correct
    # then step through and see if it assigns
    #import ipdb; ipdb.set_trace()
    if status_label:
        service.users().messages().modify(userId='me', id=msg['id'],body={"addLabelIds":[status_label]}).execute()

def get_thread_agency_label(msg):
    t = service.users().threads().get(userId='me',id=msg['threadId']).execute()
    for m in t['messages']:
        for lid in m['labelIds']:
            if lid in agency_label_ids:
                return [label['name'] for label in labels if label['id'] == lid][0]

def lookup_label(label_text):
    #matches = [label for label in labels if label['name'].replace(' ','') == label_text]
    matches = [label for label in labels if label['name'] == label_text]
    if matches:
        return matches[0]['id']

def delete_labels(label_ids=None):
    if not label_ids:     
        dal = raw_input('delete ALL user labels? *this is a first-time setup thing* [y/N]')
        if dal.lower() == 'y':
            labels = service.users().labels().list(userId='me').execute()
            print labels
            label_ids = [x['id'] for x in labels['labels'] if x['type'] == 'user']
    for label_id in label_ids:
        print 'deleting label', label_id
        #TODO comment out
        service.users().labels().delete(userId='me',id=label_id).execute()

def create_labels(labels=[]):
    if not labels:
        labels += ['agency']
        labels += ['agency/' + agency for agency in agencies] # see https://github.com/mattkiefer/gm/issues/1 
        labels += statuses
    for label in labels:
        print 'creating label', label
        service.users().labels().create(userId='me',body=make_label(label)).execute()

def make_label(label_text):
    return {'messageListVisibility': 'show',
            'name': label_text,
            'labelListVisibility': 'labelShow'}
