# foimail
A framework for mass FOIA campaigns. Distribute public records requests, manage responses and organize file attachments using GMail, Sheets and Drive.

Technically, it's a bunch of a API calls on cron.

# first-time technical setup
First, set up your server, environment, credentials and FOIA template (see [setting up](docs/setting-up.md)).

Once the server, environment and repository are set up, use `mgr.py` to initialize the application.

```bash
# load the manager shell
ipython -i mgr.py
```

```python
# load contacts directly in Gmail,
# then wait several minutes

# then generate labels
init_labels()

# prepare drafts and send messages
init_msgs(send=True)
```

[Install a crontab](http://www.ubuntututorials.com/use-crontab-ubuntu/) to run the following tasks at regular intervals:
- `mgr.py --label`, to label incoming messages by agency and status (every few minutes)
- `mgr.py --atts`, to migrate GMail attachments to Drive (nightly)
- `mgr.py --report`, to generate a status report of agency responses in Google Sheets (nightly, after attachments migrate)

This is a good time to double-check the server timezone is set to America/Chicago. See [technical docs](docs/technical.md).

# ongoing manual work
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

# technical docs
See [docs/technical.md](docs/technical.md) for detailed explanations of commands.
