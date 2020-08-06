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
build_drafts = '--build-drafts' in argv
send_drafts = '--send-drafts' in argv
build_labels = '--build-labels' in argv
delete_labels = '--delete-labels' in argv


def init_contacts(delete=False):
    if delete:
        # TODO fix
        contacts.delete_contacts()
    contacts.load_contacts()


def init_labels(delete=False):
    if delete:
        label.delete_labels()
    label.create_labels()


def init_msgs(send=False):
    compose.distribute(send=send)
    if not send:
        print('send with init_msgs(send=True)')


if build_labels:
    print("Building labels...")
    if delete_labels:
        print("... and deleting labels ...")
    init_labels(delete=delete_labels)


if build_drafts:
    print("Building drafts...")
    init_msgs(send=False)


if send_drafts:
    init_msgs(send=True)


# cron
if cron_label:
    print("Running labeler...")
    label.msgs_job()


if cron_atts:
    print("Fetching attachments...")
    gm.roll_thru()


if cron_report:
    response.init()
