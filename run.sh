#!/bin/bash

# Start the first process
python3 asr_app.py &
  
# Start the second process
celery -A tasks:celery_app worker --loglevel=info &
  
# Wait for any process to exit
wait -n
  
# Exit with status of process that exited first
exit $?
