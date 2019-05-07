"""
downloads gmail atts
"""

import base64
import logging
import os
from auth.auth import get_service
from msg.label import agencies, get_atts
from report.response import get_threads, get_status
from att.drive import get_or_create_atts_folder,\
    check_if_drive, get_or_create_drive_folder, upload_to_drive

### START CONFIG ###
buffer_path = '/tmp/'
### END CONFIG ###

gmail_service = get_service(type='gmail')


def roll_thru(agencies=agencies):
    """
    controller function rolls through each agency:
    - checks if already filed in Drive
    - checks if labeled done
    ... if neither:
    - makes Drive folder
    - downloads buffer file to this server
    - uploads file to Drive folder
    - deletes buffer file

    TODO: optimize by check_if_drive first before getting threads
    """
    atts_drive_folder = get_or_create_atts_folder()
    total_agencies = len(agencies)

    for i, agency in enumerate(agencies):
        index = str(i+1).zfill(3)
        threads = get_threads(agency)

        # no apostrophes allowed
        agency_cleaned = agency.replace("'", "")

        # move on if agency is marked done
        if not check_if_done(threads, agency):
            logging.info(
                f'{index}/{total_agencies} skipping {agency} - not marked done')
            continue

        # move on if agency folder already exists
        if check_if_drive(agency_cleaned):
            logging.info(
                f'{index}/{total_agencies} skipping {agency} - agency folder already exists')
            continue

        # execute below code if everything above fails
        atts = get_agency_atts(threads)

        logging.info(f'{index}/{total_agencies} starting {agency}')
        drive_folder = get_or_create_drive_folder(
            agency_cleaned, atts_drive_folder)

        for att in atts:
            path = download_buffer_file(att)
            upload_to_drive(att, drive_folder)
            os.remove(path)


def check_if_done(threads, agency):
    """
    checks if this agency's threads 
    include any messages labeled 'done'
    """

    return get_status(threads, agency) in ('done', 'shipped')


def get_agency_atts(threads):
    """
    given a list of threads,
    iterates through messages,
    finds attachments
    and appends att data to atts list
    """
    atts = []
    for thread in threads:
        for msg in gmail_service.users().threads().get(
                id=thread['id'], userId='me').execute().get('messages'):
            for att in get_atts(msg):
                atts.append({'att_id': att['body']['attachmentId'],
                             'msg_id': msg['id'], 'file_name': att['filename']})
    return atts


def download_buffer_file(att):
    """
    downloads specified att to
    buffer file 
    and returns path
    """
    attachment = gmail_service.users().messages().attachments().get(
        id=att['att_id'], messageId=att['msg_id'], userId='me').execute()
    file_data = base64.urlsafe_b64decode(attachment['data'].encode('UTF-8'))
    buffer_file_path = buffer_path + att['file_name']
    buffer_file = open(buffer_file_path, 'wb')
    buffer_file.write(file_data)
    buffer_file.close()
    return buffer_file_path
