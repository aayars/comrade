# Offline processing pattern for Comrade

import json
import os
import shutil
import tempfile
import time
import uuid

from .streamer import handle_reply

COMRADE_DATA = os.environ.get('COMRADE_DATA', 'offline-data')


def online_callback(client=None, **kwargs):
    """Take a toot from an online source, and store it for offline processing. See stream_offline.py"""

    print("    ... Saving offline message")

    queued_count = len(os.listdir(COMRADE_DATA))

    if queued_count and kwargs.get('notif_type') == 'mention':
        message = 'Hello, @{}!\n\n' \
            'You are around place {} in queue.\n\n' \
            'Stand by, your toot is important.'
            
        message = message.format(kwargs['account'].get('acct'), queued_count + 1)

        in_reply_to_id = kwargs.get('orig_status', {}).get('id')

        status = client.status_post(message, in_reply_to_id=in_reply_to_id, visibility='direct')

        kwargs['placeholder_id'] = status.get('id')

    temp_path = os.path.join(COMRADE_DATA, '{}-{}.json'.format(int(time.time()), uuid.uuid4()))

    with open(temp_path + '-temp', 'w') as fh:
        fh.write(json.dumps(kwargs, default=str))

    shutil.move(temp_path + '-temp', temp_path)

    print('    ... Saved offline message!')


class OfflineStreamer():
    def __init__(self, config, client, callback, exclude_user):
        self.callback = callback
        self.config = config
        self.client = client
        self.exclude_user = exclude_user  # Needed for handle_reply

    def process(self):
        while True:
            for filename in sorted(os.listdir(COMRADE_DATA)):
                if not filename.endswith('.json'):
                    continue

                full_path = os.path.join(COMRADE_DATA, filename)

                try:
                    with tempfile.TemporaryDirectory() as tempdir:
                        temp_path = os.path.join(tempdir, filename)

                        shutil.move(full_path, temp_path)

                        with open(temp_path, 'r') as fh:
                            comrade_status = json.load(fh)

                        # Was there a placeholder message indicating position in queue?
                        placeholder_id = comrade_status.pop('placeholder_id', None)

                        # If so, delete it.
                        if placeholder_id:
                            try:
                                self.client.status_delete(placeholder_id)

                            except Exception:
                                pass

                        handle_reply(streamer=self, **comrade_status)

                except Exception as e:
                    print("Couldn't process {}: {}".format(filename, str(e)))

            time.sleep(2.5)  # Breathe a little between batches, I guess?
