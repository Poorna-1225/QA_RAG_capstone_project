import math
import os
import json
import asyncio
import httpx
import time
import shutil
from datetime import datetime

POSTS_PER_PAGE = 25  # using 100 can cause HTML response to be too long so that the text gets terminated
MAX_PAGE = 8  # setting to 8 so that we get 200 pages total. Increase to download more articles

def download(session, headers, wp, data_dir):
    current_page = 1
    download_complete = False
    now = datetime.now()
    start_timecode = f"{now.year}{now.month}{now.day}{now.hour}{now.minute}{now.second}"
    padding_width = math.ceil(math.log(MAX_PAGE, 10))

    print(f"Downloading up to {MAX_PAGE * POSTS_PER_PAGE} posts...")
    while (not download_complete) and (
        current_page <= MAX_PAGE
    ):  # <= because pages are 1-indexed
        response = session.get(
            f"https://{wp}/wp-json/wp/v2/posts?page={current_page}&per_page={POSTS_PER_PAGE}",
            headers=headers,
        )
        if response.status_code == 200:
            response_json = response.json()
            with open(
                os.path.join(
                    data_dir,
                    f"{start_timecode}_{str(current_page).zfill(padding_width)}.json",
                ),
                "w",
            ) as dump_file:
                json.dump(response_json, dump_file)

            print(f"Page {current_page}. Downloaded {len(response_json)} posts")

            if len(response_json) < POSTS_PER_PAGE:
                download_complete = True
                print(
                    f"Downloaded all ({POSTS_PER_PAGE * (current_page - 1) + len(response_json)} posts)"
                )
            else:
                current_page += 1

        else:
            print(
                f"Download of page {current_page} failed with status code {response.status_code}. {response.text}"
            )
            download_complete = True

data_dir = os.path.join(os.getcwd(), 'data', 'techblogs')

# Uncomment these lines below if you wanted to redownload
shutil.rmtree(data_dir)
os.makedirs(data_dir, exist_ok=True)
download(
     session=httpx.Client(),
     headers={
         "user-agent": "Mozilla/5.0 (X11; Linux i686; rv:10.0) Gecko/20100101 Firefox/10.0",
         "Accept-Encoding": "gzip, deflate, br",
    },
     wp="developer.nvidia.com/blog",
     data_dir=data_dir,
 )

file_list = [x for x in sorted(os.listdir(data_dir)) if '.json' in x]

techblogs_dict = {}

for i, filename in enumerate(file_list):
    with open(os.path.join(data_dir, filename), 'r') as in_file:
        data = json.load(in_file)
    for item in data:
        # skip items that do not link to developer.nvidia.com/blog or blogs.nvidia.com
        if not item['link'].startswith("https://developer.nvidia.com/blog"): # and not item['link'].startswith("https://blogs.nvidia.com"):
            continue
        document_title = item['title']['rendered']
        document_url = item['link']
        document_html = item['content']['rendered']
        document_date = item['date_gmt']
        document_date_modified = item['modified_gmt']

        techblogs_dict[document_url] = item
