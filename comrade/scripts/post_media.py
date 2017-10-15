import click
import json

from twython import Twython


@click.command()
@click.option("--config", type=click.Path(dir_okay=False), required=True)
@click.option("--image", type=click.Path(dir_okay=False), required=True)
@click.option("--status", type=str, required=True)
@click.option("--in-reply-to", type=str)
@click.option("--sensitive", is_flag=True, default=False)
def main(config, image, status, in_reply_to=None, sensitive=False):
    config = json.load(open(config))

    client = Twython(config["api_key"], config["api_secret"], config["access_token"], config["access_secret"])
    client.verify_credentials()

    response = client.upload_media(media=open(image, 'rb'))
    client.update_status(status=status, media_ids=[response['media_id']], in_reply_to_status_id=in_reply_to,
                         possibly_sensitive=sensitive)
