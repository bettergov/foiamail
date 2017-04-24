from auth import auth
from log import log
from msg import compose, label
from contacts import contacts
from sys import argv
cron = '--cron' in argv

# contacts
def init_contacts(delete=False):
    if delete:
        # TODO fix
        contacts.delete_contacts()
    contacts.load_contacts()            

# labels
def init_labels(delete=False):
    if delete:
        label.delete_labels()
    label.create_labels()

# msg
def init_msgs(delete=False,send=False):
    if delete:
        compose.delete_drafts()
        #compose.prep_agency_drafts()
    if send:
        compose.distribute(send=send)
    else:
        print 'send with init_msgs(send=True)'

## cron
if cron:
    label.msgs_job()


# sheets




# drive?
