# stream_media.py but it's a Mastodon client

import click
import json
import time

from mastodon import Mastodon

from comrade.streamer import Streamer


@click.command()
@click.option("--config", type=click.Path(dir_okay=False), required=True)
@click.option("--callback", type=str, required=True)
@click.option("--exclude-user", type=str)
def main(config, callback, exclude_user=None):
    print("Starting up...")

    cfg = json.load(open(config))

    while(True):
        print("Getting client...")

        try:
            client = Mastodon(
                access_token = cfg["mastodon_token"],
                api_base_url = cfg["mastodon_instance"],
            )

            print("Have client {}".format(client))

            client.stream_user(Streamer(config=config, callback=callback, exclude_user=exclude_user))

        except Exception:
            time.sleep(10)
