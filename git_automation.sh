#!/bin/bash

while true; do
  # Add all files in the current directory to the Git index
  git add .

  # Commit the files with a message
  git commit -m "Periodic commit"

  # Push the changes to the remote repository
  git push

  # Sleep for 5 minutes before committing and pushing again
  sleep 30
done
