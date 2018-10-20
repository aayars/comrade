# stream_media.py but it's a Mastodon client

import click
import json
import mimetypes
import os
import random
import subprocess
import time

from mastodon import Mastodon
from mastodon.streaming import StreamListener

import requests


def are_replies_okay(content):
    """ Return True if the content contains the magic terms "REPLIES_OK" or "REPLY_OK" """

    return "REPLIES_OK" in content or "REPLY_OK" in content


def strip_toot(content):
    """ Strip a toot bare of all but its core essence """

    stripped = re.sub(r'<span.*?>.*</span>', "", content)
    stripped = re.sub(r'<p>', "", stripped)
    stripped = re.sub(r'</p>', "\n\n", stripped)
    stripped = re.sub(r'<br.*?>', "\n", stripped)

    stripped = html.unescape(stripped)

    return stripped


@click.command()
@click.option("--config", type=click.Path(dir_okay=False), required=True)
@click.option("--callback", type=str, required=True)
@click.option("--exclude-user", type=str)
@click.option("--testing", is_flag=True, default=False)
def main(config, callback, exclude_user=None, testing=False):
    client = None

    class Streamer(StreamListener):
        def on_update(self, status):
            media_url = self._media_url_from_status(status, are_replies_okay(status.get("content")))

            user = status.get("account", {}).get("acct")
            visibility = status.get("visibility", "public")
            sensitive = status.get("sensitive", False)

            return self._handle_media(user, media_url, status_id, visibility, sensitive, config, callback, testing)

        def on_notification(self, notif):
            user = notif.get("account", {}).get("acct")

            # To avoid death loops with other bots, ignore reply toots unless overridden.
            replies_ok = False

            if notif.get("type") == "mention":
                orig_status = notif.get("status", {})

                status = orig_status
                status_id = status.get("id")

                media_url = self._media_url_from_status(status, are_replies_okay(status.get("content")))

                if not media_url:
                    status_id = status.get("in_reply_to_id")

                    if status_id:
                        status = client.status(status_id)

                    media_url = self._media_url_from_status(status, are_replies_okay(orig_status.get("content")))

                visibility = status.get("visibility", "public")
                sensitive = status.get("sensitive", False)

            elif notif.get("type") == "follow":
                status = None

                media_url = notif.get("account", {}).get("avatar_static")
                status_id = ""
                visibility = "direct"
                sensitive = False

            elif notif.get("type") != "favourite":
                status = notif.get("status", {})

                media_url = self._media_url_from_status(status, are_replies_okay(status.get("content")))
                status_id = status.get("id")
                visibility = status.get("visibility", "public")
                sensitive = status.get("sensitive", False)

            if not media_url:
                return

            return self._handle_media(user, media_url, status_id, visibility, sensitive, config, callback, testing)

        def _media_url_from_status(self, status, replies_ok=False):
            if status.get("reblog"):
                return

            if not replies_ok and status.get("in_reply_to_id"):
                return

            media = status.get("media_attachments", [])

            if not media:
                return

            return media[0].get("url")

        def _handle_media(self, user, media_url, status_id, visibility, sensitive, config, callback, testing):
            if exclude_user == user:
                return

            r = requests.get(media_url, stream=True)

            content_type = r.headers['content-type']

            extension = mimetypes.guess_extension(content_type, strict=False)

            if extension.startswith(".jp"):
                extension = ".jpg"  # sigh

            filename = "{0}{1}".format(random.randint(1, 1000000), extension)

            # https://stackoverflow.com/questions/16694907/how-to-download-large-file-in-python-with-requests-py
            with open(filename, 'wb') as fh:
                for chunk in r.iter_content(chunk_size=1024): 
                    if chunk:
                        fh.write(chunk)

            """
            Process toot
            effect_name=`artmangler random {filename}` && post-media --config {config} --image mangled.png --status "{user} vs. $effect_name" --in-reply-to {id}
            """
            sensitive_flag = '--sensitive' if sensitive else ''

            command = callback.format(filename=filename, config=config, user=user, id=status_id, visibility=visibility, sensitive=sensitive_flag)

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

            client.stream_user(Streamer())

        except Exception:
            time.sleep(10)
