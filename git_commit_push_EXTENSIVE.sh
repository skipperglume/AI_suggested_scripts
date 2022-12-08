#!/bin/bash

# Set the commit message
MESSAGE="This is the commit message"  # The commit message is like the headline of a news article, so make it catchy!

# Set the branch to push to
BRANCH="master"  # We're pushing to the master branch, because we're the masters of our Git repos!

# Check if the working directory is clean
if ! git diff-index --quiet HEAD; then  # Let's see if our working directory is as clean as a baby's bottom...
  # If there are changes, stage them for commit
  git add .  # Looks like we have some dirty diapers here! Let's stage them for commit so we can clean things up.
fi

# Create the commit
git commit -m "$MESSAGE"  # Time to take a snapshot of our code and save it to the Git history books!

# Check if the local branch is ahead of the remote branch
if ! git rev-parse "$BRANCH" >/dev/null 2>&1; then  # Is our local branch ahead of the remote branch, or are we lagging behind?
  # If the local branch does not exist, create it
  git checkout -b "$BRANCH"  # It looks like our local branch doesn't exist yet! No worries, we'll just create it now.
fi

# Push the commit to the remote branch
git push origin "$BRANCH"  # All done! Time to push our commit to the remote branch and share it with the world.
