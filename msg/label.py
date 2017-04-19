import log
from contacts import contacts
from auth import auth
import base64
### START CONFIG ###
att_exts = ['txt','csv','xls','xlsx','pdf']
### END CONFIG ###
service = auth.get_service()
contacts_by_agency = contacts.get_contacts_by_agency()
hashtags = [agency for agency in contacts_by_agency.keys()]


def msgs_job():
    msgs = select_unlabeled_msgs()
    msg_label_queue = []
    for msg in msgs:
        msg_label_queue.append(check_labels(msg))
    update_labels(msg_label_queue)

def select_unlabeled_msgs():
    return service.users().messages().list(q='has:nouserlabels',userId='me').execute()['messages']

def check_labels(msg):
    msg = service.users().messages().get(id=msg['id'],userId='me').execute()
    req_status = check_req_status(msg)
    agency = check_agency_status(msg)
    return {'msg':msg,'req_status':req_status,'agency':agency}

def check_req_status(msg):
    if check_att(msg):
        return 'attachment'
    return 'response'

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
    return [agency for agency in contacts_by_agency if msg.sender in contacts_by_agency[agency]][0] 

def check_agency_hashtag(msg):
    try:
        return base64.decodestring(msg['payload']['parts'][0]['parts'][0]['body']['data']).split('#')[1]
        splits = base64.urlsafe_b64decode(msg['raw'].encode('ASCII')).split('#')
        matches = [x for x in splits if x in hashtags]
        return matches and matches[0] 
    except Exception, e:
        import ipdb; ipdb.set_trace()

def update_labels(msg_queue):
    for msg in msg_queue:
        if msg_queue[msg]['agency']:
            msg['labelIds'].append(msg['agency'])
        else:
            msg['labelIds'].append(msg['unidentified'])
        if msg_queue[msg]['req_status']:
            msg['labelIds'].append(msg['req_status'])

def label_sent(msg):
        msg['labelIds'].append(msg['sent'])
