# FOIAmail

![foiamail art by lucas ian smith](https://github.com/bettergov/foiamail/blob/master/IMG_0441_01.jpg)

A framework for mass FOIA campaigns. Distribute public records requests, manage responses and organize file attachments using GMail, Sheets and Drive.

Technically, it's a bunch of a API calls on cron.

# First-time technical setup

First, set up your server, environment, credentials and FOIA template (see [setting up](docs/setting-up.md)).

Once the server, environment, repository and credentials are set up, use `mgr.py` to initialize the application.

Load contacts directly in Gmail via the import contacts CSV option. See [docs/technical.md](docs/technical.md) for detailed walkthrough of the full FOIAmail workflow for importing contacts.

When your contacts are loaded, build agency labels for your contacts:

```bash
python mgr.py --build-labels
```

Next, prepare drafts for your contacts. You can look through the drafts and find any errors before you send them out:

```bash
python mgr.py --build-drafts
```

Once everything looks good, you can send them out with this command:

```bash
python mgr.py --send-drafts
```

(The `--build-drafts` and `--send-drafts` will re-create the drafts each time, so make sure you delete them when prompted.)

## Monitoring Responses

There are two ways to run the monitoring system for tagging/categorizing incoming emails, building reports and downloading responsive attachments: traditional VM using cron and Docker.

### Traditional VM/Cron

[Install a crontab](http://www.ubuntututorials.com/use-crontab-ubuntu/) to run the following tasks at regular intervals:
- `mgr.py --label`, to label incoming messages by agency and status (every few minutes)
- `mgr.py --atts`, to migrate GMail attachments to Drive (nightly)
- `mgr.py --report`, to generate a status report of agency responses in Google Sheets (nightly, after attachments migrate)

This is a good time to double-check the server timezone is set to America/Chicago. See [technical docs](docs/technical.md).

### Docker

There's a `Dockerfile` for running the services. If you have `make` you can simply run:

```bash
make docker_start
```

Or you can do it yourself:

```bash
docker build . -t foiamail
docker run --mount source=foiamail_logs,target=/home/ubuntu/foiamail/log/logs -t foiamail
```

# Ongoing manual work

_Verify draft FOIA messages before sending, including message count, contents, recipients and labels_  

Routine checklist for operating FOIAMail:
- Monitor incoming email regularly:
  - respond to questions 
  - identify issues with responses
  - report any problems
- Apply agency labels where automation fails
- Label messages '\*done' after determining an agency has responded with an acceptable data file
  - All attachments belonging to this agency's emails will migrate to Drive overnight
- Label messages '\*NA' for agencies that no longer exist or have no employees
- Throughout the project, particularly after the FOIA deadline has passed, use the response report to identify non-responsive agencies and go nudge them
- Update contact information via the GMail interface as necessary

# Technical docs

See [docs/technical.md](docs/technical.md) for detailed explanations of commands.
