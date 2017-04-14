import csv
from auth.auth import get_cred

### START CONFIG ###
infile_path  = 'contacts.csv'
### END CONFIG ###


def import_contacts():
    return [x for x in csv.DictReader(open(infile_path))]


def load_contacts():
    for contact in import_contacts():
        new_contact.name = gdata.data.Name(full_name=gdata.data.FullName(text='FOO Officer'))
        new_contact.email.append(gdata.data.Email(address='foo2',primary='true'))
        new_contact.email[0].label = 'foo'
        contact_entry = gd_client.CreateContact(new_contact)
