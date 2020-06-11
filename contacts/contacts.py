"""
this module
- loads contacts
- returns contacts by agency:
    {agency:[contacts]}
  which produces an agency list
"""
from __future__ import print_function
import csv
from auth import auth
import gdata.data
import gdata.contacts.data
from time import sleep
from log import log

from msg.utils import user_input


### START CONFIG ###
#infile_path      = 'contacts/bga_contacts.csv'
infile_path = 'contacts/contacts.csv'
test_infile_path = 'contacts/test-contacts.csv'
test = False
### END CONFIG ###


# test allows you to send sample FOIAs to test email addresses
# ********
# WARNING! google contacts API will cache contacts ...
# ********
# make sure to verify test contacts are deleted when prepping for production
# https://github.com/mattkiefer/foiamail/issues/29
if test:
    infile_path = test_infile_path
gd_client = auth.get_gd_client()


def load_contacts():
    """
    loads contacts via api
    """
    user_input('creating contacts ... hit enter')
    for contact in import_contacts():
        try:
            sleep(1)
            new_contact = gdata.contacts.data.ContactEntry()
            new_contact.name = gdata.data.Name(full_name=gdata.data.FullName(
                text=contact['first_name'] + ' ' + contact['last_name']))
            new_contact.email.append(gdata.data.Email(
                address=contact['email'], primary='true'))
            new_contact.organization = gdata.data.Organization(
                name=gdata.data.OrgName(contact['agency']), rel='work')
            new_contact.email[0].label = 'work'
            contact_entry = gd_client.CreateContact(new_contact)
            print('new contacts', contact_entry)
        except Exception as e:
            print('problem with', contact['email'], e)
            log.log_data('contact', contact)


def import_contacts():
    """
    reads contacts from file
    """
    return [x for x in csv.DictReader(open(infile_path))]


def get_contacts(max=2000):
    """
    requests all contacts from api
    """
    query = gdata.contacts.client.ContactsQuery()
    query.max_results = max
    return gd_client.GetContacts(query=query).entry


contacts = get_contacts()


def get_contacts_by_agency(contacts=None):
    """
    modify contacts
    to get custom query of
    agency contacts
    """
    if contacts is None:
        contacts = get_contacts()
    agency_contacts = {}
    for contact in contacts:
        if contact.organization:
            if contact.organization.name.text not in agency_contacts:
                agency_contacts[contact.organization.name.text] = []
            agency_contacts[contact.organization.name.text].append(
                contact.email[0].address)
    return agency_contacts


def get_contact_emails():
    """
    returns email address of each contact
    """
    return [contact.email[0].address for contact in contacts]


def already_a_contact(email):
    """
    checks if contact already exists
    """
    contact_emails = get_contact_emails()
    return email in contact_emails


def delete_contacts(cs=None):
    """
    don't think this works but you can do it from the UI
    """
    if not cs:
        dac = user_input('delete ALL contacts? [y/N]')
        if dac.lower == 'y':
            cs = get_contacts()
    for c in cs:
        gd_client.Delete(c.GetEditLink().href, force=True)
