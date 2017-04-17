import log

### START CONFIG ###


### END CONFIG ###
contacts_by_agency = get_contacts_by_agency()
hashtags = [agency for agency in contacts_by_agency.keys()]

def msgs_job():
    msgs = select_unlabeled_msgs()
    msg_label_queue = []
    for msg in msgs:
        msg_label_queue.append(check_labels(msg))
    update_labels(msg_label_queue)

def select_unlabeled_msgs():
    pass

def check_labels(msg):
    req_status = check_req_status(msg)
    agency = check_agency(msg)
    return {'msg':msg,'req_status':req_status,'agency':agency}

def check_req_status(msg):
    if check_att(msg):
        return 'attachment'
    return 'response'

def check_att():
    #TODO check for attachment
    pass

def check_agency_status(msg):
    hashtag_agency = check_agency_hashtag(msg)
    sender_agency = check_sender_agency(msg)
    return hashtag or sender_agency

def check_sender_agency(msg):
    # todo: check for multiple matches ie double agents
    return [agency for agency in contacts_by_agency if msg.sender in contacts_by_agency[agency]][0] 


def hashtag_agency(msg):
    #TODO find faster way to do this,
    # check api syntax for body text
    splits = msg.body().split('#')
    #TODO: handle multiple hashtag results (unlikely)
    matches = [x for x in splits if x.find(' ') == -1 and x in hashtags]
    return matches[0] and matches


def update_labels(msg_queue):
    for msg in msg_queue:
        if msg_queue[msg]['agency']:
            pass # TODO: update label
        else:
            pass # TODO: label unidentified
        if msg_queue[msg]['req_status']:
            pass # TODO: update req status

def label_sent(msg):
    pass # TODO: label message sent
