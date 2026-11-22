"""Historique des prédictions (SQLite en local, PostgreSQL en production)."""

import datetime as dt

from sqlalchemy import DateTime, Float, String, Text, create_engine, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
    pass


class PredictionRecord(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: dt.datetime.now(dt.UTC)
    )
    text: Mapped[str] = mapped_column(Text)
    label: Mapped[str] = mapped_column(String(16))
    confidence: Mapped[float] = mapped_column(Float)
    model_version: Mapped[str] = mapped_column(String(16))


class Database:
    def __init__(self, url: str):
        # Le pilote psycopg 3 doit être indiqué explicitement pour PostgreSQL.
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        self.engine = create_engine(url, pool_pre_ping=True)

    def init_schema(self) -> None:
        Base.metadata.create_all(self.engine)

    def is_up(self) -> bool:
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    def save(self, record: PredictionRecord) -> None:
        with Session(self.engine) as session:
            session.add(record)
            session.commit()

    def latest(self, limit: int) -> list[PredictionRecord]:
        with Session(self.engine) as session:
            query = select(PredictionRecord).order_by(PredictionRecord.id.desc()).limit(limit)
            return list(session.scalars(query))
