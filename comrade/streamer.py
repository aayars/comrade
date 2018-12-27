import html
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


def are_replies_okay(status, account, client, exclude_user=None, limit=25, sleep_time=2.5):
    """Return True if the discussion thread is still pretty short.

    :param dict status: A toot dict from the Mastodon.py API
    :param dict account: A user dict from the Mastodon.py API
    :param Mastodon client: A Mastodon client from the Mastodon.py API
    :param str|None exclude_user: Don't reply to this user (usually our own name)
    :param int limit: Discussion thread length limit
    :param float sleep_time: How long to sleep between requests when traversing thread
    """

    if exclude_user and exclude_user == account.get('acct'):
        print('    ... excluding user {}'.format(exclude_user))

        return False

    print('    ... checking length of discussion thread')

    for i in range(limit):
        if i in (0, 1) and not are_bots_okay(account):  # Check orig post and parent for #nobot
            print('    ... bots not are okay for {}'.format(account.get('acct')))

            return False

        if not status.get('in_reply_to_id'):
            return True

        status = client.status(status.get('in_reply_to_id'))

        time.sleep(sleep_time)  # Don't rapid-fire client requests at this hapless instance

    print('    ... too many responses in the thread already (limit: {})'.format(limit))

    return False


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

    stripped = re.sub(r'<span.*?>.*</span>', '', content)
    stripped = re.sub(r'<p>', '', stripped)
    stripped = re.sub(r'</p>', '\n\n', stripped)
    stripped = re.sub(r'<br.*?>', '\n', stripped)

    stripped = html.unescape(stripped)

    return stripped


def handle_reply(streamer=None, notif_type=None, status=None, orig_status=None, media_url=None, account=None):
    print('    ... Handling reply for status {}'.format(status.get('id')))

    try:
        if not are_bots_okay(account):
            print('    ... bots are not okay for {user}'.format(user=account.get('acct')))

            return

        print('    ... bots are okay!')

        if not are_replies_okay(status, account, streamer.client, exclude_user=streamer.exclude_user):
            print('    ... replies are not okay.')

            return

        print('    ... replies are okay!')

        if callable(streamer.callback):
            print('    ... running Python callback ...')

            streamer.callback(
                account=account,
                client=streamer.client,
                media_url=media_url,
                notif_type=notif_type,
                orig_status=orig_status,
                status=status,
            )

        else:
            if media_url:
                print('    ... downloading {}'.format(media_url))
                media_filename = download_media(media_url)

            else:
                print('    ... no media URL.')
                media_filename = None

            command = streamer.callback.format(
                filename=media_filename,
                config=streamer.config,
                user=account.get('acct'),
                id=orig_status.get('id', '') if orig_status else '',
                visibility=status.get('visibility', 'public') if status else 'direct',
                sensitive='--sensitive' if status and status.get('sensitive') else '',
            )

            print('    ... running command:')
            print('')
            print(command)
            print('')

            subprocess.call(command, shell=True)

            if media_filename:
                os.remove(media_filename)

        print('        ... done.')

    except Exception as e:
        print(str(e))


class Streamer(StreamListener):
    def __init__(self, config, client, callback, exclude_user, **kwargs):
        print('Streamer is initializing...')

        super(Streamer, self).__init__(**kwargs)

        self.callback = callback
        self.config = config
        self.client = client
        self.exclude_user = exclude_user

        print('    ... ready!')

    def on_update(self, status):
        account = status.get('account', {})

        print('Got a status update from {}'.format(account.get('acct')))

        media_url = media_url_from_status(status, self.client)

        return handle_reply(streamer=self, notif_type=None, status=status, orig_status=status,
                            media_url=media_url, account=account)

    def on_notification(self, notif):
        account = notif.get('account', {})

        print('Got a {kind} from {account}'.format(kind=notif.get('type'), account=account.get('acct')))

        status = notif.get('status', {})
        orig_status = status

        media_url = None

        notif_type = notif.get('type')

        if notif_type == 'mention':
            media_url = media_url_from_status(status, self.client)

            if not media_url and status.get('in_reply_to_id'):
                parent = self.client.status(status.get('in_reply_to_id'))

                media_url = media_url_from_status(parent, self.client)

                if media_url:
                    print('    ... using parent toot\'s image and privacy settings')

                    status = parent

        elif notif_type == 'follow':
            media_url = account.get('avatar_static')

        elif notif_type == 'reblog':
            media_url = media_url_from_status(status, self.client)

        return handle_reply(streamer=self, notif_type=notif_type, status=status, orig_status=orig_status,
                            media_url=media_url, account=account)

    def on_abort(self, status_code, data):
        print(status_code)
