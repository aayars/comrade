import time
import json
import mimetypes

import click
from loguru import logger
from mastodon import Mastodon

@click.command()
@click.option("--config", type=click.Path(dir_okay=False), required=True)
@click.option(
    "--image",
    type=click.Path(dir_okay=False),
    multiple=True,
    required=False,
    help="Path to an image file. Use multiple --image options to attach multiple images.",
)
@click.option("--alt", type=str, required=False)
@click.option("--status", type=str, required=True)
@click.option("--in-reply-to", type=str)
@click.option("--sensitive", is_flag=True, default=False)
@click.option("--cw", type=str)
@click.option(
    "--visibility",
    type=click.Choice(['public', 'unlisted', 'private', 'direct']),
    default="public",
    help="Post visibility (Mastodon only)"
)
@click.option("--log-dir", type=click.Path(dir_okay=True), default=None)
def main(
    config,
    image: tuple[str, ...],
    alt,
    status,
    in_reply_to=None,
    sensitive=False,
    cw=None,
    visibility="public",
    log_dir=None,
):
    cfg = json.load(open(config))

    if log_dir:
        logger.add(f"{log_dir}/comrade.log", retention="7 days")

    if cfg.get("mastodon_token"):
        try:
            mastodon = Mastodon(
                access_token=cfg["mastodon_token"],
                api_base_url=cfg["mastodon_instance"]
            )

            def upload_media(path, description):
                mime_type = mimetypes.guess_type(path)[0]
                response = mastodon.media_post(
                    open(path, "rb"),
                    mime_type,
                    description=description,
                    synchronous=True
                )
                return response["id"]

            if image:
                media_ids = [upload_media(path, alt) for path in image]
            else:
                media_ids = None

            mastodon.status_post(
                status,
                in_reply_to_id=in_reply_to,
                media_ids=media_ids,
                sensitive=sensitive,
                visibility=visibility,
                spoiler_text=cw
            )

        except Exception as e:
            logger.error("Failed to post to Fediverse: " + str(e))


if __name__ == "__main__":
    main()

