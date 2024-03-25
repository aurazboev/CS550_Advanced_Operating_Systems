#!/bin/bash

# Define the temporary file and the log files for stdout and stderr
TEMP_FILE="tempfile.img"
STDOUT_LOG="stdout.log"
STDERR_LOG="stderr.log"

# Create a function to clean up the temporary file
cleanup() {
  if [[ -f $TEMP_FILE ]]; then
    rm $TEMP_FILE
  fi
}

# Register the cleanup function to run when the script exits
trap cleanup EXIT

# Benchmark write speed
echo "Benchmarking write speed..." | tee -a $STDOUT_LOG
{ dd if=/dev/zero of=$TEMP_FILE bs=1M count=1024 conv=fdatasync 2>&1 1>&3 | tee -a $STDERR_LOG; } 3>&1 1>&2 | tee -a $STDOUT_LOG

# Clean up the tempfile before reading (to clear caches)
sync
echo 3 | sudo tee /proc/sys/vm/drop_caches

# Benchmark read speed
echo "Benchmarking read speed..." | tee -a $STDOUT_LOG
{ dd if=$TEMP_FILE of=/dev/null bs=1M count=1024 2>&1 1>&3 | tee -a $STDERR_LOG; } 3>&1 1>&2 | tee -a $STDOUT_LOG

# Output the results
echo "Benchmark results:"
echo "STDOUT:"
cat $STDOUT_LOG

echo "STDERR:"
cat $STDERR_LOG

# The temporary file will be removed by the cleanup function
