# <3 CAT
from __future__ import print_function
from auth import auth
from log import log
from msg import compose, label
from contacts import contacts
from sys import argv
from report import response
from att import gm
cron_label = '--label' in argv
cron_atts = '--atts' in argv
cron_report = '--report' in argv

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


def init_msgs(send=False):
    if send:
        compose.distribute(send=send)
    else:
        print('send with init_msgs(send=True)')


# cron
if cron_label:
    label.msgs_job()

if cron_atts:
    gm.roll_thru()

if cron_report:
    response.init()
