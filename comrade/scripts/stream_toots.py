# stream_media.py but it's a Mastodon client

import click
import json
import mimetypes
import os
import subprocess
import time

from mastodon import Mastodon
from mastodon.streaming import StreamListener

import requests


@click.command()
@click.option("--config", type=click.Path(dir_okay=False), required=True)
@click.option("--callback", type=str, required=True)
@click.option("--exclude-user", type=str)
@click.option("--testing", is_flag=True, default=False)
@click.option("--hashtag", type=str)
def main(config, callback, exclude_user=None, testing=False):
    class Streamer(StreamListener):
        def on_notification(self, notif):
            user = notif.get("account", {}).get("acct")

            if exclude_user and exclude_user == user:
                return

            if notif.get("type") == "follow":
                media_url = notif.get("account", {}).get("avatar_static")
                status_id = None

            else:
                data = notif.get("status", {})

                if data.get("sensitive"):
                    return

                if data.get("reblog"):
                    return

                if data.get("in_reply_to_id"):
                    return

                media = data.get("media_attachments", [])

                if not media:
                    return

                media_url = media[0].get("url")
                status_id = data.get("id")

            if not media_url:
                return
            
            r = requests.get(media_url, stream=True)

            content_type = r.headers['content-type']

            extension = mimetypes.guess_extension(content_type, strict=False)

            if extension.startswith(".jp"):
                extension = ".jpg"  # sigh

            filename = "$RANDOM{0}".format(extension)

            # https://stackoverflow.com/questions/16694907/how-to-download-large-file-in-python-with-requests-py
            with open(filename, 'wb') as fh:
                for chunk in r.iter_content(chunk_size=1024): 
                    if chunk:
                        fh.write(chunk)

            """
            Process toot
            effect_name=`artmangler random {filename}` && post-media --config {config} --image mangled.png --status "{user} vs. $effect_name" --in-reply-to {id}
            """
            command = callback.format(filename=filename, config=config, user=user, id=status_id)

            if testing:
                print(command)

            else:
                subprocess.call(command, shell=True)

            os.remove(filename)

            # print(json.dumps(data, indent=4))

        def on_abort(self, status_code, data):
            print(status_code)

    cfg = json.load(open(config))

    while(True):
        try:
            client = Mastodon(
                access_token = cfg["mastodon_token"],
                api_base_url = cfg["mastodon_instance"],
            )

            if hashtag:
                client.stream_hashtag(hashtag, Streamer())

            else:
                client.stream_user(Streamer())

        except Exception:
            time.sleep(10)
