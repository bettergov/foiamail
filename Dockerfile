FROM python:3.7.4-slim-buster AS deps

# Install the Python deps (common across worker & web server, for now)
RUN mkdir -p /home/ubuntu/foiamail
WORKDIR /home/ubuntu/foiamail

# Timezone setup (else defaults to UTC)
RUN mv /etc/localtime /etc/localtime.bk
RUN cp /usr/share/zoneinfo/America/Chicago /etc/localtime

# Git for py3 deps
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        build-essential python3-dev python3-setuptools python3-wheel python3-cffi \
        libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev \
        shared-mime-info \
        rsyslog \
        logrotate \
        cron \
        tree \
        git \
    && rm -rf /var/lib/apt/lists/*

## os requirements
RUN mv /etc/localtime /etc/localtime.bk
RUN cp /usr/share/zoneinfo/America/Chicago /etc/localtime
# Use the following to reset to UTC
RUN dpkg-reconfigure --frontend noninteractive tzdata

RUN apt install -y

COPY . /home/ubuntu/foiamail
RUN cat crontab >> /etc/crontab

RUN pip install -r /home/ubuntu/foiamail/requirements.txt
RUN pip install -r /home/ubuntu/foiamail/requirements.py3.txt

FROM deps as base

# persist logs across docker runs
VOLUME /home/ubuntu/foiamail/log/logs

# fake a virtualenv so we don't have to maintain a separate cron
RUN mkdir /home/ubuntu/foiamail/bin
RUN touch /home/ubuntu/foiamail/bin/activate

CMD cron -f -L 15
