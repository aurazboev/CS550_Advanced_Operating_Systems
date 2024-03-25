#!/bin/bash

time (
	echo "DD Benchmark"
	echo "Write benchmark running..."
	dd if=/dev/zero of=testfile bs=15M count=1024 oflag=dsync
	echo "Write benchmark completed."
	    
	echo "Read benchmark running..."
	dd if=testfile of=/dev/null bs=15M
	echo "Read benchmark completed."
    
	rm testfile
) &> disk-benchmark-background-log.txt &

disown
