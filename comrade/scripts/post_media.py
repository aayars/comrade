import click
import json

from twython import Twython


@click.command()
@click.option("--config", type=click.Path(dir_okay=False), required=True)
@click.option("--image", type=click.Path(dir_okay=False), required=True)
@click.option("--status", type=str, required=True)
def main(config, image, status):
    config = json.load(open(config))

    client = Twython(config["api_key"], config["api_secret"], config["access_token"], config["access_secret"])
    client.verify_credentials()

    response = client.upload_media(media=open(image, 'rb'))
    client.update_status(status=status, media_ids=[response['media_id']])
