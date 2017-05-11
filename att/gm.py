import base64, os
from auth.auth import get_service
from msg.label import agencies, get_atts
from report.response import get_threads, get_status
from att.drive import get_or_create_atts_folder,\
        check_if_drive, make_drive_folder, upload_to_drive

### START CONFIG ###
buffer_path = '/tmp/'
### END CONFIG ###

gmail_service = get_service(type='gmail')

def roll_thru():
    atts_drive_folder = get_or_create_atts_folder()
    for agency in agencies:
        try:
            threads = get_threads(agency)
            if not check_if_drive(agency) and check_if_done(threads,agency): 
                # only proceed if agency is done, has atts and not already in drive
                atts = get_agency_atts(threads)
                if atts:
                    print agency
                    drive_folder = make_drive_folder(agency,atts_drive_folder)
                    for att in atts:
                        path = download_buffer_file(att)
                        upload_to_drive(att, drive_folder)
                        os.remove(path)
            else:
                print 'skipping', agency
        except Exception, e:
            print agency,'failed',e

def check_if_done(threads,agency):
    return get_status(threads,agency) == 'done'

def get_agency_atts(threads):
    atts = []
    for thread in threads:
        for msg in gmail_service.users().threads().get(\
                id=thread['id'],userId='me').execute().get('messages'):
            for att in get_atts(msg):
                atts.append({'att_id':att['body']['attachmentId'],'msg_id':msg['id'],'file_name':att['filename']})
    return atts

def download_buffer_file(att):  
    attachment = gmail_service.users().messages().attachments().get(\
            id=att['att_id'],messageId=att['msg_id'],userId='me').execute()
    file_data = base64.urlsafe_b64decode(attachment['data'].encode('UTF-8'))
    buffer_file_path = buffer_path + att['file_name'] 
    buffer_file = open(buffer_file_path,'w')
    buffer_file.write(file_data)
    buffer_file.close()
    return buffer_file_path

