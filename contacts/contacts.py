import csv
from auth import auth
import atom.data
import gdata.data
import gdata.contacts.data
from time import sleep
from log import log

### START CONFIG ###
#infile_path      = 'contacts/bga_contacts.csv'
infile_path      = 'contacts/redo_contacts.csv'
test_infile_path = 'contacts/test_contacts.csv'
test             = False
### END CONFIG ###
if test: infile_path = test_infile_path
gd_client = auth.get_gd_client()

def load_contacts():
    raw_input('creating contacts ... hit enter')
    for contact in import_contacts():
        try:
            sleep(1)
            new_contact = gdata.contacts.data.ContactEntry()
            new_contact.name = gdata.data.Name(full_name=gdata.data.FullName(text=contact['first_name'] + ' ' + contact['last_name']))
            new_contact.email.append(gdata.data.Email(address=contact['email'],primary='true'))
            new_contact.organization = gdata.data.Organization(name=gdata.data.OrgName(contact['agency']),rel='work')
            new_contact.email[0].label = 'work'
            contact_entry = gd_client.CreateContact(new_contact)
            print 'new contacts', contact_entry
        except Exception, e:
            print 'problem with',contact['email'], e
            log.log_data('contact',contact)

def import_contacts():
    return [x for x in csv.DictReader(open(infile_path))]

def get_contacts(max=2000):
    query = gdata.contacts.client.ContactsQuery()
    query.max_results = max
    return gd_client.GetContacts(query=query).entry

contacts = get_contacts()

def get_contacts_by_agency(contacts=get_contacts()):
    """
    modify contacts
    to get custom query of
    agency contacts
    """
    agency_contacts = {}
    for contact in contacts:
        if contact.organization:
            if contact.organization.name.text not in agency_contacts:
                agency_contacts[contact.organization.name.text] = []
            agency_contacts[contact.organization.name.text].append(contact.email[0].address)
    return agency_contacts

def get_contact_emails():
    return [contact.email[0].address for contact in contacts]

def already_a_contact(email):
    contact_emails = get_contact_emails()
    return email in contact_emails

def delete_contacts(cs=[]):
    if not cs:
        dac = raw_input('delete ALL contacts? [y/N]')
        if dac.lower == 'y':
            cs = contacts
    for c in cs:
        gd_client.Delete(c.GetEditLink().href,force=True)
