#!/bin/bash

# Prompt user for the string to be removed
echo "Enter the string you want to remove: "
read str

# Prompt user for the file name
echo "Enter the file name: "
read file

# Use sed to remove all occurrences of the string
# and save the output to a new file
sed "/$str/d" $file > new_file

# Delete the original file
rm $file

# Rename the new file to the original file name
mv new_file $file
