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

RUN pip install -r /home/ubuntu/foiamail/requirements.txt
RUN pip install -r /home/ubuntu/foiamail/requirements.py3.txt

FROM deps as base

RUN echo "*/15 7-19 * * * cd /home/ubuntu/foiamail && python /home/ubuntu/foiamail/mgr.py --label | tee -a /home/ubuntu/foiamail/log/logs/cron-label" >> /etc/crontab
RUN echo "0 0 * * * cd /home/ubuntu/foiamail && python mgr.py --atts | tee -a /home/ubuntu/foiamail/log/logs/cron-atts" >> /etc/crontab
RUN echo "0 5 * * * cd /home/ubuntu/foiamail && python mgr.py --report | tee -a /home/ubuntu/foiamail/log/logs/cron-report" >> /etc/crontab

RUN touch /home/ubuntu/foiamail/log/logs/cron-atts
RUN touch /home/ubuntu/foiamail/log/logs/cron-label
RUN touch /home/ubuntu/foiamail/log/logs/cron-report

CMD cron -f -L 8
