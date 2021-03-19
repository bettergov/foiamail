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
from time import sleep
from log import log

from msg.utils import user_input, error_info
from config import config


infile_path = config.data["contacts"]["infile_path"]
test_infile_path = config.data["contacts"]["test_infile_path"]
test = config.data["contacts"]["test"]


# test allows you to send sample FOIAs to test email addresses
# ********
# WARNING! google contacts API will cache contacts ...
# ********
# make sure to verify test contacts are deleted when prepping for production
# https://github.com/mattkiefer/foiamail/issues/29
if test:
    infile_path = test_infile_path

people_service = auth.get_service(type="people").people()


def load_contacts():
    """
    loads contacts via api
    """
    user_input('about to create contacts. press enter to continue...')
    for contact in import_contacts():
        try:
            sleep(1)
            body = {
                "names": [{"givenName": contact["Name"]}],
                "emailAddresses": [{"value": contact['E-mail 1 - Value']}],
                "organizations": [{"current": True, "name": contact['Organization 1 - Name']}]
            }
            print("new contacts", body)
        except Exception as e:
            print('problem with', contact['E-mail 1 - Value'], error_info(e))
            log.log_data('contact', contact)


def import_contacts():
    """
    reads contacts from file
    """
    return [x for x in csv.DictReader(open(infile_path))]


def get_contacts(max=1000):
    """
    requests all contacts from api
    """
    contacts = []
    page_token = None
    while True:
        results = people_service.connections().list(resourceName="people/me",
                                                    pageSize=max,
                                                    personFields="names,organizations,"
                                                    "emailAddresses,userDefined",
                                                    pageToken=page_token).execute()
        contacts += results["connections"]
        if "nextPageToken" in results:
            page_token = results["nextPageToken"]
        else:
            break
    return contacts


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
        if "organizations" in contact:
            org_name = contact["organizations"][0]["name"]
            if org_name not in agency_contacts:
                agency_contacts[org_name] = []
            agency_contacts[org_name].append(
                contact["emailAddresses"][0]["value"])
    return agency_contacts


def get_contact_emails():
    """
    returns email address of each contact
    """
    return [contact["emailAddresses"][0]["value"] for contact in contacts]


def already_a_contact(email):
    """
    checks if contact already exists
    """
    contact_emails = get_contact_emails()
    return email in contact_emails


def delete_contacts(cs=None):
    """
    delete contacts using API
    """
    if not cs:
        dac = user_input('delete ALL contacts? [y/N]: ')
        if dac.lower == 'y':
            cs = get_contacts()
    for c in cs:
        people_service.deleteContact(resourceName=c["resourceName"]).execute()
