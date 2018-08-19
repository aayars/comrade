import click
import json
import mimetypes

from mastodon import Mastodon
from twython import Twython

@click.command()
@click.option("--config", type=click.Path(dir_okay=False), required=True)
@click.option("--image", type=click.Path(dir_okay=False), required=False)
@click.option("--status", type=str, required=True)
@click.option("--in-reply-to", type=str)
@click.option("--sensitive", is_flag=True, default=False)
def main(config, image, status, in_reply_to=None, sensitive=False):
    config = json.load(open(config))

    if config.get("api_key"):
        try:
            client = Twython(config["api_key"], config["api_secret"], config["access_token"], config["access_secret"])
            client.verify_credentials()

            if image:
                responses = [client.upload_media(media=open(i, 'rb')) for i in image.split(',')]
                media_ids = [r['media_id'] for r in responses]

            else:
                media_ids = None

            client.update_status(status=status, media_ids=media_ids, in_reply_to_status_id=in_reply_to, possibly_sensitive=sensitive)

        except Exception as e:
            # ¯\_(ツ)_/¯
            pass

    if config.get("mastodon_token"):
        try:
            mastodon = Mastodon(
                access_token = config["mastodon_token"],
                api_base_url = config["mastodon_instance"],
            )

            if image:
                responses = [mastodon.media_post(open(i, 'rb'), mimetypes.guess_type(i)[0]) for i in image.split(',')]
                media_ids = [r['id'] for r in responses]

            else:
                media_ids = None

            mastodon.status_post(status, in_reply_to_id=in_reply_to, media_ids=media_ids, sensitive=sensitive)

        except Exception as e:
            pass
