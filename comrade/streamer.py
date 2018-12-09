import mimetypes
import os
import random
import re
import subprocess
import time

from mastodon.streaming import StreamListener

import requests


def are_bots_okay(account):
    """Return True unless this user's profile contains #nobot

    :param dict account: A user dict from the Mastodon.py API
    """

    return '#nobot' not in account.get('note', '')


def are_replies_okay(status, account, client, exclude_user=None, limit=5, sleep_time=2.5):
    """Return True if the discussion thread is still pretty short.

    :param dict status: A toot dict from the Mastodon.py API
    :param dict account: A user dict from the Mastodon.py API
    :param Mastodon client: A Mastodon client from the Mastodon.py API
    :param str|None exclude_user: Don't reply to this user (usually our own name)
    :param int limit: Discussion thread length limit
    :param float sleep_time: How long to sleep between requests when traversing thread
    """

    if exclude_user and exclude_user == account.get('acct'):
        return

    if status.get('reblog'):
        return

    for i in range(limit):
        if not status.get('in_reply_to_id'):
            return True

        if i in (0, 1) and not are_bots_okay(account):  # Check orig post and parent for #nobot
            return False

        status = client.status(status.get('in_reply_to_id'))

        time.sleep(sleep_time)  # Don't rapid-fire client requests at this hapless instance

    # Already enough responses in a thread
    return False


def media_url_from_status(status, client):
    """Check the given status (or its parent) for a media attachment, and return the url or None.

    :param dict status: A toot dict from the Mastodon.py API
    :param Mastodon client: A Mastodon client from the Mastodon.py API
    """

    media = status.get('media_attachments', [])

    if not media and status.get('in_reply_to_id'):
        status = client.status(status.get('in_reply_to_id'))

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

    stripped = re.sub(r'<span.*?>.*</span>', '', content)
    stripped = re.sub(r'<p>', '', stripped)
    stripped = re.sub(r'</p>', '\n\n', stripped)
    stripped = re.sub(r'<br.*?>', '\n', stripped)

    stripped = stripped.unescape(stripped)

    return stripped


class Streamer(StreamListener):
    def __init__(self, config, callback, exclude_user, **kwargs):
        print('Streamer is initializing...')

        self.__init__(**kwargs)

        self.callback = callback
        self.config = config
        self.exclude_user = exclude_user

    def on_update(self, status):
        print('Got update {}'.format(status))

        account = status.get('account', {})

        if not are_bots_okay(account):
            return

        print('    ... bots are okay!')

        media_url = media_url_from_status(status, self.client)

        return self._handle_reply(status, media_url, account)

    def on_notification(self, notif):
        print('Got notification {}'.format(notif))

        account = notif.get('account', {})

        if not are_bots_okay(account):
            return

        print('    ... bots are okay!')

        if notif.get('type') == 'mention':
            orig_status = notif.get('status', {})

            status = orig_status

            media_url = media_url_from_status(status, self.client)

        elif notif.get('type') == 'follow':
            status = None

            media_url = account.get('avatar_static')

        elif notif.get('type') != 'favourite':
            status = notif.get('status', {})

            media_url = media_url_from_status(status, self.client)

        return self._handle_reply(status, media_url, account)

    def _handle_reply(self, status, media_url, account):
        print('Handling reply')

        if not are_replies_okay(status, account, self.client, exclude_user=self.exclude_user):
            return

        print('    ... replies are okay!')
        print('    ... have media url {}'.format(media_url))

        media_filename = download_media(media_url) if media_url else None

        try:
            if callable(self.callback):
                self.callback(
                    status=status,
                    account=account,
                    client=self.client,
                    media_filename=media_filename,
                )

            else:
                command = self.callback.format(
                    filename=media_filename,
                    config=self.config,
                    user=account.get('acct'),
                    id=status.get('id') if status else None,
                    visibility=status.get('visibility', 'public') if status else 'direct',
                    sensitive='--sensitive' if status and status.get('sensitive') else '',
                    content=strip_toot(status.get('content', '')) if status else None,
                )

                print('    ... running command:')
                print('')
                print(command)
                print('')

                subprocess.call(command, shell=True)

                print('        ... done.')

        except Exception as e:
            print(str(e))

        os.remove(media_filename)

    def on_abort(self, status_code, data):
        print(status_code)
