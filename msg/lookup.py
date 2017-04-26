from auth.auth import get_service

def get_subject(msg):
    return [x['value'] for x in msg['payload']['headers'] if x['name'].lower() == 'subject'][0]


def get_msg_by_subject(msgs,keyword):
    matches = []
    for msg in msgs['messages']:
        msg = service.users().messages().get(id=msg['id'],userId='me').execute()
        subject = get_subject(msg)
        if keyword in subject:
            matches.append(service.users().messages().get(id=msg['id'],userId='me').execute())
    return matches
