import html
import json
import mimetypes
import os
import random
import re
import shutil
import subprocess
import time

from diskcache import Cache
from mastodon.streaming import StreamListener

import requests

COMRADE_CACHE = os.environ.get('COMRADE_CACHE', 'offline-cache')

SQUELCH_THRESHOLD = 4

SILENCE_THRESHOLD = 8


def cache_path(id):
    return os.path.join(COMRADE_CACHE, '{}.json'.format(id))


def are_bots_okay(account):
    """Return True unless this user's profile contains #nobot

    :param dict account: A user dict from the Mastodon.py API
    """

    return '#nobot' not in account.get('note', '')


def media_url_from_status(status, client):
    """Check the given status (or its parent) for a media attachment, and return the url or None.

    :param dict status: A toot dict from the Mastodon.py API
    :param Mastodon client: A Mastodon client from the Mastodon.py API
    """

    media = status.get('media_attachments', [])

    return media[0].get('url') if media else None


def download_media(media_url):
    """Saves the given media url, and returns the filename.

    :param str media_url:
    """

    r = requests.get(media_url, stream=True)

    content_type = r.headers['content-type']

    extension = mimetypes.guess_extension(content_type, strict=False)

    if extension.startswith('.jp'):
        extension = '.jpg'  # sigh

    filename = '{0}{1}'.format(random.randint(1, 1000000), extension)

    # https://stackoverflow.com/questions/16694907/how-to-download-large-file-in-python-with-requests-py
    with open(filename, 'wb') as fh:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                fh.write(chunk)

    return filename


def strip_toot(content):
    """Strip a toot's content bare of all but its core essence.

    :param str content:
    """

    stripped = re.sub(r'<p>', '', content)
    stripped = re.sub(r'</p>', '\n\n', stripped)
    stripped = re.sub(r'<br.*?>', '\n', stripped)
    stripped = re.sub(r'<.*?>', '', stripped)

    stripped = html.unescape(stripped)

    return stripped


class AbstractStreamer():
    def _setup_vars(self, config, client, callback, exclude_user):
        """Call me from __init__"""

        self.callback = callback
        self.config = config
        self.client = client
        self.exclude_user = exclude_user  # Needed for handle_reply

        self.user_time = {}   # Map of username to last interaction time
        self.user_count = {}  # Map of username to interaction counter

        self.cache = Cache(os.environ.get('COMRADE_CACHE'))

    def should_squelch_user(self, username):
        """Limit interactions to some number per minute"""

        if username in self.user_count:
            minutes_since_last_interaction = int((time.time() - self.user_time[username]) / 60)

            self.user_count[username] = max(0, self.user_count[username] - minutes_since_last_interaction)

        else:
            self.user_count[username] = 0

        self.user_time[username] = time.time()
        self.user_count[username] += 1

        return self.user_count[username] >= SQUELCH_THRESHOLD

    def handle_reply(self, notif_type=None, status=None, orig_status=None, media_url=None, account=None):
        if status:
            self.set_status(status.get('id'), status)

        if orig_status:
            self.set_status(orig_status.get('id'), orig_status)

        username = account.get('acct')

        print('Received {} from {}'.format(notif_type or 'update', username))

        try:
            if not self.are_replies_okay(status, account):
                return

            if self.should_squelch_user(username):
                count = self.user_count[username]

                if count >= SILENCE_THRESHOLD:
                    return

                if status:
                    status['visibility'] = 'direct'

                if orig_status:
                    orig_status['visibility'] = 'direct'

            if callable(self.callback):
                self.callback(
                    account=account,
                    client=self.client,
                    media_url=media_url,
                    notif_type=notif_type,
                    orig_status=orig_status,
                    status=status,
                )

            else:
                if media_url:
                    media_filename = download_media(media_url)

                else:
                    media_filename = None

                command = self.callback.format(
                    filename=media_filename,
                    config=self.config,
                    user=username,
                    id=orig_status.get('id', '') if orig_status else '',
                    visibility=status.get('visibility', 'public') if status else 'direct',
                    sensitive='--sensitive' if status and status.get('sensitive') else '',
                )

                subprocess.call(command, shell=True)

                if media_filename:
                    os.remove(media_filename)

        except Exception as e:
            print(str(e))

    def get_status(self, id):
        """Get a status entry from the cache, falling back to the client."""

        status = self.cache.get(id)

        if status:
            return json.loads(status)

        status = self.client.status(id)

        self.set_status(id, status)

        return status

    def set_status(self, id, status):
        """Cache a status entry."""

        self.cache.set(id, json.dumps(status, default=str))

    def are_replies_okay(self, status, account, limit=25):
        """Return True if the discussion thread is still pretty short.

        :param dict status: A toot dict from the Mastodon.py API
        :param dict account: A user dict from the Mastodon.py API
        :param Mastodon client: A Mastodon client from the Mastodon.py API
        :param str|None exclude_user: Don't reply to this user (usually our own name)
        :param int limit: Discussion thread length limit
        """

        if self.exclude_user and self.exclude_user == account.get('acct'):
            return False

        for i in range(limit):
            if i in (0, 1) and not are_bots_okay(account):  # Check orig post and parent for #nobot
                return False

            if not status.get('in_reply_to_id'):
                return True

            status = self.get_status(status.get('in_reply_to_id'))

        return False


class Streamer(AbstractStreamer, StreamListener):
    def __init__(self, *args, **kwargs):
        self._setup_vars(*args)

        super(Streamer, self).__init__(**kwargs)

    def on_update(self, status):
        account = status.get('account', {})

        media_url = media_url_from_status(status, self.client)

        return self.handle_reply(notif_type=None, status=status, orig_status=status, media_url=media_url, account=account)

    def on_notification(self, notif):
        account = notif.get('account', {})

        status = notif.get('status', {})
        orig_status = status

        media_url = None

        notif_type = notif.get('type')

        if notif_type == 'mention':
            media_url = media_url_from_status(status, self.client)

            if not media_url and status.get('in_reply_to_id'):
                parent = self.get_status(status.get('in_reply_to_id'))

                # if this mention doesn't have an image, check parent
                media_url = media_url_from_status(parent, self.client)

                if media_url:
                    status = parent

        elif notif_type == 'follow':
            media_url = account.get('avatar_static')

        elif notif_type == 'reblog':
            media_url = media_url_from_status(status, self.client)

        return self.handle_reply(notif_type=notif_type, status=status, orig_status=orig_status, media_url=media_url, account=account)

    def on_abort(self, status_code, data):
        print(status_code)
