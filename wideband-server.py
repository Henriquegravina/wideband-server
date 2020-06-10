
#!/usr/bin/env python

#
# RTL_SDR multicast server for Hamradio
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
import getopt
import json
import time
import subprocess

band_data = {
    '3': {'qrg_l': 10489540000,'qrg_h': 10489570000,'qrg_offset':-9750000000,'direct_sampling':0, 'samples':2400000 , 'decimation':50, 'public_port':15003, 'public_group':"239.0.0.3" }, 
    '160':  {'qrg_l':1830000,  'qrg_h': 1870000,'qrg_offset':0,  'direct_sampling':2, 'samples':2400000 , 'decimation':50, 'public_port':150160, 'public_group':"239.0.0.160" },
    '80':  {'qrg_l': 3560000,  'qrg_h': 3585000,'qrg_offset':0,  'direct_sampling':2, 'samples':2400000 , 'decimation':50, 'public_port':15080, 'public_group':"239.0.0.80" },
    '40':  {'qrg_l': 7070000,  'qrg_h': 7085000,'qrg_offset':0,  'direct_sampling':2, 'samples':2400000 , 'decimation':50, 'public_port':15040, 'public_group':"239.0.0.40" }, 
    '15':  {'qrg_l': 21074000,  'qrg_h': 21090000,'qrg_offset':0,  'direct_sampling':2, 'samples':2400000 , 'decimation':50, 'public_port':15015, 'public_group':"239.0.0.15" }  
}

rtl_device = 0

try:
    opts, args = getopt.getopt(sys.argv[1:],"hg:p:b:d:")
except getopt.GetoptError:
    print 'wideband-server -b band'
    sys.exit(2)
for opt, arg in opts:
    if opt == "-h":
        print 'wideband-server -b band'
        sys.exit(2)
  #  elif opt == "-g":
  #      public_group = arg
    elif opt == "-d":
        rtl_device = arg
    elif opt == "-b":
        r_band = arg


public_port = band_data[r_band]['public_port']
public_group = band_data[r_band]['public_group']
qrg_l = band_data[r_band]['qrg_l']
qrg_h = band_data[r_band]['qrg_h']
decimation = band_data[r_band]['decimation']
samples = band_data[r_band]['samples']
direct_sampling = band_data[r_band]['direct_sampling']
qrg_offset = band_data[r_band]['qrg_offset']


print "Staring server on group:"+public_group+":"+str(public_port)+" with band:"+r_band

# Group 239.0.0.10 Port 15000 for server advertise
multicast_group = ("239.0.0.10",15000)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(0.2) # to not block socket on receive

# Set the time-to-live for messages to 1 so they do not go past the LAN
ttl = struct.pack('b', 1)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)


# Run rtl and csdr from an bash to be a simple PID
cmd_receiver = ["./wideband-receiver.sh -p=0 -q="+str(qrg_l + qrg_offset)+" -l="+str(qrg_h + qrg_offset)+" -sg="+public_group+" -sp="+str(public_port)+" -sr="+str(samples)+" -dc="+str(decimation)+" -d="+str(rtl_device)+" -ds="+str(direct_sampling)] 
print cmd_receiver
receiver = subprocess.Popen(cmd_receiver, shell=True, stdin=None, stdout=subprocess.PIPE,stderr=None)

# Json information to clients
message = json.dumps( {'type': 'BAND.DATA',
                       'params': {'name':r_band ,
                                 'qrg_l':qrg_l,
                                 'qrg_h':qrg_h,
                                 'qrg_offset':qrg_offset,
                                 'samples':samples,
                                 'decimation':decimation,
                                 'multicast_group':public_group,
                                 'multicast_port':public_port,
                                 'rtl_sdr-pid': receiver.pid }
                                 }
)


try:
    # Send receiver information to the multicast group
    while True:
        #print >>sys.stderr, 'sending "%s"' % message
        sent = sock.sendto(message, multicast_group)
        time.sleep(1)
    
finally:
    print >>sys.stderr, 'closing socket'
    receiver.kill()
    sock.close()
