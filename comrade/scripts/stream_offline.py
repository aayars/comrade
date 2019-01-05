import click
import json
import os
import time

from mastodon import Mastodon


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

            kwargs = {
                'client': client,
                'config': config,
                'data_dir': data_dir,
                'exclude_user': exclude_user,
            }

            if callback:  # Callback for offline streamer was provided
                from comrade.offline import OfflineStreamer

                OfflineStreamer(callback=callback, **kwargs).process()

            else:  # Otherwise we're just a message sink
                from comrade.streamer import Streamer
                from comrade.offline import get_online_callback

                streamer = Streamer(callback=get_online_callback(data_dir), **kwargs)

                client.stream_user(streamer)

        except Exception as e:
            print(str(e))

            time.sleep(10)
