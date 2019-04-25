# setting up
This example uses an EC2 Ubuntu server but should work on any Ubuntu machine.

## ssh access

This assumes you have already set up an AWS account and are logged in as an IAM user with access to the Amazon EC2 Console. If not, check out Amazon's documentation to [sign up for AWS](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/get-set-up-for-amazon-ec2.html#sign-up-for-aws) and [create an IAM user](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/get-set-up-for-amazon-ec2.html#create-an-iam-user).

### creating a key pair

From Amazon's documentation:
> AWS uses public-key cryptography to secure the login information for your instance. A Linux instance has no password; you use a key pair to log in to your instance securely. You specify the name of the key pair when you launch your instance, then provide the private key when you log in using SSH.

Follow [Amazon's instructions](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/get-set-up-for-amazon-ec2.html#create-a-key-pair) to create a key pair from the EC2 console. In the end, you should have a private key of the form `YOUR_KEY_PAIR.pem`.

### launching the instance

Follow [Amazon's instructions](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EC2_GetStarted.html#ec2-launch-instance). Use the key pair you set up in the previous part. Also make sure to take note of your Amazon Machine Image (AMI).

### connecting to your instance using your key pair

You can connect to your EC2 instance many ways — this is just one option.

Note the following:
* The private key location (e.g., `PATH/MY_KEY_PAIR.pem`)
* The public DNS name of the **instance** (e.g., `ec2-##-###-##-##.MY-REGION.compute.amazonaws.com`)
* The default **user** name for the AMI that you used to launch your instance (e.g., `ubuntu` for Ubuntu AMI (full list [here](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/AccessingInstancesLinux.html)))

With this information, we can connect to the EC2 instance using SSH.
```bash
ssh -i PATH/MY_KEY_PAIR.pem user@aws-instance
```

You can use a command-line tool like [ssh-agent](https://www.ssh.com/ssh/agent) to manage your SSH keys.

### Adding multiple keys to the EC2 instance

Sometimes you may want to add multiple keys to the EC2 instance. For example, you may want to grant someone temporary access without having to recreate a key when you want to revoke that access.

***There is no doubt in my mind that this isn't the best option, so if you know a better way, let me know.***

In order to add an additional key, we will just be manually updating the server's authorized keys now that we have direct access.

#### 1. generating a keypair on your local computer ([instructions](https://www.ssh.com/ssh/keygen/#sec-Creating-an-SSH-Key-Pair-for-User-Authentication)).
#### 2. adding the new public key to your EC2 instance
```bash
cat NewKey.pub | ssh -i OriginalKey.pem user@amazon-instance "cat >> .ssh/authorized_keys"
```
#### 3. testing the new key
```bash
ssh -i NewKey.pem user@aws-instance
```

## os requirements
First, set the timezone.
```bash
sudo mv /etc/localtime /etc/localtime.bk
sudo cp /usr/share/zoneinfo/America/Chicago /etc/localtime
# Use the following to reset to UTC
# sudo dpkg-reconfigure --frontend noninteractive tzdata
```

Then set up python and pipenv.
```bash
# instructions for setting up python3 on ubuntu 18.04

# make sure versions are up to date
sudo apt update
sudo apt -y upgrade

# check that Python 3 is installed
python3 -V

# install pip3
sudo apt install -y python3-pip

# add other python dev packages
sudo apt install build-essential libssl-dev libffi-dev python3-dev

# install pipenv
pip3 install --user pipenv
source ~/.profile
```

## code requirements
```bash
git clone https://github.com/bettergov/foiamail.git
```

## python requirements
```bash
cd foiamail
export PIPENV_VENV_IN_PROJECT=1
pipenv install
```

## google requirements
### create fresh google account
We recommend creating a new Google account. The app iterates through all contacts when drafting FOIAs, so an initially empty contacts list guarantees that no stray emails get loose.

### register google application
https://console.cloud.google.com/home/dashboard  
create project

### get credentials
- apis & services
  - credentials
    - create credentials
      - oath clientid
      - configure consent screen
      - application type: other
      - save client_secret.json to foiamail/auth/ and add path to auth.py config

```bash
scp client_secret.json ubuntu@ec2-XX-XXX-XXX-XXX.us-east-2.compute.amazonaws.com:~/foiamail/auth/client_secret.json
```

### authorize google apis
- apis & services
  - library
  - enable the following apis:
    - gmail api
    - contacts api
    - sheets api
    - drive api
 
It might take a few minutes.

### obtain credentials.dat
Activate the virtual environment and open a python console:
```bash
pipenv run python
```
Then trigger the Google credentials download by invoking the OAuth 2.0 flow: 
```python
from auth.auth import get_cred
```
Follow the instructions to copy/paste the link into a browser, then enter the verification code found on the screen.


### auth
The `auth` module works behind the scenes in every other FOIAMail module. The wrapper functions, `get_service()` and `get_gd_client()`, are called by Contacts, GMail, Drive and Sheets APIs to authenticate requests.  

The auth module depends on the credentials.dat file to verify requests.  

Verify authorization:
```python
from auth.auth import test_cred
test_cred()
```

*Note: The Drive test won't pass if your Drive is empty.*

# importing/updating contacts
The app handles contacts through the [Gmail Contacts screen](https://mail.google.com/mail/u/0/#contacts). Read Google's own documentation for [how to import contacts](https://support.google.com/contacts/answer/1069522?hl=en&visit_id=1-636625309780616904-2128193528&rd=3).

Note that for a contact to be recognized by the app, the contact needs to have an **organization** filled in. The app will draft messages for **all** contacts with organizations.

**TODO**: Create a sample contacts file with the right column headers.

# composing/sending messages
Once contacts are loaded, FOIAs messages may be drafted and sent using the `msg` module.

## importing a template
A FOIA template should be saved to the `foiamail/msg` directory in .docx format and referenced in the configuration section of `compose.py`.  

This template file will be imported when drafting FOIA messages.


## creating drafts
The FOIAMail application creates one draft for each agency. These drafts are based off the above-referenced template and are identical with the following exceptions:
- Each draft's `To:` field includes all email contacts on file under its agency's name.
- Each draft's `Body` field is appended with the agency_slug unique identifier. (Whitespace-stripped, title-cased, and appended/prepended by hashtags `#`, as defined in `mgs.utils`. e.g.: `#ArlingtonHeights#`)

To create drafts, call the `distribute()` function in the `msg.compose` module. Leaving the keyword argument `drafts` to the default empty list, which prompts for preparation of new drafts for each agency.

```python
from msg.compose import distribute
distribute()
```


## sending
To send, call `msg.compose` module's `distribute()` function with `send=True`.

```python
from msg.compose import distribute
distribute(send=True)
```

# labeling
FOIAMail attempts to label incoming messages in two taxonomies:
1. name of the agency responding 
2. status of response

The `msg.label` module handles labeling for all incoming messages. The main wrapper function at work is `check_labels()`, which calls `check_req_status` and `check_agency_status()`.  

## agency
`check_agency_status()` assigns an agency name to the message thread by scanning it for the agency_slug identifier, e.g. #ArlingtonHeights#.  
(It's worth noting that agency labels assigned to initial FOIA request messages should remain intact with standard reply messages. i.e., this is a GMail feature that doesn't depend on FOIAMail logic.)
`check_req_status()` returns one or none of the following status labels:
- `*responded` is the default assigned value for an incoming message label
- `*attachment` means the message has an attachment with an acceptable extension (e.g., xls, xlsx, csv, txt, pdf)

## status
Note: There are two request statuses that are manually assigned by a team member: 
- `*done` indicates that the agency has responded with data and the data/format appears to meet the requirements of the request
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
`write_to_log()` writes the agency name, status, and links to GMail threads into a Google Sheet, as defined by Drive file name in the configuration section of the `report.reponse` module.

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

# misc
