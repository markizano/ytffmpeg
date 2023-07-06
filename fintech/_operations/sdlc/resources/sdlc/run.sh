#!/bin/bash

set -e

wid_present=0x0c28f526
wid_console=0x01c03042

screenshot() { import +repage -screen -window "$wid_present" "$1"; }

wmctrl -i -a $wid_present
sleep 2
while read png; do
  screenshot "$png"
  xte 'key Right'
  sleep 1
done < c

wmctrl -i -a $wid_console



