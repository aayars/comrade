import click
import json
import os
import shutil
import time
import uuid

from mastodon import Mastodon

from comrade.streamer import Streamer
from comrade.offline import OfflineStreamer


@click.command(help="Work with offline toots.")
@click.option("--config", type=click.Path(dir_okay=False), required=True)
@click.option("--data-dir", type=click.Path(), required=True, help="Message sink offline data dir")
@click.option("--callback", type=str, help="If not given, act as a message sink")
@click.option("--exclude-user", type=str)
def main(config, data_dir, callback, exclude_user):
    def online_callback(client=None, cache=None, **kwargs):
        """Take a toot from an online source, and store it for offline processing."""

        print("    ... Saving offline message")

        queue_dir = os.path.join(data_dir, 'queue')

        if not os.path.exists(queue_dir):
            os.makedirs(queue_dir)

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

    cfg = json.load(open(config))

    while(True):
        try:
            client = Mastodon(
                access_token=cfg["mastodon_token"],
                api_base_url=cfg["mastodon_instance"],
            )

            kwargs = {
                'client': client,
                'config': config,
                'data_dir': data_dir,
                'exclude_user': exclude_user,
            }

            if callback:  # Callback for offline streamer was provided
                OfflineStreamer(callback=callback, **kwargs).process()

            else:  # Otherwise we're just a message sink
                streamer = Streamer(callback=online_callback, **kwargs)

                client.stream_user(streamer)

        except Exception as e:
            print(str(e))

            time.sleep(10)
