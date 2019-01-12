import os

from sqlalchemy import Boolean, Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Toot(Base):
    """See 'Toot dicts' in Mastodon.py"""

    __tablename__ = 'toot'

    id = Column(Integer, primary_key=True)

    uri = Column(String)

    url = Column(String)

    account_id = Column(Integer)  # Toot dict contains whole user dict, we keep 'id'

    account_name = Column(String)  # Toot dict contains whole user dict, we keep 'acct'

    in_reply_to_id = Column(Integer)

    in_reply_to_account_id = Column(Integer)

    reblog_id = Column(Integer)  # Toot dict contains entire status. We keep the 'id'

    content = Column(String)

    created_at = Column(String)  # TODO: Convert me

    reblogs_count = Column(Integer)

    favourites_count = Column(Integer)

    reblogged = Column(Boolean)

    favourited = Column(Boolean)

    sensitive = Column(Boolean)

    spoiler_text = Column(String)

    visibility = Column(String)

    media_url = Column(String)  # TODO: Support more than one

    language = Column(String)

    muted = Column(Boolean)

    pinned = Column(Boolean)

    def __repr__(self):
        return "<Toot id='{self.id}'>".format(self=self)


def get_engine(data_dir):
    archive_dir = os.path.join(data_dir, 'archive')

    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)

    engine = create_engine('sqlite:///{}/toots.db'.format(archive_dir))

    Base.metadata.create_all(engine)

    return engine
