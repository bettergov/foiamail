# Setting Up

In order to set up FOIAmail, you'll need to do the following:

- create a virtual machine to run the services on (AWS EC2 Ubuntu is used in this example)
- install Python with the required dependencies
- set up & get credentials to a Google account for sending mail, managing contacts, storing attachment and reporting (via drive)
- import contacts and set up FOIA request template

This example uses an EC2 Ubuntu server but should work on any Ubuntu machine.

## Virtual Machine Setup

## SSH Access

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
sudo chmod 600 PATH/MY_KEY_PAIR.pem
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

## OS requirements

First, set the timezone.

```bash
sudo mv /etc/localtime /etc/localtime.bk
sudo cp /usr/share/zoneinfo/America/Chicago /etc/localtime
# Use the following to reset to UTC
# sudo dpkg-reconfigure --frontend noninteractive tzdata
```

```bash
sudo apt update
sudo apt install python-setuptools 
sudo apt install python-pip  
sudo pip install virtualenv 
sudo apt-get update
sudo apt-get install python-dev gcc 
```

## code requirements

```bash
git clone https://github.com/bettergov/foiamail.git
```

## python requirements

```bash
sudo apt install python-pip
cd foiamail
virtualenv ./
. bin/activate
pip install -r requirements.txt
```

If you're running Python 3 also run this:
```bash
pip install -r requirements.py3.txt
```

## Google Requirements

### create fresh google account
We recommend creating a new Google account. The app iterates through all contacts when drafting FOIAs, so an initially empty contacts list guarantees that no stray emails get loose.

### register google application

_incognito:_ https://console.cloud.google.com/home/dashboard  

Google might prompt you, if this is a new account, to accept terms and set a country. Do so, then continue by creating a project (click "Create Project").

Enter a project name and click create.

### Get Credentials

Once you've created a project, you'll be directed to the project dashboard. We're going to get a OAuth credentials JSON file.

From the dashboard, follow this series of menu options:

- left nav: click apis & services > oauth consent screen
  - user type: external
  - set application name, click save below
- left nav: credentials
  - create credentials
    - OAuth client ID
    - configure consent screen
    - application type: desktop
    - enter application name
    - if a dialog opens, close it, you should be on credentials page
    - find OAuth 2.0 row and click download icon
    - save file as `auth/client_secret.json` inside the `foiamail` directory

### Authorize Google APIs

Now you need to grant permission to specific Google services:

- APIs & Services > Library
  - search for and enable the following APIs:
    - Gmail API
    - Contacts API
    - Sheets API
    - Drive API

It might take a few minutes.

### Obtain credentials.dat

This is the final step to authorize the FOIAmail CLI application with Google services.

Activate the virtual environment:

```bash
cd foiamail
. bin/activate
```

Then trigger the Google credentials download by invoking the OAuth 2.0 flow: 

```bash
python mgr.py --get-cred
```

Follow the instructions to copy/paste the link into a browser, accept the requested permissions, and then enter the verification code found on the screen into the program. You'll probably get a "This app isn't verified" warning if you're using Chrome. Click "Advanced" and continue, ignoring the error. Make sure to allow all permissions requested.

### auth
The `auth` module works behind the scenes in every other FOIAMail module. The wrapper functions, `get_service()` and `get_gd_client()`, are called by Contacts, GMail, Drive and Sheets APIs to authenticate requests.  

The auth module depends on the `credentials.dat` file to verify requests.

Verify authorization:

```python
from auth.auth import test_cred
test_cred()
```

## Importing/Updating Contacts

The app handles contacts through the [Gmail Contacts screen](https://contacts.google.com/). Read Google's own documentation for [how to import contacts](https://support.google.com/contacts/answer/1069522).

Note that for a contact to be recognized by the app, the contact needs to have an **organization** filled in. The app will draft messages for **all** contacts with organizations.

## Importing a FOIA Request Template

A FOIA template should be saved to the `foiamail/msg` directory in one of the following formats:

- [Markdown document](https://daringfireball.net/projects/markdown/basics) `.md` (supports replacement variables and auto creates and attaches a PDF of your request upon draft creation)
- Microsoft Word document `.docx` (WARNING: do not use lists in your template!)

The template should be referenced in the `foia_doc` variable in the `msg` section of your `config/config.yaml` configuration file.  

This template file will be imported when drafting FOIA messages. Templates support the following variables that will be replaced for each contact upon creation of the draft:

- `{AGENCY}` the agency listed in the Contact info (`Organization 1 - Name` field from the contact CSV)
- `{DATE}` the date the draft was prepared

## Next Steps

See `docs/technical.md` for creating drafts, sending FOIA requests and monitoring/categorizing responses.
