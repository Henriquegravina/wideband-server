#!/usr/bin/env python

#
# SDR Multicast client with FT8 decode for Hamradio
#
#
# Author: Henrique Brancher Gravina, PU3IKE
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License 2 as published by
# the Free Software Foundation
#
#

import socket
import struct
import sys
import os
import getopt
import json
import subprocess
import time
import re

band_name = "40"
ft8_qrg = 7074000

try:
    opts, args = getopt.getopt(sys.argv[1:],"hg:p:b:d:f:")
except getopt.GetoptError:
    print 'wideband-server -b band'
    sys.exit(2)
for opt, arg in opts:
    if opt == "-h":
        print 'wideband-client -b band -f qrg'
        sys.exit(2)
    elif opt == "-b":
        band_name = arg
    elif opt == "-f":
        ft8_qrg = int(arg)
        
ANY = "0.0.0.0" 
MCAST_ADDR = "239.0.0.10"
MCAST_PORT = 15000

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
sock.bind((ANY,MCAST_PORT))
status = sock.setsockopt(socket.IPPROTO_IP,
socket.IP_ADD_MEMBERSHIP,
socket.inet_aton(MCAST_ADDR) + socket.inet_aton(ANY))

while 1:
    try:
        data, addr = sock.recvfrom(1024)
    except socket.error as e:
        pass
    else:
        print "Looking for band receiver data"
        message = json.loads(data)
        if(message['type'] == 'BAND.DATA'):
            if(message['params']['name'] == band_name):
                print message
                sock.close()
                break

## Servidor multicas para os spots
multicast_group = ('239.0.0.10',14000)
spot_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
spot_sock.settimeout(0.2) # to not block socket on receive
# Set the time-to-live for messages to 1 so they do not go past the LAN
ttl = struct.pack('b', 1)
spot_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)



# Message example:
# sending "{"params": {"qrg_l": "3550000", "multicast_group": "239.0.0.81", "decimation": "50", "qrg_h": "3585000", "name": "80m", "samples": "2400000", "multicast_port": "15081", "rtl_sdr-pid": 11934}, "type": "BAND.DATA"}"

#${message['params']['multicast_group']}

# A porta para a bada todoa/ spectrum vai ser banda +1 +15000 ( por exemplo para banda de 80 metros: 15081)
# A porta para a parte de WSPR banda +2 +15000( por exemplo para banda de 80 metros: 15082)
# A porta para a parte de FT8 banda +3 +15000 ( por exemplo para banda de 80 metros: 15083)

spectrum_port = int(message['params']['name']) + 15000  + 3
spectrum_group = message['params']['multicast_group']
qrg_offset = message['params']['qrg_offset']

qrg_shift = ( ft8_qrg - float(message['params']['qrg_l']) ) / 48000

cmd_ft8_spectrum = "msend-wideband.sh -rg=" + message['params']['multicast_group'] + \
                                    " -rp=" + str(message['params']['multicast_port'])+ \
                                    " -og=" + spectrum_group + \
                                    " -op=" + str(spectrum_port) + \
                                    " -sh=" + str(qrg_shift) + \
                                    " -bw=0.1"
print cmd_ft8_spectrum
ft8_spectrum = subprocess.Popen(cmd_ft8_spectrum, shell=True, stdin=None, stdout=None,stderr=None)

cmd_wsskimmer = "mkdir /run/user/"+str(os.getuid())+"/"+ str(ft8_qrg)+" 2>/dev/null;" +\
                "cd /run/user/"+str(os.getuid())+"/"+ str(ft8_qrg)+";"+ \
                " wsskimmer -f "+ str(ft8_qrg)+" -c pu3ike -l gg40an" + \
                " -g "+ spectrum_group + \
                " -p "+ str(spectrum_port)
print cmd_wsskimmer
wsskimmer = subprocess.Popen(cmd_wsskimmer, shell=True, stdin=None, stdout=subprocess.PIPE,stderr=subprocess.PIPE)

regex = r'(^(?:(?P<word1>(?:CQ|DE|QRZ)(?:\s?DX|\s(?:[A-Z]{1,4}|\d{3}))|[A-Z0-9/]+|\.{3})\s)(?:(?P<word2>[A-Z0-9/]+)(?:\s(?P<word3>[-+A-Z0-9]+)(?:\s(?P<word4>(?:OOO|(?!RR73)[A-R]{2}[0-9]{2})))?)?)?)'


try:
       while True:
        ft8_decoded =  wsskimmer.stderr.readline().strip()
        print ft8_decoded
        decoded_msg = ft8_decoded.strip().split("~  ")
        print decoded_msg[1]

        matchObj = re.match( regex, decoded_msg[1], re.M|re.I)
        if matchObj:
            print "Escutei :", matchObj.group('word2')
            message = json.dumps( {'type': 'DX.SPOT','params': {'qrg':str(ft8_qrg) ,'dxcall':matchObj.group('word2') }})
            sent = spot_sock.sendto(message, multicast_group)

        
finally:
    print >>sys.stderr, 'Fechando...'
    spot_sock.close()
    ft8_spectrum.kill()
    wsskimmer.kill()

    

        
