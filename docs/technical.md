# Importing Contacts

As of this writing, the workflow to import contacts involves uploading a csv file via the gmail ui. Use the `config/contacts_template.csv`, populating *Name* (optional), *Organization 1 - Name* and *Email 1 - Value* fields before uploading to [Google Contacts](https://contacts.google.com).

By default, contacts imported via CSV end up in an isolated "Imported on MONTH/DAY" label. These are not visible to FOIAmail. Make sure to move any imported contacts "into contacts" by using the "add to contacts" button at the top of the list, from inside the created label. You have to select the contacts in order see this button.

# Composing/Sending Messages

Once contacts are loaded, FOIAs messages may be drafted and sent using the `msg` module.

## Configuration

FOIAmail support configuration via a YAML file. You should copy the example config, `config/config.example.yaml` to `config/config.yaml` and edit the options to your liking.

## Importing a Template

A FOIA template should be saved to as `config/foia.md` (markdown, default) or `config/foia.docx`. If you're not using `config/foia.md`, then set the `msg.compose.foia_doc` variable of the `config/config.yaml` configuration file to the template you're using. There's an example FOIA message `config/foia.example.md` that demonstrates using replacement variables.

The template file will be imported when drafting FOIA messages.

If you choose a Markdown template, a PDF will also be created and attached to your FOIA drafts, in addition to the body of the email containing your FOIA message.

## Creating Drafts

The FOIAMail application creates one draft for each agency. These drafts are based off the above-referenced template and are customized per-agency in the following ways:

- Each draft's `To:` field includes all email contacts on file under its agency's name.
- Each draft's `Body` field is appended with the agency_slug unique identifier. (Whitespace-stripped, title-cased, and appended/prepended by hashtags `#`, as defined in `mgs.utils`. e.g.: `#ArlingtonHeights#`)
- If your FOIA template contains any replacement variables (e.g., `{AGENCY}` and `{DATE}`), these will be replaced with the agency name and date of draft creation, per agency.
- If your FOIA template is a Markdown formatted file, (e.g., `config/foia.md`), then your message will *also* be converted to a PDF and attached to the request. The agency slug will not be added to the PDF.

To create drafts, call the `distribute()` function in the `msg.compose` module. Leaving the keyword argument `drafts` to the default empty list, which prompts for preparation of new drafts for each agency.

Via the Python shell:

```python
from msg.compose import distribute
distribute()
```

Or via the command line:

```bash
python mgr.py --build-drafts
```

## Sending FOIA Requests

Once you're happy with the drafts, it's time to send them out.

To send, call `msg.compose` module's `distribute()` function with `send=True`.

```python
from msg.compose import distribute
distribute(send=True)
```

Or you can do this via the command line:

```bash
python mgr.py --send-drafts
```

If there are any existing drafts existing, FOIAmail will prompt you to delete them, first. It is suggested that you do so, as the drafts are created fresh each time you run `--build-drafts` or `--send-drafts`.

# Response Labeling

FOIAMail attempts to label incoming messages in two taxonomies:

1. name of the agency responding 
2. status of response

The `msg.label` module handles labeling for all incoming messages. The main wrapper function at work is `check_labels()`, which calls `check_req_status` and `check_agency_status()`.  

## Agency

`check_agency_status()` assigns an agency name to the message thread by scanning it for the agency_slug identifier, e.g. #ArlingtonHeights#.  
(It's worth noting that agency labels assigned to initial FOIA request messages should remain intact with standard reply messages. i.e., this is a GMail feature that doesn't depend on FOIAMail logic.)
`check_req_status()` returns one or none of the following status labels:
- `*responded` is the default assigned value for an incoming message label
- `*attachment` means the message has an attachment with an acceptable extension (e.g., xls, xlsx, csv, txt, pdf)

## status

Note: There are two request statuses that are manually assigned by a team member: 
- `*done` indicates that the agency has responded with data and the data/format appears to meet the requirements of the request
- `*installment` indicates that the agency has responded with data and the data/format appears to meet the requirements of the request, but the request is not yet complete (more installments are coming)
- `*NA` indicates "not applicable." i.e., the agency does not exist or has no employees, or this is a duplicate request, etc.


\# TODO: explain labeling distinctions when it comes to messages vs threads


# filing attachments
FOIAmail will file attachments from completed responses in designated Drive folder, specifically in a subdirectory named after the agency. These operations are typically performed globally via cronjob. 

## reading emails
The `att.gm` module contains functions related to detecting GMail attachments, as well as control logic for downloading those attachments to buffer files, uploading them to Drive (see below) and removing buffer files. This process can be described as "shipping" attachments.   

The `roll_thru()` function performs these tasks globally, iterating through each agency and checking if it meets these requirements to ship attachments:
1. agency folder doesn't exist
2. agency has a message thread labeled `\*done`

Note that attachment shipping is greedy by design in that it will ship every attachment of every file extension, from every message and thread belonging to that agency.

Also note that FOIAMail does not label threads as shipped since there doesn't seem to be much of a use case for this feature.  

## writing to drive
The `att.drive` module contains functions related to uploading and filing completed attachments to the above-referenced Drive folder. 

# reporting statuses
The `report.response` module generates a Google Sheet listing each distinct agency found in Contacts and its FOIA request status. Control logic is found in the `roll_thru()` function.


## looking up agency status
The relevant status-lookup logic is found in the `get_status()` function. This function returns an agency's highest status in this descending order: 
- `shipped` if a Drive folder exists under the agency's name
- `*N/A` if a thread has been labeled as such
- `*done` if a thread has been labeled as such
- `*attachment` if a thread has been labeled as such
- `*responded` if a thread has been labeled as such
- `SENT` if a thread has been labeled as such 
- `no status available` suggests no threads were found under the agency label
 

## writing to sheet
`write_to_log()` writes the agency name, status, and links to GMail threads into a Google Sheet, as defined by Drive file name in the `report` section of the `config/config.yaml` config file.

# management
Commands to manage the FOIAmail workflow are found under `foiamail/mgr.py' and may be invoked manually or via cron.

## mgr
`mgr.py` includes management commands for the following one-time initialization tasks, typically invoked manually:
- creating/deleting contacts \# does deletion work?
- creating/deleting labels 
- creating/sending/deleting draft messages

... as well as the following tasks repeated at regular intervals (typically invoked via cron; see below):
- labeling message threads by agency and response status
- migrating attachments to Drive
- generating the response report

## cron
Because the GMail API doesn't expose hooks to trigger actions on message receipt, FOIAMail uses cron jobs to act as a daemon to perform these actions at regular intervals.

Here's a sample crontab:
```bash
# m h  dom mon dow   command
*/15 7-19 * * * cd /home/matt/projects/bga/gm && . bin/activate && python mgr.py --label > /home/matt/projects/bga/gm/log/logs/cron-label
0 5 * * * cd /home/matt/projects/bga/gm && . bin/activate && python mgr.py --report > /home/matt/projects/bga/gm/log/logs/cron-report
50 6-20 * * * cd /home/matt/projects/bga/gm && . bin/activate && python mgr.py --atts > /home/matt/projects/bga/gm/log/logs/cron-atts
```


# logging things
There are logging functions found in `log.log` that are designed to write debugging data for FOIAMail's core functions.  

 
## types of logging
Logs are configured for the following:
- stdout
- auth
- contact
- message
- label
- report
- att
