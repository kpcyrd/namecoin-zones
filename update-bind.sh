#!/bin/sh
cd /opt/namecoin-zones/
./namecoin-zones > /etc/bind/db.namecoin.bit
service bind9 reload
