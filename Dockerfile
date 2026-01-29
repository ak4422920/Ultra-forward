# Python 3.8 use kar rahe hain jaisa aapne kaha
FROM python:3.8-slim-buster

# System updates aur Git installation
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y git && \
    rm -rf /var/lib/apt/lists/*

# Requirements install karna
COPY requirements.txt /requirements.txt
RUN pip3 install -U pip && pip3 install -U -r /requirements.txt

# Bot ka folder banana
RUN mkdir /fwdbot
WORKDIR /fwdbot

# Sabse Zaroori: Saari files ko container ke andar copy karna
COPY . .

# Start script ko permission dena aur chalana
RUN chmod +x start.sh
CMD ["/bin/bash", "start.sh"]
