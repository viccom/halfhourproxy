#!/bin/bash

[ $(id -u) != "0" ] && { echo "${CFAILURE}Error: You must be root to run this script${CEND}"; exit 1; }

cd /usr/local/microservice && pip3 install virtualenv && virtualenv venv && source venv/bin/activate
/usr/local/microservice/venv/bin/pip3 install -r requirements.txt
/usr/local/microservice/venv/bin/python3 /usr/local/microservice/main.py

