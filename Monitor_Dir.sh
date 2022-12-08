#!/bin/bash

# This script monitors a system for changes and logs the activity.

# Set the directory to monitor.
MONITOR_DIR="../MCJES_UFO"

# Set the log file.
LOG_FILE="file.log"

# Check if the log file exists. If not, create it.
if [ ! -f "$LOG_FILE" ]; then
    touch "$LOG_FILE"
fi

# Set the initial state of the directory.
INITIAL_STATE=$(ls -l "$MONITOR_DIR")

while true; do
    # Check the current state of the directory.
    CURRENT_STATE=$(ls -l "$MONITOR_DIR")

    # Compare the current state with the initial state.
    if [ "$INITIAL_STATE" != "$CURRENT_STATE" ]; then
        # If the states are different, log the time and the changes.
        echo "$(date): Changes detected in $MONITOR_DIR" >> "$LOG_FILE"
        echo "---" >> "$LOG_FILE"
        echo "$CURRENT_STATE" >> "$LOG_FILE"
        echo "---" >> "$LOG_FILE"
        echo >> "$LOG_FILE"

        # Update the initial state to the current state.
        INITIAL_STATE="$CURRENT_STATE"
    fi

    # Sleep for 1 second before checking the state again.
    sleep 1
done
