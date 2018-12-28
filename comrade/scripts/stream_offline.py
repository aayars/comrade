import click
import json
import os
import time

from mastodon import Mastodon


@click.command(help="Work with offline toots.")
@click.option("--config", type=click.Path(dir_okay=False), required=True)
@click.option("--cache-dir", type=click.Path(), required=True, help="Status cache dir")
@click.option("--data-dir", type=click.Path(), required=True, help="Message sink offline data dir")
@click.option("--callback", type=str, help="If not given, act as a message sink")
@click.option("--exclude-user", type=str)
def main(config, cache_dir, data_dir, callback, exclude_user):
    cfg = json.load(open(config))

    while(True):
        try:
            client = Mastodon(
                access_token = cfg["mastodon_token"],
                api_base_url = cfg["mastodon_instance"],
            )

            os.environ['COMRADE_CACHE'] = cache_dir
            os.environ['COMRADE_DATA'] = data_dir

            if callback:  # Callback for offline streamer was provided
                from comrade.offline import OfflineStreamer

                OfflineStreamer(config, client, callback).process()

            else:  # Otherwise we're just a message sink
                from comrade.streamer import Streamer
                from comrade.offline import online_callback

                client.stream_user(Streamer(config, client, online_callback, exclude_user))

        except Exception as e:
            print(str(e))

            time.sleep(10)
