import click
import json
import time

from mastodon import Mastodon
from sqlalchemy.orm import sessionmaker

from comrade.archive import ArchiveSink, ArchiveSource
from comrade.model import get_engine
from comrade.streamer import toot_from_status


@click.command(help='Work with archived toots.')
@click.option('--config', type=click.Path(dir_okay=False), required=True)
@click.option('--data-dir', type=click.Path(), required=True, help='Comrade data dir')
@click.option('--callback', type=str, help='If not given, act as a message sink')
@click.option('--timeline', type=str, default='home', help='‘home’, ‘local’, ‘public’, ‘tag/hashtag’ or ‘list/id’')
@click.option('--limit', type=int, default=100, help='Pagination size limit')
@click.option('--account-id', type=int, default=None, help='Get toots made by account id (overrides --timeline)')
@click.option('--exclude-user', type=str)
def main(config, data_dir, callback, exclude_user, timeline, limit, account_id):
    def online_callback(
            client=None,
            account=None,
            media_url=None,
            notif_type=None,
            orig_status=None,
            status=None,
            ):
        """Take a toot from an online source, and archive it."""

        if not status:
            return

        try:
            session = sessionmaker(get_engine(data_dir))()
            session.add(toot_from_status(status))
            session.commit()

            print('    ... Saved archived message!')

        except Exception as e:
            print(str(e))

    cfg = json.load(open(config))

    try:
        client = Mastodon(
            access_token=cfg["mastodon_token"],
            api_base_url=cfg["mastodon_instance"],
        )

        kwargs = {
            'client': client,
            'config': config,
            'data_dir': data_dir,
            'exclude_user': exclude_user,
        }

        if callback:  # Callback for archived streamer was provided
            ArchiveSource(callback=callback, **kwargs).process()  # TODO: Accept query params

        else:  # Otherwise we're just a message sink
            streamer = ArchiveSink(callback=online_callback, **kwargs)

            streamer.process(timeline=timeline, limit=limit, account_id=account_id)

    except Exception as e:
        print(str(e))

        time.sleep(10)
