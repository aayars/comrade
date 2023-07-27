import click
import json
import mimetypes

from loguru import logger
from mastodon import Mastodon


@click.command()
@click.option("--config", type=click.Path(dir_okay=False), required=True)
@click.option("--image", type=click.Path(dir_okay=False), required=False)
@click.option("--alt", type=str, required=False)
@click.option("--status", type=str, required=True)
@click.option("--in-reply-to", type=str)
@click.option("--sensitive", is_flag=True, default=False)
@click.option("--cw", type=str)
@click.option("--visibility", type=click.Choice(["public", "unlisted", "private", "direct"]), default="public", help="Post visibility (Mastodon only)")
@click.option("--log-dir", type=click.Path(dir_okay=True), default=None)
def main(config, image, alt, status, in_reply_to=None, sensitive=False, cw=None, visibility="public", log_dir=None):
    config = json.load(open(config))

    if log_dir:
        logger.add(log_dir + "/comrade.log", retention="7 days")

    if config.get("mastodon_token"):
        try:
            mastodon = Mastodon(
                access_token=config["mastodon_token"],
                api_base_url=config["mastodon_instance"],
            )

            if image:
                responses = [mastodon.media_post(open(i, 'rb'), mimetypes.guess_type(i)[0], description=alt) for i in image.split(',')]
                media_ids = [r['id'] for r in responses]

            else:
                media_ids = None

            mastodon.status_post(status, in_reply_to_id=in_reply_to, media_ids=media_ids, sensitive=sensitive, visibility=visibility, spoiler_text=cw)

        except Exception as e:
            logger.error("Failed to post to Fediverse: " + str(e))
