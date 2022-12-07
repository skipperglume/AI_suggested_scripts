echo "Enter the name of the file: "
read filename

# Prompt the user for the old substring
echo "Enter the old substring: "
read oldsubstring

# Prompt the user for the new substring
echo "Enter the new substring: "
read newsubstring

# Substitute the old substring with the new one in the file
# and save the result to a new file
sed "s/${oldsubstring}/${newsubstring}/g" "${filename}" > "${filename}_new"

# Print a success message
echo "Substitution complete. The new file is named ${filename}_new"