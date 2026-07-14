from datetime import date

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.data_service import seed
from src.data_service.db_tables import ActiveListing, Base


def test_clean_row_preserves_iso_post_date():
    row = pd.Series({"property_id": 1, "post_date": "2026-07-02"})

    cleaned = seed.clean_row(row)

    assert cleaned["post_date"] == date(2026, 7, 2)


def test_clean_row_parses_legacy_day_first_post_date():
    row = pd.Series({"property_id": 1, "post_date": "04/07/2026"})

    cleaned = seed.clean_row(row)

    assert cleaned["post_date"] == date(2026, 7, 4)


def test_seed_updates_existing_active_listing(tmp_path, monkeypatch):
    database = create_engine(f"sqlite:///{tmp_path / 'listings.db'}")
    Base.metadata.create_all(database)
    monkeypatch.setattr(seed, "SessionLocal", sessionmaker(bind=database))

    csv_path = tmp_path / "active.csv"
    csv_path.write_text(
        "property_id,price,post_date\nlisting-1,1000000,2026-07-02\n",
        encoding="utf-8",
    )
    seed.seed_table(str(csv_path), ActiveListing)

    csv_path.write_text(
        "property_id,price,post_date\nlisting-1,1200000,2026-07-03\n",
        encoding="utf-8",
    )
    seed.seed_table(str(csv_path), ActiveListing)

    with sessionmaker(bind=database)() as session:
        listing = session.query(ActiveListing).one()

    assert listing.price == 1_200_000
    assert listing.post_date == date(2026, 7, 3)


def test_active_audit_reports_csv_date_difference(tmp_path):
    from src.data_service.bootstrap import audit_active_rows

    database = create_engine(f"sqlite:///{tmp_path / 'listings.db'}")
    Base.metadata.create_all(database)
    with sessionmaker(bind=database)() as session:
        session.add(ActiveListing(property_id="listing-1", price=1_000_000, post_date=date(2026, 2, 7)))
        session.commit()

    csv_path = tmp_path / "active.csv"
    csv_path.write_text(
        "property_id,price,post_date\nlisting-1,1000000,2026-07-02\n",
        encoding="utf-8",
    )

    report = audit_active_rows(csv_path, database.url.render_as_string(hide_password=False))

    assert report["csv_rows"] == 1
    assert report["database_rows"] == 1
    assert report["changed_fields"] == {"post_date": 1}
