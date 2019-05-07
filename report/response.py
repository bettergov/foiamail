"""
writes a response report to Drive with:
    - agency name
    - status
    - link to thread
"""
import csv
import logging
from auth.auth import get_service
from msg.label import agencies, lookup_label
from att.drive import check_if_drive

### START CONFIG ###
outfile_path = 'report/reports/response.csv'
outfile_headers = ['agency', 'status', 'threads']
sheet_filename = 'agency_response_log'
STATUSES = ['SENT', '*responded', '*attachment', '*done', '*NA']
### END CONFIG ###
service = get_service()
drive_service = get_service(type='drive')
sheets_service = get_service(type='sheets')

# save labels to file scope w/ single API call
# reference this variable for label lookups
LABELS = service.users().labels().list(userId='me').execute()['labels']


def init(report_agencies=None):
    """
    starts response report
    """
    if not report_agencies:
        report_agencies = agencies  # for debugging

    outfile, outcsv = setup_outfile()
    roll_thru(report_agencies, outcsv)
    outfile.close()

    with open(outfile_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    sorted_rows = sorted(rows, key=lambda x: (x['status'], x['agency']))
    write_to_log(sorted_rows)


def setup_outfile():
    """
    creates the local file for writing the report to csv
    """
    outfile = open(outfile_path, 'w')
    outcsv = csv.DictWriter(outfile, outfile_headers)
    outcsv.writeheader()
    return outfile, outcsv


def roll_thru(agencies, outcsv):
    """
    collects agency statuses and thread urls,
    writing results to file
    """
    num_agencies = len(agencies)

    for i, agency in enumerate(agencies):
        logging.info(f'({str(i+1).zfill(3)}/{num_agencies}) {agency}')
        threads = get_threads(agency)

        try:
            status = get_status(threads, agency) if threads else None
        except Exception as e:
            logging.exception(e)
            status = 'error'

        row = {'agency': agency, 'status': status,
               'threads': get_label_url('agency/' + agency)}
        logging.info(row)
        outcsv.writerow(row)


def get_threads(agency):
    """
    gets all threads labeled as specified agency
    """
    agency_label_id = lookup_label('agency/' + agency, LABELS)

    if agency_label_id:
        return service.users().threads().list(userId='me', labelIds=agency_label_id).execute()['threads']


def get_status(threads, agency):
    """
    gets the 'highest' status
    found in the specified threads
    """
    agency_statuses = set()

    for t in threads:
        thread = service.users().threads().get(
            userId='me', id=t['id']).execute()
        for m in thread['messages']:
            # get label objects where label id in m['labelIds']
            m_labels = [x for x in LABELS if x['id'] in m['labelIds']]

            # filter down to just "status" labels
            m_statuses = [x['name'] for x in m_labels if x['name'] in STATUSES]

            agency_statuses.update(m_statuses)

    # TODO: loop thru statuses list (in desc order of precedence)
    if check_if_drive(agency.replace("'", "")):  # no apostrophes allowed
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


def get_label_url(label):
    """
    gets url for all threads matching the given label
    """
    import urllib.parse
    return 'https://mail.google.com/mail/u/0/#label/' + urllib.parse.quote_plus(label)

### DRIVE ###


def get_or_create_log(name=sheet_filename):
    """
    gets or creates the agency response log in Drive
    """
    log_query = drive_service.files().list(
        q="name='" + sheet_filename + "'").execute().get('files')
    if log_query:
        log = log_query[0]
    else:
        log = drive_service.files().create(body={'name': sheet_filename,
                                                 'mimeType': 'application/vnd.google-apps.spreadsheet'}).execute()
    return log


def write_to_log(data):
    """
    takes the locally written agency response log csv
    and writes to Sheets file as specified
    """
    # get/create and clear
    log = get_or_create_log()
    sheets_service.spreadsheets().values().clear(
        spreadsheetId=log['id'], range='Sheet1', body={}).execute()
    # headers
    values = [outfile_headers]
    # data
    for row in data:
        values.append([row['agency'], row['status'], row['threads']])
    body = {'values': values}
    result = sheets_service.spreadsheets().values().update(
        spreadsheetId=log['id'], range='Sheet1', valueInputOption='RAW', body=body).execute()
