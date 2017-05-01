import csv
from auth.auth import get_service
from msg.label import agencies, lookup_label

### START CONFIG ###
outfile_path = 'report/reports/response.csv'
outfile_headers = ['agency','status','threads']
statuses = ['SENT','*responded','*attachment']
### END CONFIG ###
service = get_service()
#TODO: build dict of label ids, names for status labels to reduce API calls

def init():
    outfile, outcsv = setup_outfile()
    roll_thru(agencies,outcsv)
    outfile.close()

def setup_outfile():
    outfile = open(outfile_path,'w')
    outcsv = csv.DictWriter(outfile,outfile_headers)
    outcsv.writeheader()
    return outfile, outcsv

def roll_thru(agencies,outcsv):
    for agency in agencies:
        threads = get_threads(agency)
        status = get_status(threads) if threads else None
        thread_urls = get_thread_urls(threads) if threads else None
        row = {'agency':agency,'status':status,'threads':thread_urls}
        print row
        outcsv.writerow(row)
    
def get_threads(agency):
    agency_label_id = lookup_label('agency/' + agency)
    if agency_label_id:
        try:
            return service.users().threads().list(userId='me',labelIds=agency_label_id).execute()['threads']
        except Exception, e:
            print agency, e

def get_status(threads):
    agency_statuses = set()
    for t in threads:
        thread = service.users().threads().get(userId='me',id=t['id']).execute()
        for m in thread['messages']:
            for lid in m['labelIds']:
                label = service.users().labels().get(userId='me',id=lid).execute()
                if label['name'] in statuses:
                    agency_statuses.add(label['name'])
    # TODO: loop thru statuses list (in desc order of precedence)
    if '*attachment' in agency_statuses:
        return 'attachment'
    elif '*responded' in agency_statuses:
        return 'responded'
    elif 'SENT' in agency_statuses:
        return 'SENT'

def get_thread_urls(threads):
    return ' '.join(['https://mail.google.com/mail/u/2/#inbox/' + thread['id'] for thread in threads])
