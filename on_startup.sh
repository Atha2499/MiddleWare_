#!/bin/bash

# Set static IP for ethernet 0
sudo /usr/sbin/ip addr flush dev ethernet0
sudo /usr/sbin/ip  addr add 192.168.2.34/24 dev ethernet0

sudo python3 /home/torizon/MiddleWare/latest_05032025/app.py

