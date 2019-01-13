# Offline processing pattern for Comrade

import json
import os
import shutil
import tempfile
import time

from .streamer import AbstractStreamer


class OfflineStreamer(AbstractStreamer):
    """Stream recent toots from a local queue."""

    def __init__(self, *args, **kwargs):
        self._setup_vars(*args, **kwargs)

        self.queue_dir = os.path.join(self.data_dir, 'queue')

        if not os.path.exists(self.queue_dir):
            os.makedirs(self.queue_dir)

    # Queue is populated with stream_offline.py
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

            time.sleep(1.0)
