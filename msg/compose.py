"""
creates and sends
foia messages
"""
from __future__ import print_function
from datetime import datetime
# TODO: python2 mode
import io
import re
from time import sleep
from log import log
from docx import Document
# python 2
try:
    from email.MIMEMultipart import MIMEMultipart
# python 3
except ModuleNotFoundError:
    from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import base64
import markdown
from weasyprint import HTML

from auth import auth
from contacts.contacts import get_contacts_by_agency
from msg.utils import agency_slug, user_input
from msg.label import label_agency


# TODO: move all this into separate configs (JSON/YAML files?)
# TODO: proper markdown -> plaintext support. right now this
# just removes <br/> tags and assumes the md is already email text
### START CONFIG ###
foia_doc       = 'msg/foia.md'
# Uncomment the below line for original FOIA message functionality, note
# the DOCX list bug -- lists will be missing from your final FOIA message
# so make sure to not use them
# foia_doc       = 'msg/foia.docx'
interval       = 1 # seconds
subject        = ' Non-commercial FOIA'
me             = 'me'
logtype        = 'msg'
### END CONFIG ###
service = auth.get_service()


def distribute(send=False):
    """
    prepares drafts for each agency
    and sends if specified and tests pass

    due to potential for sending failure,
    this function will attempt to retry
    sending unsent drafts under the following conditions:
    - unsent agencies exist
    - previous attempts successfully sent 1 or more drafts
    *** retry logic is untested ***
    """
    retry = True
    drafts = prep_agency_drafts()
    if send and sanity_check(drafts):
        ready = user_input('drafts created. inspect and type "send" to distribute')
        if ready.lower() == 'send':
            while retry:
                original_draft_len = len(drafts)
                for draft in drafts:
                    print(('sending', draft))
                    sender(draft)
                # make sure everything sent, or else retry
                drafts = prep_agency_drafts()
                if drafts and len(drafts) < original_draft_len:
                    print((len(drafts), 'drafts remaining ... retrying'))
                    continue
                elif not drafts:
                    retry = False
                    print('distribution complete.')
                elif drafts and len(drafts) == original_draft_len:
                    # drafts aren't sending, it's a lost cause. avoid infinite
                    # loop
                    retry = False
                    print(('distribution incomplete:', len(drafts), 'unsent'))
                else:
                    retry = False
        else:
            print('aborting')


def unsent_agency_contacts():
    """
    gets
    contacts by agency
    for all unsent agencies
    """
    from report.response import get_threads
    contacts_by_agency = get_contacts_by_agency()
    print('contacts_by_agency', contacts_by_agency)
    return dict((agency, contacts_by_agency[agency]) for agency
                in contacts_by_agency if not get_threads(agency))


def prep_agency_drafts(contacts_by_agency=None):
    """
    preps drafts for unsent agencies, with:
    - agency name appended to subject
    - agency slug appended to body
    - agency name attached to draft list for labeling

    a draft is a dict containing
    - the gmail draft object
    - the name of the agency (for labeling)
    i.e.:
    draft = [{'agency': agency_name,'draft': draft}]

    """
    if not contacts_by_agency:
        contacts_by_agency = unsent_agency_contacts()
    # first delete existing drafts
    delete_drafts()
    # then create new drafts
    print(('agencies to be prepped:', list(contacts_by_agency.keys())))
    pd = user_input('prep drafts now? [y/N]')
    if pd.lower() == 'y':
        drafts = []
        date = datetime.now().date().strftime("%a, %b %d, %Y")
        for agency in contacts_by_agency:
            foia_text = load_foia_text(
                AGENCY=agency.title(), DATE=date
            )
            slug = agency_slug(agency)
            body = foia_text + '\r\n\r\n' + slug
            slug_subject = agency.title() + subject
            contacts = ','.join(contacts_by_agency[agency])
            draft = {
                "agency": agency,
                "draft": compose_draft(body, slug_subject, contacts),
            }
            # TODO label the draft here not when you send so you can verify
            # thanks
            drafts.append(draft)
            print(draft)
        # TODO verify all agencies have a draft ... some get skipped i.e.
        # service errors
        return drafts
    else:
        print('skipping')


def sanity_check(drafts):
    """
    look before you leap
    """
    print(drafts)
    print(('len(drafts)', len(drafts)))
    verify = user_input('Everything ready? [y/N]')
    return verify in ['Y', 'y']


def html_to_text(body):
    no_tags = re.sub(r"<br\s*/>", "\n", body)
    return no_tags


def strip_markdown(md_body):
    """
    NOTE: Works poorly for lists right now.
    """
    def unmark_element(element, stream=None):
        if stream is None:
            stream = io.StringIO()
        if element.text:
            stream.write(element.text)
        for sub in element:
            unmark_element(sub, stream)
        if element.tail:
            stream.write(element.tail)
        return stream.getvalue()

    # patching Markdown
    markdown.Markdown.output_formats["plain"] = unmark_element
    __md = markdown.Markdown(output_format="plain")
    __md.stripTopLevelTags = False

    def unmark(text):
        unmarked = __md.convert(text)
        no_tags = re.sub(r"<br\s*/>", "\n", unmarked)
        return no_tags

    return unmark(md_body)


def load_foia_text(**kwarg_replacements):
    """
    reads foia template from docx file as config'd

    this will apply any replacements in the text using keys/values found
    in kwarg_replacements (passed as keyword args)
    """
    if foia_doc.endswith(".docx"):
        # TODO: this has a bad error where it doesn't capture any
        # of the text inside of a list, the paragraph of a list is blank
        return '\r\n'.join([
            p.text for p in Document(docx=foia_doc).paragraphs
        ])
    elif foia_doc.endswith(".md"):
        with open(foia_doc, "r") as f:
            text = f.read()
            for key in kwarg_replacements.keys():
                search = "{%s}" % (key)
                replace = kwarg_replacements[key]
                text = text.replace(search, replace)
            # make all line endings windows
            text = re.sub("\n", "\r\n", re.sub("\r\n", "\n", text))
            # make sure we don't have any un-replaced replacements, this
            # would be bad to send
            err_msg = "Found un-replaced replacement variable in text"
            assert "{" not in text and "}" not in text, err_msg
            print("Plaintext:\n%s" % (text))
            return text
    else:
        err_msg = "Unknown FOIA template: %s. Valid types: .docx, .md" % (
            foia_doc
        )
        raise NotImplementedError(err_msg)


def load_foia_pdf(foia_text):
    foia_html = markdown.markdown(foia_text.replace("#", "\#"))
    doc = HTML(file_obj=foia_html)
    buf = io.BytesIO()
    doc.write_pdf(target=buf)
    buf.seek(0)
    pdf = buf.read()
    return pdf


def compose_draft(body, subject, contacts):
    """
    creates draft
    from message object
    and returns it
    """
    message = compose_message(body, subject, contacts)
    # return service.users().drafts().create(userId=me, body=message).execute()
    draft_id = service.users().drafts().create(
        userId='me', body={'message': message}).execute()['id']
    draft = service.users().drafts().get(userId='me', id=draft_id).execute()
    return draft


def compose_message(body, subject, contacts):
    """
    composes message
    using message text, subject, contacts
    and returns it encoded
    """
    message = MIMEMultipart()
    message['subject'] = subject
    message['from'] = me
    message['to'] = contacts

    plaintext_body = html_to_text(body)
    print("Plaintext:\n%s" % (plaintext_body))
    message.attach(MIMEText(plaintext_body, "plain"))

    # Attach the pdf to the msg going by e-mail
    pdf = load_foia_pdf(body)
    if pdf:
        attach = MIMEApplication(pdf, _subtype="pdf")
        # attach = MIMEApplication(f.read(),_subtype="pdf")
        attach.add_header(
            'Content-Disposition', 'attachment', filename="records-request.pdf"
        )
        message.attach(attach)

    # python2
    try:
        return {'raw': base64.urlsafe_b64encode(message.as_string())}
    # python 3
    except TypeError:
        enc_bytes = base64.urlsafe_b64encode(message.as_bytes())
        return {'raw': enc_bytes.decode("utf-8")}


def sender(draft):
    """
    sends drafts with specified sleep interval,
    logs exceptions
    """
    agency = draft['agency']
    draft = draft['draft']
    try:
        sent = service.users().drafts().send(
            userId='me', body={'id': draft['id']}).execute()
        thread = service.users().threads().get(
            userId='me', id=sent['threadId']).execute()
        msg = thread['messages'][0]
        label_agency(msg, agency)
        print(('sent', sent))
    except Exception as e:
        print(('draft.id', draft['id'], 'raised exception: ', e))
        log.log_data(
            'msg', [{'draft_id': draft['id'], 'agency':agency, 'exception':e}])
    sleep(interval)


def delete_drafts(draft_ids=None):
    """
    this can be handled via UI
    """
    if not draft_ids:
        # check for existence of drafts
        drafts = get_drafts()
        draft_ids = [x['id'] for x in drafts if type(drafts) == list]  # hack
    print(('len(draft_ids)', len(draft_ids)))
    dd = user_input('existing drafts found ... delete ?[y/N]')
    if dd.lower() == 'y':
        print(drafts)
        for draft_id in draft_ids:
            print('deleting', draft_id)
            service.users().drafts().delete(userId='me', id=draft_id).execute()


def get_drafts():
    """
    gets all drafts.
    only called by delete_drafts, may be unnecessary
    """
    drafts = service.users().drafts().list(
        userId='me', maxResults=2000
    ).execute()
    if 'drafts' in list(drafts.keys()):
        drafts = drafts['drafts']
    return drafts
