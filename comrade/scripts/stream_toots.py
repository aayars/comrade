# stream_media.py but it's a Mastodon client

import click
import json
import time

from mastodon import Mastodon


@click.command()
@click.option("--config", type=click.Path(dir_okay=False), required=True)
@click.option("--callback", type=str, required=True)
@click.option("--cache-dir", type=click.Path(), required=True, help="Status cache dir")
@click.option("--exclude-user", type=str)
def main(config, callback, cache_dir, exclude_user=None):
    cfg = json.load(open(config))

    while(True):
        try:
            client = Mastodon(
                access_token = cfg["mastodon_token"],
                api_base_url = cfg["mastodon_instance"],
            )

            os.environ['COMRADE_CACHE'] = cache_dir

            from comrade.streamer import Streamer

            client.stream_user(Streamer(config, client, callback, exclude_user))

        except Exception as e:
            print(str(e))

            time.sleep(10)
