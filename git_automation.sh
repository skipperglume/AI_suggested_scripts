#!/bin/bash

while true; do
  # Add all files in the current directory to the Git index
  echo "Start a new add->commit->push session"
  git add .

  # Commit the files with a message
  git commit -m "Periodic commit"

  # Push the changes to the remote repository
  git push

  # Sleep for 5 minutes before committing and pushing again
  echo "Finished"
  sleep 30
done
