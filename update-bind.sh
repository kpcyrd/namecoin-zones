#!/bin/sh
cd /opt/namecoin-zones/
./namecoin-zones.py config.yml > /etc/bind/db.namecoin.bit
service bind9 reload
