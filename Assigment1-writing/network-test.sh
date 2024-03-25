#!/bin/bash

if [ ! -f network-test-machinelist.txt ]; then
  echo "File network-test-machinelist.txt not found!"
  exit 1
fi

: > network-test-latency.txt

while IFS= read -r address; do
  if [ -z "$address" ]; then
    continue
  fi

  rtt=$(ping -c 3 "$address" | tail -1 | awk '{print $4}' | cut -d '/' -f 2)
  
  if [ -n "$rtt" ]; then
    echo "$address $rtt" >> network-test-latency.txt
  else
    echo "$address -" >> network-test-latency.txt
  fi

done < network-test-machinelist.txt

