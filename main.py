"""This script runs as a cron job.

It will be a daily workflow ran until the source text file is empty.
Once the text file is empty, the job will stop running for the assigned text file.

To execute this script, use ./execute.sh ./src/{entities_file_name}.txt
"""

#! /usr/bin/python3
import os

from sys import argv
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from instagrapi import Client

load_dotenv()

INSTAGRAM_USER = os.getenv('INSTAGRAM_USERNAME')
INSTAGRAM_PASSWORD = os.getenv('INSTAGRAM_PASSWORD')

os.environ["DISPLAY"] = ":99"

ENTRIES_FILE_PATH = argv[1]

IG_CLIENT = Client()
INSTAGRAM_SESSION_PATH = "./instagram_session.json"

with sync_playwright() as pw:
    # Establish a Chromium-based browser session.
    browser = pw.chromium.launch(headless=False)
    context = browser.new_context(
        record_video_dir='out/',
        record_video_size={'width': 1280, 'height': 720},
        viewport={'width': 1280, 'height': 720}
    )
    page = context.new_page()
    video_path = Path(page.video.path().replace('webm', 'mp4'))

    def route_interception(route):
        """
        Get rid of ads on the page.
        """
        if 'ads' in route.request.url:
            route.abort()
        else:
            route.continue_()

    page.route('**/*', route_interception)

    # Initially load the page and wait for the necessary elements to appear.
    page.goto('https://wheelofnames.com')
    wheel_canvas = page.locator('canvas')
    wheel_canvas.wait_for()

    # Fill the entries text area with the entries text file content.
    with open(ENTRIES_FILE_PATH, 'rt', encoding="utf-8") as efp:
        entries = efp.read()
    basic_editor = page.locator('div.basic-editor')
    basic_editor.wait_for()
    page.evaluate('text => document.querySelector(\'div.basic-editor\').innerText = text', entries)
    basic_editor.focus()
    page.keyboard.press('Enter')

    # Wheel of Names offers a keyboard shortcut (CTRL + ENTER) to spin the wheel.
    page.keyboard.press('Control+Enter')

    # Wait for the wheel to finish spinning and the winner to display on the page.
    winner_div = page.locator('div.q-dialog')
    winner_div.wait_for(timeout=30000, state='attached')
    winner_text = page.locator('span.winner-text')
    winner_text.wait_for(timeout=30000, state='attached')
    winner = winner_text.text_content()
    with open(ENTRIES_FILE_PATH, 'rt', encoding="utf-8") as efr:
        lines = efr.readlines()
        with open(ENTRIES_FILE_PATH, 'wt', encoding="utf-8") as efw:
            for line in lines:
                if line.strip('\n') != winner:
                    efw.write(line)

    # Add delay for a cleaner video and save the video as a .mp4 file.
    page.wait_for_timeout(5000)
    page.close()
    page.video.save_as(video_path)
    browser.close()

# Use instagram API library with the credentials in the environment variables and post the video.
try:
    IG_CLIENT.load_settings(INSTAGRAM_SESSION_PATH)
except FileNotFoundError:
    IG_CLIENT.login(INSTAGRAM_USER, INSTAGRAM_PASSWORD)
    IG_CLIENT.dump_settings(INSTAGRAM_SESSION_PATH)

IG_CLIENT.clip_upload(
    video_path,
    caption=f'{winner} has been elminated! #fyp #wheel #spinwheel #viral #troll'
)

# Clean up the output directory.
for file in video_path.parent.iterdir():
    file.unlink()
