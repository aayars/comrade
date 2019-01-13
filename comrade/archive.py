# Historical backfill and processing pattern for Comrade

import time

from sqlalchemy.orm import sessionmaker

from .model import Toot, get_engine
from .streamer import AbstractStreamer, media_url_from_status


class AbstractArchiveStreamer(AbstractStreamer):
    """Abstract class for archive streamers. Don't use directly."""

    def __init__(self, *args, **kwargs):
        self._setup_vars(*args, **kwargs)

    def should_squelch_user(self, *args):
        return False

    def get_status(self, id):
        """Get a status entry from the archive, falling back to the cache, then the client."""

        session = sessionmaker(get_engine(self.data_dir))()

        toot = session.query(Toot).filter(Toot.id == id).first()

        if toot:
            return toot.__dict__

        return super().get_status(id)


class ArchiveSink(AbstractArchiveStreamer):
    """Process historical toots from a server"""

    def are_replies_okay(self, *args):
        return True

    def process(self, timeline='home', limit=100, account_id=None):
        if account_id:
            statuses = self.client.account_statuses(id=account_id, limit=limit)

        else:
            statuses = self.client.timeline(timeline=timeline, limit=limit)

        while statuses:
            for status in statuses:
                media_url = media_url_from_status(status)

                self.handle_reply(notif_type='update', status=status, orig_status=status, media_url=media_url, account=status.get('account'))

            statuses = self.client.fetch_next(statuses)

            time.sleep(1.0)


class ArchiveSource(AbstractArchiveStreamer):
    """Process historical toots from a local archive"""

    def __init__(self, *args, **kwargs):
        self._setup_vars(*args, **kwargs)

    # Archive is created via callback in stream_archive.py
    def process(self):
        """TODO: Filter by columns!"""

        session = sessionmaker(get_engine(self.data_dir))()

        for toot in session.query(Toot):
            self.handle_reply(notif_type='update', status=toot.__dict__, orig_status=toot.__dict__, media_url=toot.media_url, account=toot.account_name)
