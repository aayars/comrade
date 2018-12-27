import click
import json
import os
import time

from mastodon import Mastodon

from comrade.streamer import Streamer


@click.command(help="Work with offline toots.")
@click.option("--config", type=click.Path(dir_okay=False), required=True)
@click.option("--data-dir", type=click.Path(), required=True, help="Message sink offline data dir")
@click.option("--callback", type=str, help="If not given, act as a message sink")
@click.option("--exclude-user", type=str)
def main(config, data_dir, callback, exclude_user):
    cfg = json.load(open(config))

    while(True):
        try:
            client = Mastodon(
                access_token = cfg["mastodon_token"],
                api_base_url = cfg["mastodon_instance"],
            )

            os.environ['COMRADE_DATA'] = data_dir

            from comrade.offline import OfflineStreamer, online_callback

            if callback:  # Callback for offline streamer was provided
                OfflineStreamer(config, client, callback, exclude_user).process()

            else:  # Otherwise we're just a message sink
                client.stream_user(Streamer(config, client, online_callback, exclude_user))

        except Exception as e:
            print(str(e))

            time.sleep(10)
