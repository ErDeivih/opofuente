"""Modelos de infraestructura (no son entidades de negocio).

Las entidades de negocio empiezan en S01 (`oppositions`, `convocations`, ...). Aquí solo
vive el registro de metadatos de la instancia local, que permite a /health/ready
comprobar que la migración inicial se aplicó de verdad y no solo que el fichero existe.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from opofuente.infrastructure.db import Base


class AppMetadataRecord(Base):
    __tablename__ = "app_metadata"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
