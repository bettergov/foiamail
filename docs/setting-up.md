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

## os requirements
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
sudo easy_install pip  
sudo pip install virtualenv 
sudo apt-get update
sudo apt-get install python-dev gcc 
```

## code requirements
```bash
git clone https://github.com/mattkiefer/foiamail.git
```

## python requirements
```bash
sudo apt install python-pip
cd foiamail
virtualenv ./
. bin/activate
pip install -r requirements.txt
```

## google requirements
### create fresh google account
We recommend creating a new Google account. The app iterates through all contacts when drafting FOIAs, so an initially empty contacts list guarantees that no stray emails get loose.

### register google application
_incognito:_ https://console.cloud.google.com/home/dashboard  
create project

### get credentials
- apis & services
  - credentials
    - create credentials
      - oath clientid
      - configure consent screen
      - application type: desktop
      - save client_secret.json to foiamail/auth/ and add path to auth.py config


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
cd foiamail
. bin/activate
python
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

# importing/updating contacts
The app handles contacts through the [Gmail Contacts screen](https://mail.google.com/mail/u/0/#contacts). Read Google's own documentation for [how to import contacts](https://support.google.com/contacts/answer/1069522?hl=en&visit_id=1-636625309780616904-2128193528&rd=3).

Note that for a contact to be recognized by the app, the contact needs to have an **organization** filled in. The app will draft messages for **all** contacts with organizations.

# importing a template
A FOIA template should be saved to the `foiamail/msg` directory in .docx format and referenced in the configuration section of `compose.py`.  

This template file will be imported when drafting FOIA messages.
