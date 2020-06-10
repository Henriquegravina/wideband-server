#!/bin/bash

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

PATH=$PATH:$(pwd)
cd /run/user/$UID

DEVICE=0
DS=0

for i in "$@"
do
case $i in
    -p=*|--ppm=*)
    PPM="${i#*=}"
    shift # past argument=value
    ;;
    -d=*)
    DEVICE="${i#*=}"
    shift # past argument=value
    ;;
    -q=*|--qrg=*)
    QRG="${i#*=}"
    shift # past argument=value
    ;;
    -l=*|--lo=*)
    LO="${i#*=}"
    shift # past argument=value
    ;;
    -ds=*)
    DS="${i#*=}"
    shift # past argument=value
    ;;
    -sr=*)
    SPS="${i#*=}"
    shift # past argument=value
    ;;
    -dc=*)
    DECIMATION="${i#*=}"
    shift # past argument=value
    ;;
    -sg=*)
    SEND_GROUP="${i#*=}"
    shift # past argument=value
    ;;
    -sp=*)
    SEND_PORT="${i#*=}"
    shift # past argument=value
    ;;
    --default)
    PPM=0
    QRG=3568600
    LO=3580000
    SPS=2400000
    shift # past argument with no value
    ;;
    *)
          # unknown option
    ;;
esac
done
echo "PPM  = ${PPM}"
echo "QRG  = ${QRG}"
echo "LO   = ${LO}"
echo "Sample Rate = ${SPS}"
echo "Decimation  = ${DECIMATION}"
echo "Send Group  = ${SEND_GROUP}"
echo "SEnd Port   = ${SEND_PORT}"
echo "DEVICE   = ${DEVICE}"



if [[ -n $1 ]]; then
    echo "Last line of file specified as non-opt/last argument:"
    tail -1 $1
fi


SHIFT=`python -c "print float($LO-$QRG) / $SPS"`

rtl_sdr -d $DEVICE -p $PPM -D $DS -s $SPS -f $LO - | \
csdr convert_u8_f | \
csdr shift_addition_cc $SHIFT | \
csdr fir_decimate_cc $DECIMATION 0.005 HAMMING | \
#csdr bandpass_fir_fft_cc 0 1 0.02 | \
#csdr realpart_cf | \
#csdr convert_f_s16 | \
msend $SEND_GROUP $SEND_PORT 1