from sqlalchemy import Column, Integer, String, DateTime, func, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.declarative import declarative_base
from core.db import metadata

Base = declarative_base(metadata=metadata)


class IPRecord(Base):
	__tablename__ = "ip_records"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
	timestamp: Mapped[str] = mapped_column(Text)
	ip: Mapped[str] = mapped_column(Text, index=True)
	country: Mapped[str | None] = mapped_column(Text, nullable=True)
	region: Mapped[str | None] = mapped_column(Text, nullable=True)
	city: Mapped[str | None] = mapped_column(Text, nullable=True)
	isp: Mapped[str | None] = mapped_column(Text, nullable=True)
	source_file: Mapped[str | None] = mapped_column(Text, nullable=True)
	created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
