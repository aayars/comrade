# Offline processing pattern for Comrade

import json
import os
import shutil
import tempfile
import time
import uuid

from .streamer import AbstractStreamer


def get_online_callback(data_dir):
    def online_callback(client=None, **kwargs):
        """Take a toot from an online source, and store it for offline processing. See stream_offline.py"""

        print("    ... Saving offline message")

        queue_dir = os.path.join(data_dir, 'queue')

        queued_count = len(os.listdir(queue_dir))

        if queued_count and kwargs.get('notif_type') == 'mention':
            message = 'Hello, @{}!\n\n' \
                'You are around place {} in queue.\n\n' \
                'Stand by, your toot is important.'

            message = message.format(kwargs['account'].get('acct'), queued_count + 1)

            in_reply_to_id = kwargs.get('orig_status', {}).get('id')

            status = client.status_post(message, in_reply_to_id=in_reply_to_id, visibility='direct')

            kwargs['placeholder_id'] = status.get('id')

        temp_path = os.path.join(queue_dir, '{}-{}.json'.format(int(time.time()), uuid.uuid4()))

        with open(temp_path + '-temp', 'w') as fh:
            fh.write(json.dumps(kwargs, default=str))

        shutil.move(temp_path + '-temp', temp_path)

        print('    ... Saved offline message!')

    return online_callback


class OfflineStreamer(AbstractStreamer):
    def __init__(self, *args, **kwargs):
        self._setup_vars(*args, **kwargs)

        self.queue_dir = os.path.join(self.data_dir, 'queue')

        if not os.path.exists(self.queue_dir):
            os.makedirs(self.queue_dir)


    def process(self):
        while True:
            for filename in sorted(os.listdir(self.queue_dir)):
                if not filename.endswith('.json'):
                    continue

                full_path = os.path.join(self.queue_dir, filename)

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

                        self.handle_reply(**comrade_status)

                except Exception as e:
                    print("Couldn't process {}: {}".format(filename, str(e)))

            time.sleep(2.5)  # Breathe a little between batches, I guess?
