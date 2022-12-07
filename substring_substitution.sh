if [ $# -ne 3 ]; then
  echo "Usage: substitute <filename> <old_string> <new_string>"
  exit 1
fi

# Store the filename, old string, and new string in variables for convenience
filename=$1
old_string=$2
new_string=$3

# Read each line in the file and substitute the old string with the new string
while read -r line; do
  echo "${line//$old_string/$new_string}"
done < "$filename"

# ./substitute.sh file.txt fox cat > new_file.txt