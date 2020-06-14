"""
downloads gmail atts
"""
from __future__ import print_function

import base64
import os
import traceback

from auth.auth import get_service
from msg.label import agencies, get_atts
from msg.utils import error_info
from report.response import get_threads, get_status
from att.drive import (
    get_or_create_atts_folder, check_if_drive, make_drive_folder,
    upload_to_drive
)
from config import config


buffer_path = config.data["att"]["buffer_path"]

gmail_service = get_service(type='gmail')


def roll_thru():
    """
    controller function rolls through each agency:
    - checks if already filed in Drive
    - checks if labeled done
    ... if neither:
    - makes Drive folder
    - downloads buffer file to this server
    - uploads file to Drive folder
    - deleteds buffer file

    TODO: optimize by check_if_drive first before getting threads
    """
    atts_drive_folder = get_or_create_atts_folder()
    for agency in agencies:
        clean_agency = agency.replace("'", "")
        try:
            threads = get_threads(agency)
            if not check_if_done(threads, agency):
                print("skipping '%s' (not marked done)" % (agency))
                continue

            # don't create a bunch of blank directories every time we get
            # a response (whether or not we have an attachment)
            drive_folder = check_if_drive(clean_agency)
            if drive_folder:
                drive_folder = make_drive_folder(
                    clean_agency, atts_drive_folder
                )

            # only proceed if agency is done, has atts and not already in drive
            atts = get_agency_atts(threads)
            if atts:
                print(agency)
                # no apostrophes allowed
                drive_folder = make_drive_folder(
                    clean_agency, atts_drive_folder
                )
                for att in atts:
                    path = download_buffer_file(att)
                    upload_to_drive(att, drive_folder)
                    os.remove(path)
        except Exception as e:
            print(agency, 'failed', error_info(e))


def check_if_done(threads, agency):
    """
    checks if this agency's threads
    include any messages labeled 'done'
    """
    return get_status(threads, agency) == 'done'


def get_agency_atts(threads):
    """
    given a list of threads,
    iterates through messages,
    finds attachments
    and appends att data to atts list
    """
    atts = []
    for thread in threads:
        messages = gmail_service.users().threads().get(
            id=thread['id'], userId='me'
        ).execute().get('messages')
        for msg in messages:
            for att in get_atts(msg):
                atts.append({
                    'att_id': att['body']['attachmentId'],
                    'msg_id': msg['id'],
                    'file_name': att['filename']
                })
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
    buffer_file = open(buffer_file_path, 'w')
    buffer_file.write(file_data)
    buffer_file.close()
    return buffer_file_path
