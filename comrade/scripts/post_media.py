import json
import mimetypes

import click
from pathlib import Path
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
@click.option(
    "--visibility",
    type=click.Choice(['public', 'unlisted', 'private', 'direct']),
    default="public",
    help="Post visibility (Mastodon only)"
)
@click.option("--log-dir", type=click.Path(dir_okay=True), default=None)
def main(
    config,
    image,
    alt,
    status,
    in_reply_to=None,
    sensitive=False,
    cw=None,
    visibility="public",
    log_dir=None
):
    """Post a status with optional media to supported platforms."""
    with open(config) as cfg_file:
        cfg = json.load(cfg_file)

    if log_dir:
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        logger.add(f"{log_dir}/comrade.log", retention="7 days")

    if cfg.get("mastodon_token"):
        try:
            mastodon = Mastodon(
                access_token=cfg["mastodon_token"],
                api_base_url=cfg["mastodon_instance"]
            )

            def upload_media(path, description):
                mime_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
                with open(path, "rb") as media_file:
                    response = mastodon.media_post(
                        media_file,
                        mime_type,
                        description=description,
                        synchronous=True,
                    )
                return response["id"]

            if image:
                paths = [p.strip() for p in image.split(",") if p.strip()]
                media_ids = [upload_media(item, alt) for item in paths]
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

