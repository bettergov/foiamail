"""
TODO: 
build dict of label ids, 
names for status labels 
to reduce API calls
"""
import csv
from auth.auth import get_service
from msg.label import agencies, lookup_label
from att.drive import check_if_drive

### START CONFIG ###
outfile_path = 'report/reports/response.csv'
outfile_headers = ['agency','status','threads']
sheet_filename = 'agency_response_log'
statuses = ['SENT','*responded','*attachment','*done','*NA']
### END CONFIG ###
service = get_service()
drive_service = get_service(type='drive')
sheets_service = get_service(type='sheets')

def init(report_agencies=None):
    if not report_agencies: report_agencies=agencies #for debugging
    outfile, outcsv = setup_outfile()
    roll_thru(report_agencies,outcsv)
    outfile.close()

def setup_outfile():
    outfile = open(outfile_path,'w')
    outcsv = csv.DictWriter(outfile,outfile_headers)
    outcsv.writeheader()
    return outfile, outcsv

def roll_thru(agencies,outcsv):
    rows = []
    for agency in agencies:
        print agency
        threads = get_threads(agency)
        try:
            status = get_status(threads,agency) if threads else None
        except Exception, e:
            print e
            status = 'error'
        thread_urls = get_thread_urls(threads) if threads else None
        row = {'agency':agency,'status':status,'threads':thread_urls}
        rows.append(row)
        print row
        outcsv.writerow(row)
    sorted_rows = sorted(rows, key = lambda x: (x['status'],x['agency']))
    write_to_log(sorted_rows)
    
def get_threads(agency):
    agency_label_id = lookup_label('agency/' + agency)
    if agency_label_id:
        try:
            return service.users().threads().list(userId='me',labelIds=agency_label_id).execute()['threads']
        except Exception, e:
            print agency, e

def get_status(threads,agency):
    agency_statuses = set()
    for t in threads:
        thread = service.users().threads().get(userId='me',id=t['id']).execute()
        for m in thread['messages']:
            for lid in m['labelIds']:
                label = service.users().labels().get(userId='me',id=lid).execute()
                if label['name'] in statuses:
                    agency_statuses.add(label['name'])
    # TODO: loop thru statuses list (in desc order of precedence)
    if check_if_drive(agency):
        return 'shipped'
    elif '*NA' in agency_statuses:
        return 'NA'
    elif '*done' in agency_statuses:
        return 'done'
    elif '*attachment' in agency_statuses:
        return 'attachment'
    elif '*responded' in agency_statuses:
        return 'responded'
    elif 'SENT' in agency_statuses:
        return 'sent'
    else:
        return 'no status available'

def get_thread_urls(threads):
    return '\r\n'.join(['https://mail.google.com/mail/u/2/#inbox/' + thread['id'] for thread in threads])

### DRIVE ###

def get_or_create_log(name=sheet_filename):
    log_query = drive_service.files().list(q="name='" + sheet_filename + "'").execute().get('files')
    if log_query:
        log = log_query[0]
    else:
        log = drive_service.files().create(body={'name':sheet_filename,\
                'mimeType': 'application/vnd.google-apps.spreadsheet'}).execute()
    return log

def write_to_log(data):
    # get/create and clear
    log = get_or_create_log()
    sheets_service.spreadsheets().values().clear(spreadsheetId=log['id'],range='Sheet1',body={}).execute()
    # headers
    values = [outfile_headers]
    # data
    for row in data:
        values.append([row['agency'],row['status'],row['threads']])
    body = {'values':values}
    result = sheets_service.spreadsheets().values().update(\
            spreadsheetId=log['id'],range='Sheet1',valueInputOption='RAW',body=body).execute()
