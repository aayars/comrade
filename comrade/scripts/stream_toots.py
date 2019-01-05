# stream_media.py but it's a Mastodon client

import click
import json
import os
import time

from mastodon import Mastodon

from comrade.streamer import Streamer


@click.command()
@click.option("--config", type=click.Path(dir_okay=False), required=True)
@click.option("--callback", type=str, required=True)
@click.option("--data-dir", type=click.Path(), required=True)
@click.option("--exclude-user", type=str)
def main(config, callback, data_dir, exclude_user=None):
    cfg = json.load(open(config))

    while(True):
        try:
            client = Mastodon(
                access_token = cfg["mastodon_token"],
                api_base_url = cfg["mastodon_instance"],
            )

            streamer = Streamer(
                config=config,
                client=client,
                callback=callback,
                exclude_user=exclude_user,
                data_dir=data_dir
            )

            client.stream_user(streamer)

        except Exception as e:
            print(str(e))

            time.sleep(10)
