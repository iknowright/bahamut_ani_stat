from typing import Dict, Set

import sqlalchemy
from sqlalchemy import select, update
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from bahamut_ani_stat.db import models


def create_tables(db_uri: str):
    engine = sqlalchemy.create_engine(db_uri)
    with engine.connect():
        models.Base.metadata.create_all(engine)


def upsert_anime(session: Session, attrs: Dict) -> None:
    insert_stmt = insert(models.Anime).values(**attrs)
    upsert_stmt = insert_stmt.on_conflict_do_update(
        index_elements=[models.Anime.sn], set_=attrs
    )
    session.execute(upsert_stmt)


def clean_up_old_animes(session: Session, new_animes_sn: Set[str]):
    # Set is_new to False for old animes
    select_stmt = select(models.Anime.sn).where(models.Anime.is_new.is_(True))
    result = session.execute(select_stmt)
    original_new_animes_sn = result.scalars().all()
    old_anime_sn = set(original_new_animes_sn) - set(new_animes_sn)

    update_stmt = (
        update(models.Anime)
        .where(models.Anime.sn.in_(old_anime_sn))
        .values(is_new=False)
    )
    session.execute(update_stmt)


def is_view_count_changed_since_latest_update(
    session: Session, view_count: float, anime_sn: str
):
    stmt = (
        select(models.AnimeViewCount.view_count)
        .filter_by(anime_sn=anime_sn)
        .order_by(models.AnimeViewCount.insert_time.desc())
    )
    latest_view_count = session.execute(stmt).scalars().first()

    return view_count != latest_view_count