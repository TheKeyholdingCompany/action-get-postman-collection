#!/bin/sh -l

python3 /fetch-postman-collection.py "$1" "$2" "$3" "$4"

echo "Github output:"
echo "${GITHUB_OUTPUT}"

