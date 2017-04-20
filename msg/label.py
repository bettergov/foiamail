"""
todo:
    batch label creation
"""
from log import log
from contacts import contacts
from auth import auth
import base64
from msg.utils import agency_slug

### START CONFIG ###
att_exts = ['txt','csv','xls','xlsx','pdf']
statuses = ['*unidentified','*responded','*attachment','*done']
### END CONFIG ###

service = auth.get_service()
contacts_by_agency = contacts.get_contacts_by_agency()
agencies = [agency for agency in contacts_by_agency.keys()]
labels = service.users().labels().list(userId='me').execute()['labels'] 

def msgs_job():
    msgs = select_unlabeled_msgs()
    msg_label_queue = []
    for msg in msgs:
        msg_label_queue.append(check_labels(msg))
        print msg
    update_labels(msg_label_queue)

def select_unlabeled_msgs():
    #return service.users().messages().list(q='has:nouserlabels',userId='me').execute()['messages']
    return service.users().messages().list(userId='me').execute()['messages']

def check_labels(msg):
    msg = service.users().messages().get(id=msg['id'],userId='me').execute()
    req_status = check_req_status(msg)
    agency = check_agency_status(msg)
    return {'msg':msg,'req_status':req_status,'agency':agency}

def check_req_status(msg):
    if check_att(msg):
        return '*attachment'
    return '*responded'

def check_att(msg):
    # list len evals to bool
    has_att = False
    if 'parts' in msg['payload'].keys():
        for part in msg['payload']['parts']:
            if 'filename' in part.keys() and \
                    part['filename'].split('.')[-1] in att_exts:
                has_att = True
    return has_att

def check_agency_status(msg):
    hashtag = check_agency_hashtag(msg)
    sender_agency = check_sender_agency(msg)
    return hashtag or sender_agency

def check_sender_agency(msg):
    # todo: check for multiple matches ie double agents
    sender = [x for x in msg['payload']['headers'] if x['name'] == 'From'][0]['value'] 
    matching_agencies = [agency for agency in contacts_by_agency if sender in contacts_by_agency[agency]]
    if matching_agencies:
        return matching_agencies[0]

def check_agency_hashtag(msg):
    try:
        msg = service.users().messages().get(id=msg['id'],userId='me',format='raw').execute()
        body = base64.urlsafe_b64decode(msg['raw'].encode('ASCII'))
        splits = body.split('#')
        matches = [x for x in splits if x in agencies]
        return matches and matches[0] 
    except Exception, e:
        import ipdb; ipdb.set_trace()

def update_labels(msg_queue):
    for x in msg_queue:
        try:
            msg = x['msg']
            if x['agency']:
                label_agency(msg,x['agency'])
            else:
                label_agency(msg,'*unidentified')
            if x['req_status']:
                label_status(msg,x['req_status'])
            print 'labels', x
            #log.log_data('label',{'msg_id':msg['id'],'agency':x['agency'] if x['agency'] else 'unidentified','status':x['status']})
        except Exception, e:
            print e
            import ipdb; ipdb.set_trace()

def label_agency(msg,agency):
    label_id = lookup_label(agency)
    if label_id:
        service.users().messages().modify(userId='me', id=msg['id'],body={"addLabelIds":[label_id]}).execute()

def label_status(msg,status):
    status_label = lookup_label(status)
    if status_label:
        service.users().messages().modify(userId='me', id=msg['id'],body={"addLabelIds":[status_label]}).execute()

def lookup_label(label_text):
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
        labels += agencies 
        labels += statuses
    for label in labels:
        print 'creating label', label
        service.users().labels().create(userId='me',body=make_label(label)).execute()

def make_label(label_text):
    return {'messageListVisibility': 'show',
            'name': label_text,
            'labelListVisibility': 'labelShow'}
