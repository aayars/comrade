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
@click.option("--cw", type=str)
@click.option("--visibility", type=click.Choice(["public", "unlisted", "private", "direct"]), default="public", help="Post visibility (Mastodon only)")
def main(config, image, status, in_reply_to=None, sensitive=False, cw=None, visibility="public"):
    config = json.load(open(config))

    if config.get("api_key"):
        try:
            print("DEBUG: Posting to Twitter")

            client = Twython(config["api_key"], config["api_secret"], config["access_token"], config["access_secret"])
            client.verify_credentials()

            print("DEBUG: Verified credentials")

            if image:
                responses = [client.upload_media(media=open(i, 'rb')) for i in image.split(',')]

                print("DEBUG: Got responses from upload_media: " + str(responses))

                media_ids = [r['media_id'] for r in responses]

            else:
                media_ids = None

            response = client.update_status(status=status, media_ids=media_ids, in_reply_to_status_id=in_reply_to, possibly_sensitive=sensitive)

            print("DEBUG: Got response from update_status: " + str(response))

        except Exception as e:
            print("Failed to post to Twitter: " + str(e))

    if config.get("mastodon_token"):
        try:
            mastodon = Mastodon(
                access_token=config["mastodon_token"],
                api_base_url=config["mastodon_instance"],
            )

            if image:
                responses = [mastodon.media_post(open(i, 'rb'), mimetypes.guess_type(i)[0]) for i in image.split(',')]
                media_ids = [r['id'] for r in responses]

            else:
                media_ids = None

            mastodon.status_post(status, in_reply_to_id=in_reply_to, media_ids=media_ids, sensitive=sensitive, visibility=visibility, spoiler_text=cw)

        except Exception:
            print("Failed to post to Fediverse: " + str(e))
