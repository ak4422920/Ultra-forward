# Python 3.9 use kar rahe hain (3.8 se zyada stable aur fast hai async ke liye)
FROM python:3.9-slim-buster

# System updates aur zaroori libraries install karna
# ffmpeg aur libsm6 media processing/thumbnails ke liye zaroori hain
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y git ffmpeg libsm6 libxext6 gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Bot ka folder banana
WORKDIR /fwdbot

# Sabse pehle requirements copy karke install karna (Layer Caching ke liye)
COPY requirements.txt .
RUN pip3 install -U pip && pip3 install --no-cache-dir -U -r requirements.txt

# Baaki saari files copy karna
COPY . .

# Start script ko execution permission dena
RUN chmod +x start.sh

# Bot ko start karna
CMD ["/bin/bash", "start.sh"]
