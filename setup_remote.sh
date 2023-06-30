#!/bin/bash

if [ $# -ne 3 ]; then
    echo "Usage: $0 ../substrate <remote_name> <remote_url>"
    exit 1
fi

# Move to project dir
cd $1
remote_name=$2
remote_url=$3

parity_set=$(git remote get-url $remote_name)
if [ $? -ne 0 ]; then
	echo "Creating $remote_name remote"
	git remote add $remote_name $remote_url
elif [[ $parity_set == $remote_url ]]; then
	echo "$remote_name remote exists"
else
	echo "$parity_set"
	echo "Updating $remote_name remote to $remote_url"
	git remote set-url $remote_name $remote_url
fi

#git fetch $remote_name
