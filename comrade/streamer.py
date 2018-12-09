import mimetypes
import os
import random
import re
import subprocess

from mastodon.streaming import StreamListener

import requests


def are_bots_okay(account):
    """ Return True unless this user's profile contains #nobot """

    return '#nobot' not in account.get('note', '')


def are_replies_okay(status, client):
    """ Return True if the discussion thread is still pretty short. """

    if status.get("reblog"):
        return

    for i in range(6):
        if not status.get("in_reply_to_id"):
            return True

        if i in (0, 1) and not are_bots_okay(status.get('account', {})):  # Check orig post and parent for #nobot
            return False

        status = client.status(status.get("in_reply_to_id"))

    # Already enough responses in a thread
    return False


def media_url_from_status(status, client):
    """ Check the given status (or its parent) for a media attachment, and return the url or None. """

    media = status.get("media_attachments", [])

    if not media and status.get("in_reply_to_id"):
        status = client.status(status.get("in_reply_to_id"))

        media = status.get("media_attachments", [])

    return media[0].get("url") if media else None


def download_media(media_url):
    """ Saves the given media url, and returns the filename. """

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

    return filename


def strip_toot(content):
    """ Strip a toot bare of all but its core essence """

    stripped = re.sub(r'<span.*?>.*</span>', "", content)
    stripped = re.sub(r'<p>', "", stripped)
    stripped = re.sub(r'</p>', "\n\n", stripped)
    stripped = re.sub(r'<br.*?>', "\n", stripped)

    stripped = stripped.unescape(stripped)

    return stripped


class Streamer(StreamListener):
    def __init__(self, config, callback, exclude_user, **kwargs):
        self.__init__(**kwargs)

        self.callback = callback
        self.config = config
        self.exclude_user = exclude_user

    def on_update(self, status):
        account = status.get("account")

        if not are_bots_okay(account):
            return

        media_url = media_url_from_status(status, self.client)

        user = account.get("acct")
        visibility = status.get("visibility", "public")
        sensitive = status.get("sensitive", False)

        return self._respond(user, media_url, status, visibility, sensitive)

    def on_notification(self, notif):
        account = notif.get("account", {})

        if not are_bots_okay(account):
            return

        user = account.get("acct")

        if notif.get("type") == "mention":
            orig_status = notif.get("status", {})

            status = orig_status

            media_url = media_url_from_status(status, self.client)

            visibility = status.get("visibility", "public")
            sensitive = status.get("sensitive", False)

        elif notif.get("type") == "follow":
            status = None

            media_url = account.get("avatar_static")

            visibility = "direct"
            sensitive = False

        elif notif.get("type") != "favourite":
            status = notif.get("status", {})

            media_url = media_url_from_status(status, self.client)
            visibility = status.get("visibility", "public")
            sensitive = status.get("sensitive", False)

        if not media_url:
            return

        return self._respond(user, media_url, status, visibility, sensitive)

    def _respond(self, user, media_url, status, visibility, sensitive):
        if self.exclude_user == user:
            return

        if not are_replies_okay(status, self.client):
            return

        filename = download_media(media_url) if media_url else None

        """
        Process toot
        effect_name=`artmangler random {filename}` && post-media --config {config} --image mangled.png --status "{user} vs. $effect_name" --in-reply-to {id}
        """
        status_id = status.get('id') if status else None

        try:
            if callable(self.callback):
                self.callback(
                    filename=filename,
                    config=self.config,
                    user=user,
                    id=status_id,
                    visibility=visibility,
                    sensitive=sensitive
                )

            else:
                command = self.callback.format(
                    filename=filename,
                    config=self.config,
                    user=user,
                    id=status_id,
                    visibility=visibility,
                    sensitive='--sensitive' if sensitive else '',
                    content=strip_toot(status.get('content', ''))
                )

                subprocess.call(command, shell=True)

        except Exception as e:
            print(str(e))

        os.remove(filename)

    def on_abort(self, status_code, data):
        print(status_code)
