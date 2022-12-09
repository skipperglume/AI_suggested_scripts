#!/bin/bash

# Prompt user for the string to be replaced
echo "Enter the string you want to replace: "
read old_str

# Prompt user for the replacement string
echo "Enter the replacement string: "
read new_str

# Prompt user for the file name
echo "Enter the file name: "
read file

# Use sed to replace all occurrences of the string
# and save the output to a new file
sed "s/$old_str/$new_str/g" $file > new_file

# Delete the original file
rm $file

# Rename the new file to the original file name
mv new_file $file
