FILENAME=*.txt
if find . -type f -empty -name "${FILENAME}"; then
    echo "File is empty"
else
    echo "File is not empty"
fi
