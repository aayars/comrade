import click
import json
import mimetypes

from loguru import logger
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
@click.option("--log-dir", type=click.Path(dir_okay=True), default=None)
def main(config, image, status, in_reply_to=None, sensitive=False, cw=None, visibility="public", log_dir=None):
    config = json.load(open(config))

    if log_dir:
        logger.add(log_dir + "/comrade.log", retention="7 days")

    if config.get("api_key"):
        try:
            logger.debug("Posting to Twitter")

            client = Twython(config["api_key"], config["api_secret"], config["access_token"], config["access_secret"])
            client.verify_credentials()

            logger.debug("Verified credentials")

            if image:
                responses = []

                for i in image.split(','):
                    if i.endswith('.gif'):
                        responses.append(client.upload_video(media=open(i, 'rb'), media_type='image/gif', media_category='tweet_gif'))

                    elif i.endswith('.mp4'):
                        responses.append(client.upload_video(media=open(i, 'rb'), media_type='video/mp4', media_category='tweet_video', check_progress=True))

                    else:
                        responses.append(client.upload_media(media=open(i, 'rb')))

                logger.debug("Got responses from upload_media: " + str(responses))

                media_ids = [r['media_id'] for r in responses]

            else:
                media_ids = None

            if cw:
                cw_status = cw + "\n\n" + status

            else:
                cw_status = status

            response = client.update_status(status=cw_status, media_ids=media_ids, in_reply_to_status_id=in_reply_to, possibly_sensitive=bool(cw or sensitive))

            logger.debug("Got response from update_status: " + str(response))

        except Exception as e:
            logger.error("Failed to post to Twitter: " + str(e))

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

        except Exception as e:
            logger.error("Failed to post to Fediverse: " + str(e))
