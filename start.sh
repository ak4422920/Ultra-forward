#!/bin/bash

# Web Server (Flask/Gunicorn) ko background mein start karna
# Isse Koyeb/VPS ko 'Healthy' signal milta rahega
gunicorn app:app & 

# Main Bot process ko start karna
# Ye main process hai, isliye ise background (&) mein nahi daalna hai
python3 bot.py
