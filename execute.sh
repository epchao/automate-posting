#!/bin/bash
RELATIVE_DIRECTORY="/home/epchao/Development/Projects/automate-posting"
FILE="$1"
SCRIPT_PATH="$RELATIVE_DIRECTORY/main.py"
FILE_PATH="$RELATIVE_DIRECTORY$FILE"
XVFB_DISPLAY=:99

if [[ -z "$FILE_PATH" ]]; then
    echo "Error: No file provided."
    exit 1
fi

if [[ -s "$FILE_PATH" ]]; then
    cd $RELATIVE_DIRECTORY
    echo "Running script with Xvfb."
    Xvfb $XVFB_DISPLAY -screen 0 1280x1024x16 &
    XVFB_PID=$!
    export DISPLAY=$XVFB_DISPLAY
    source "$RELATIVE_DIRECTORY/.venv/bin/activate"
    python3 "$SCRIPT_PATH" "$FILE_PATH" >> "$RELATIVE_DIRECTORY/out.txt"
    kill $XVFB_PID
else
    # TODO: remove job
    # TODO: fix requirements.txt with correct packages
    echo "$RELATIVE_DIRECTORY/$FILE is empty. Removing job."
    crontab -l | grep -v "$0" | crontab -
fi
