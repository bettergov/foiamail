# first-time technical setup
See [technical docs](docs/technical.md) for detailed instructions.  

Once the server, environment and repository are set up, use `mgr.py` to initialize the application.

```bash
# load the manager shell
ipython -i mgr.py
```

```python
# load contacts per configuration
init_contacts()

# then generate labels
init_labels()

# prepare drafts and send messages
init_msgs(send=True)
```

Install a crontab to run the following tasks at regular intervals:
- `mgr.py --label`, to label incoming messages by agency and status (every few minutes)
- `mgr.py --atts`, to migrate GMail attachments to Drive (nightly)
- `mgr.py --report`, to generate a status report of agency responses in Google Sheets (nightly, after attachments migrate)

This is a good time to double-check the server timezone is set to America/Chicago. See [technical docs](docs/technical.md).

# ongoing manual work
_Verify draft FOIA messages before sending_  

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

