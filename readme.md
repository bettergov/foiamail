yet another foia automation service

# setup
## Setting up SSH access

This assumes you have already set up an AWS account and are logged in as an IAM user with access to the Amazon EC2 Console. If not, check out Amazon's documentation to [sign up for AWS](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/get-set-up-for-amazon-ec2.html#sign-up-for-aws) and [create an IAM user](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/get-set-up-for-amazon-ec2.html#create-an-iam-user).

### Create a key pair

From Amazon's documentation:
> AWS uses public-key cryptography to secure the login information for your instance. A Linux instance has no password; you use a key pair to log in to your instance securely. You specify the name of the key pair when you launch your instance, then provide the private key when you log in using SSH.

Follow [Amazon's instructions](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/get-set-up-for-amazon-ec2.html#create-a-key-pair) to create a key pair from the EC2 console. In the end, you should have a private key of the form `YOUR_KEY_PAIR.pem`.

### Launch the instance

Follow [Amazon's instructions](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EC2_GetStarted.html#ec2-launch-instance). Use the key pair you set up in the previous part. Also make sure to take note of your Amazon Machine Image (AMI).

### To connect to your instance using your key pair

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

#### 1. Generate a keypair on your local computer ([instructions](https://www.ssh.com/ssh/keygen/#sec-Creating-an-SSH-Key-Pair-for-User-Authentication)).
#### 2. Add the new public key to your EC2 instance
```bash
cat NewKey.pub | ssh -i OriginalKey.pem user@amazon-instance "cat >> .ssh/authorized_keys"
```
#### 3. Test the new key
```bash
    ssh -i NewKey.pem user@aws-instance
```



## os requirements
```
sudo apt install python-setuptools 
sudo easy_install pip  
sudo pip install virtualenv 
```

## code requirements
```
git clone https://github.com/mattkiefer/foiamail.git
```

## python requirements
```
cd foiamachine
virtualenv ./
. bin/activate
pip install requirements
```

## google requirements
### register google application
https://console.cloud.google.com/home/dashboard
create project
- iam & admin
  - api credentials
    - create credentials
      - oath clientid
        - (download client_secret.json to foiamail/auth/ and add path to auth.py config)

### authorize google apis
- api manager
  - enable api
    - gmail api
    - contacts api
    - sheets api
    - drive api
    - enable (and wait a few mins)


### creds
The client_secret.json file downloaded from the [Google Cloud Platform](### register google application) is used to call up a browser-based google account login page, where the user authorizes access to the requested APIs and generates a credentials.dat file for download. Keep this file in the `foiamail/auth` directory. 

### auth
The `auth` module works behind the scenes in every other FOIAMail module. The wrapper functions, `get_service()` and 'get_gd_client()`, are called by Contacts, GMail, Drive and Sheets APIs to authenticate requests.  

The auth module depends on the credentials.dat file to verify requests. 

# import/update contacts
The `contacts` module function, `load_contacts()`, takes a specified csv file of contacts (with field headers 'first name','last name','agency' and 'email') and loads them into the user's Google Contacts.  

These contacts are later accessed by GMail when generating FOIA requests.  

Verify contacts are loaded via the [GMail Contacts screen](https://mail.google.com/mail/u/0/#contacts)

# compose/send messages
Once contacts are loaded, FOIAs messages may be drafted and sent using the `msg` module.

## import template
A FOIA template should be saved to the `foiamail/msg` directory in .docx format and referenced in the configuration section of `compose.py`.  

This template file will be imported when drafting FOIA messages.


## create drafts
The FOIAMail application creates one draft for each agency. These drafts are based off the above-referenced template and are identical with the following exceptions:
- Each draft's `To:` field includes all email contacts on file under its agency's name.
- Each draft's `Body` field is appended with the agency's unique slug. (Whitespace-stripped, title-cased, and appended/prepended by hashtags `#`, as defined in `mgs.utils`. e.g.: `#ArlingtonHeights#`)

To create drafts, call the `distribute()` function in the `msg.compose` module. Leaving the keyword argument `drafts` to the default empty list, which prompts for preparation of new drafts for each agency.  


## send
To send, call `msg.compose` module's `distribute()` function with `send=True`.

\# See issue \#4 

# label incoming
## agency
## status


# file attachments
## read emails
## write to drive


# report statuses
## look up agency status
## write to sheet


# log things
## types of logging (verify they work)


# management
## mgr
## cron


# misc
