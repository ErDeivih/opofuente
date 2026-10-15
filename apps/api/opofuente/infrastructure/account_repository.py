"""Cuentas, sesiones, recuperación, freno y consentimiento sobre SQLite (S28, §8 y §9).

**Qué guarda y qué no**, porque es la parte del bloque que más fácil se estropea:

- la contraseña, **solo** como resumen argon2id; el resumen vive en este repositorio y no sale de él
  salvo en el tipo `AccountWithSecret`, que existe precisamente para que sacarlo sea un acto
  deliberado;
- los testigos de sesión y de recuperación, **solo** como su SHA-256: quien lea la base no puede
  suplantar a nadie;
- **ni una dirección de red y ni un navegador**: no hay columna donde ponerlos, y el inventario de
  datos del §9 lo declara y la prueba de integración lo comprueba contra este esquema;
- de la auditoría, el **antes y el después sanitizado** («se dio de alta», «accedió», «cerró la
  cuenta»), nunca la contraseña ni el testigo.

Todo lo que escribe pasa por `audit_events` con su actor y su identificador de correlación, que es
elcamino auditado de siempre (migración 0004): el §8 pide que el alta, el acceso y la baja queden
registrados, y «registrado» aquí significa una fila que se puede leer.
"""

from __future__ import annotations

import json
from datetime import datetime
from uuid import uuid4

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session, sessionmaker

from opofuente.application.account_models import (
    Account,
    AccountAuditEntry,
    AccountWithSecret,
    ConsentSummary,
    SessionView,
)
from opofuente.domain.accounts import (
    ACCOUNT_AUDIT_ACTOR,
    AccountEventKind,
    ThrottleState,
)
from opofuente.infrastructure.correlation import get_correlation_id
from opofuente.infrastructure.db_models import (
    AccountRecord,
    AccountSessionRecord,
    AnalyticsEventRecord,
    AuditEventRecord,
    ConsentRecordRecord,
    LearningErrorRecord,
    LoginThrottleRecord,
    NotesReportRecord,
    PasswordResetRecord,
    ReviewItemRecord,
    StudySessionRecord,
)
from opofuente.infrastructure.sql_counts import affected_rows

#: El tipo de objeto con el que se firman los eventos de cuenta en `audit_events`.
ACCOUNT_OBJECT_TYPE = "account"


def _account(fila: AccountRecord) -> Account:
    return Account(
        id=fila.id,
        email=fila.email,
        email_normalized=fila.email_normalized,
        owner_id=fila.owner_id,
        created_at=fila.created_at,
        password_changed_at=fila.password_changed_at,
    )


class SqlAlchemyAccountRepository:
    """Todo lo que toca las tablas de cuentas. Ninguna ruta escribe SQL por su cuenta."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    # ------------------------------------------------------------------ auditoría

    def write_event(
        self,
        *,
        kind: AccountEventKind,
        account_id: str,
        occurred_at: datetime,
        detail: dict[str, object] | None = None,
    ) -> str:
        """Escribe el evento auditado de un movimiento de cuenta y devuelve su identificador.

        `detail` es **lo que se puede contar**: el desenlace y poco más. La contraseña, el testigo y
        la dirección de correo no entran aquí nunca. Los eventos sin cuenta —un intento contra una
        dirección que no existe— se firman con el resumen de la dirección como identificador, que es
        lo único que hay, para que el freno y la auditoría cuenten lo mismo.
        """
        evento_id = str(uuid4())
        payload = json.dumps(detail or {}, ensure_ascii=False, sort_keys=True)
        with self._session_factory() as session:
            session.add(
                AuditEventRecord(
                    id=evento_id,
                    actor=ACCOUNT_AUDIT_ACTOR,
                    action=str(kind),
                    object_type=ACCOUNT_OBJECT_TYPE,
                    object_id=account_id,
                    before_json=None,
                    after_json=payload,
                    correlation_id=get_correlation_id(),
                    created_at=occurred_at,
                )
            )
            session.commit()
        return evento_id

    def events_for(self, account_id: str, *, limit: int = 50) -> list[AccountAuditEntry]:
        """Los últimos movimientos de una cuenta, ya legibles para la pantalla de «mi cuenta»."""
        with self._session_factory() as session:
            filas = (
                session.execute(
                    select(AuditEventRecord)
                    .where(
                        AuditEventRecord.object_type == ACCOUNT_OBJECT_TYPE,
                        AuditEventRecord.object_id == account_id,
                    )
                    .order_by(AuditEventRecord.created_at.desc())
                    .limit(limit)
                )
                .scalars()
                .all()
            )
        entradas: list[AccountAuditEntry] = []
        for fila in filas:
            detalle: dict[str, object] = {}
            if fila.after_json:
                try:
                    leido = json.loads(fila.after_json)
                except json.JSONDecodeError:
                    leido = None
                if isinstance(leido, dict):
                    detalle = {str(clave): valor for clave, valor in leido.items()}
            entradas.append(
                AccountAuditEntry(kind=fila.action, occurred_at=fila.created_at, detail=detalle)
            )
        return entradas

    # ---------------------------------------------------------------------- cuentas

    def create_account(
        self,
        *,
        email: str,
        email_normalized: str,
        password_hash: str,
        password_algo: str,
        owner_id: str,
        now: datetime,
    ) -> Account:
        with self._session_factory() as session:
            fila = AccountRecord(
                id=str(uuid4()),
                email=email,
                email_normalized=email_normalized,
                password_hash=password_hash,
                password_algo=password_algo,
                owner_id=owner_id,
                created_at=now,
                updated_at=now,
                password_changed_at=now,
            )
            session.add(fila)
            session.commit()
            return _account(fila)

    def account_with_secret(self, email_normalized: str) -> AccountWithSecret | None:
        """La cuenta y su resumen, para comprobar una contraseña. Es el único camino al resumen."""
        with self._session_factory() as session:
            fila = session.execute(
                select(AccountRecord).where(AccountRecord.email_normalized == email_normalized)
            ).scalar_one_or_none()
        if fila is None:
            return None
        return AccountWithSecret(
            account=_account(fila),
            password_hash=fila.password_hash,
            password_algo=fila.password_algo,
        )

    def account_by_id(self, account_id: str) -> Account | None:
        with self._session_factory() as session:
            fila = session.get(AccountRecord, account_id)
        return None if fila is None else _account(fila)

    def set_password(self, *, account_id: str, password_hash: str, now: datetime) -> None:
        with self._session_factory() as session:
            fila = session.get(AccountRecord, account_id)
            if fila is None:
                return
            fila.password_hash = password_hash
            fila.password_changed_at = now
            fila.updated_at = now
            session.commit()

    def close_account(self, account_id: str, *, keep_audit_event_id: str) -> dict[str, int]:
        """Cierra la cuenta: borra lo suyo y deja constancia de que se cerró.

        En una sola transacción y en este orden:

        1. el progreso del dueño de la cuenta (`acct:<id>`), que es lo que el §9 declara que se
        borra;        2. la cuenta, que se lleva por delante sus sesiones y sus enlaces de
        recuperación
           (`ON DELETE CASCADE`);
        3. los eventos de auditoría de esa cuenta **menos el del cierre**, que se conserva: es la
           única prueba de que la baja se hizo, y sin él «cerró la cuenta» sería una promesa sin
           rastro.

        Devuelve cuántas filas se ha llevado de cada cosa, para poder decirlo en la respuesta en
        lugar de en un «hecho» sin cifra.
        """
        with self._session_factory() as session:
            sesiones = session.execute(
                select(func.count())
                .select_from(AccountSessionRecord)
                .where(AccountSessionRecord.account_id == account_id)
            ).scalar_one()
            cuentas = session.execute(
                select(func.count())
                .select_from(AccountRecord)
                .where(AccountRecord.id == account_id)
            ).scalar_one()
            if not cuentas:
                return {"account": 0, "sessions": 0, "study_rows": 0, "audit_events": 0}
            fila = session.get(AccountRecord, account_id)
            owner_id = "" if fila is None else fila.owner_id
            estudio = self._delete_owner_rows(session, owner_id)
            session.execute(delete(AccountRecord).where(AccountRecord.id == account_id))
            eventos = affected_rows(
                session.execute(
                    delete(AuditEventRecord).where(
                        AuditEventRecord.object_type == ACCOUNT_OBJECT_TYPE,
                        AuditEventRecord.object_id == account_id,
                        AuditEventRecord.id != keep_audit_event_id,
                    )
                )
            )
            session.commit()
        return {
            "account": int(cuentas),
            "sessions": int(sesiones),
            "study_rows": estudio,
            "audit_events": eventos,
        }

    def _delete_owner_rows(self, session: Session, owner_id: str) -> int:
        """Borra el progreso de un dueño.

        Las hijas de la sesión de estudio —`session_questions`, `attempts`, `attempt_evaluations` y
        `learning_errors`— **no** se borran aquí a mano: cuelgan con `ON DELETE CASCADE`, y
        borrarlas otra vez solo serviría para que la cifra que se devuelve contara cosas que ya no
        estaban.

        Los **repasos** van primero y por otra vía, porque `review_items` no está firmada por dueño:
        se van los que apuntan a un fallo de este dueño, y se van antes de que el fallo desaparezca
        (la relación es `ON DELETE SET NULL`, así que si se borrara antes el fallo, el repaso se
        quedaría huérfano y sin dueño identificable).
        """
        if not owner_id:
            return 0
        fallos_del_dueno = select(LearningErrorRecord.id).where(
            LearningErrorRecord.owner_id == owner_id
        )
        borradas = affected_rows(
            session.execute(
                delete(ReviewItemRecord).where(
                    ReviewItemRecord.learning_error_id.in_(fallos_del_dueno)
                )
            )
        )
        borradas += affected_rows(
            session.execute(delete(NotesReportRecord).where(NotesReportRecord.owner_id == owner_id))
        )
        borradas += affected_rows(
            session.execute(
                delete(StudySessionRecord).where(StudySessionRecord.owner_id == owner_id)
            )
        )
        return borradas

    # ---------------------------------------------------------------------- sesiones

    def create_session(
        self,
        *,
        account_id: str,
        owner_id: str,
        token_hash: str,
        now: datetime,
        expires_at: datetime,
    ) -> str:
        with self._session_factory() as session:
            fila = AccountSessionRecord(
                id=str(uuid4()),
                account_id=account_id,
                token_hash=token_hash,
                owner_id=owner_id,
                created_at=now,
                last_seen_at=now,
                expires_at=expires_at,
                revoked_at=None,
            )
            session.add(fila)
            session.commit()
            return fila.id

    def live_session(self, token_hash: str, *, now: datetime) -> tuple[Account, str] | None:
        """La cuenta de una sesión viva, con el identificador de la sesión.

        «Viva» quiere decir tres cosas a la vez: existe, no se ha cerrado y no ha caducado. Las
        tres se comprueban en la consulta y no en el código que la llama: una sesión caducada que se
        colara
        sería una puerta abierta para siempre.
        """
        with self._session_factory() as session:
            fila = session.execute(
                select(AccountSessionRecord, AccountRecord)
                .join(AccountRecord, AccountRecord.id == AccountSessionRecord.account_id)
                .where(
                    AccountSessionRecord.token_hash == token_hash,
                    AccountSessionRecord.revoked_at.is_(None),
                    AccountSessionRecord.expires_at > now,
                )
            ).first()
        if fila is None:
            return None
        sesion, cuenta = fila
        return _account(cuenta), sesion.id

    def touch_session(self, session_id: str, *, now: datetime, expires_at: datetime) -> None:
        """Marca la sesión como usada y **alarga** su caducidad.

        Alargarla es lo que hace que quien estudia todos los días no tenga que volver a entrar; y no
        alargarla sería una sesión que caduca mientras se usa, que es peor que no tenerla.
        """
        with self._session_factory() as session:
            fila = session.get(AccountSessionRecord, session_id)
            if fila is None:
                return
            fila.last_seen_at = now
            fila.expires_at = expires_at
            session.commit()

    def revoke_session(self, session_id: str, *, now: datetime) -> bool:
        with self._session_factory() as session:
            fila = session.get(AccountSessionRecord, session_id)
            if fila is None:
                return False
            fila.revoked_at = now
            session.commit()
        return True

    def sessions_for(self, account_id: str, *, now: datetime, current_id: str) -> list[SessionView]:
        """Las sesiones vivas de una cuenta, la de ahora marcada.

        Se marca cuál es la de esta petición para que la pantalla pueda decir «esta eres tú» y no
        ofrecer cerrarla: cerrar la sesión que se está usando desde la lista de sesiones es una
        forma de dejar a alguien fuera de su propia cuenta sin querer.
        """
        with self._session_factory() as session:
            filas = (
                session.execute(
                    select(AccountSessionRecord)
                    .where(
                        AccountSessionRecord.account_id == account_id,
                        AccountSessionRecord.revoked_at.is_(None),
                        AccountSessionRecord.expires_at > now,
                    )
                    .order_by(AccountSessionRecord.last_seen_at.desc())
                )
                .scalars()
                .all()
            )
        return [
            SessionView(
                id=fila.id,
                created_at=fila.created_at,
                last_seen_at=fila.last_seen_at,
                expires_at=fila.expires_at,
                current=fila.id == current_id,
            )
            for fila in filas
        ]

    def revoke_all_sessions(self, account_id: str, *, now: datetime) -> int:
        """Cierra **todas** las sesiones de una cuenta. Se hace al cambiar la contraseña.

        Es lo que convierte «he cambiado la contraseña» en «y ya no hay nadie dentro con la vieja»:
        sin esto, quien hubiera entrado antes seguiría dentro con la sesión abierta, y el cambio de
        contraseña no serviría para echarlo.
        """
        with self._session_factory() as session:
            cerradas = affected_rows(
                session.execute(
                    update(AccountSessionRecord)
                    .where(
                        AccountSessionRecord.account_id == account_id,
                        AccountSessionRecord.revoked_at.is_(None),
                    )
                    .values(revoked_at=now)
                )
            )
            session.commit()
        return cerradas

    def purge_expired_sessions(self, *, now: datetime) -> int:
        """Borra las sesiones caducadas o cerradas.

        Es lo que hace verdad el «treinta días» del inventario de datos: sin esto, la frase sería
        una promesa sobre filas que nadie borra nunca.
        """
        with self._session_factory() as session:
            borradas = affected_rows(
                session.execute(
                    delete(AccountSessionRecord).where(
                        (AccountSessionRecord.expires_at <= now)
                        | (AccountSessionRecord.revoked_at.is_not(None))
                    )
                )
            )
            session.commit()
        return borradas

    # ------------------------------------------------------------------ recuperación

    def create_reset(
        self,
        *,
        account_id: str,
        token_hash: str,
        now: datetime,
        expires_at: datetime,
    ) -> str:
        with self._session_factory() as session:
            fila = PasswordResetRecord(
                id=str(uuid4()),
                account_id=account_id,
                token_hash=token_hash,
                created_at=now,
                expires_at=expires_at,
                used_at=None,
            )
            session.add(fila)
            session.commit()
            return fila.id

    def live_reset(self, token_hash: str, *, now: datetime) -> tuple[Account, str] | None:
        with self._session_factory() as session:
            fila = session.execute(
                select(PasswordResetRecord, AccountRecord)
                .join(AccountRecord, AccountRecord.id == PasswordResetRecord.account_id)
                .where(
                    PasswordResetRecord.token_hash == token_hash,
                    PasswordResetRecord.used_at.is_(None),
                    PasswordResetRecord.expires_at > now,
                )
            ).first()
        if fila is None:
            return None
        reset, cuenta = fila
        return _account(cuenta), reset.id

    def mark_reset_used(self, reset_id: str, *, now: datetime) -> None:
        with self._session_factory() as session:
            fila = session.get(PasswordResetRecord, reset_id)
            if fila is None:
                return
            fila.used_at = now
            session.commit()

    def purge_expired_resets(self, *, now: datetime) -> int:
        with self._session_factory() as session:
            borrados = affected_rows(
                session.execute(
                    delete(PasswordResetRecord).where(
                        (PasswordResetRecord.expires_at <= now)
                        | (PasswordResetRecord.used_at.is_not(None))
                    )
                )
            )
            session.commit()
        return borrados

    # ------------------------------------------------------------------------ freno

    def throttle(self, key_hash: str) -> ThrottleState:
        with self._session_factory() as session:
            fila = session.get(LoginThrottleRecord, key_hash)
        if fila is None:
            return ThrottleState()
        return ThrottleState(
            failures=fila.failures,
            window_started_at=fila.window_started_at,
            locked_until=fila.locked_until,
        )

    def save_throttle(self, key_hash: str, state: ThrottleState, *, now: datetime) -> None:
        with self._session_factory() as session:
            fila = session.get(LoginThrottleRecord, key_hash)
            if fila is None:
                session.add(
                    LoginThrottleRecord(
                        key_hash=key_hash,
                        failures=state.failures,
                        window_started_at=state.window_started_at or now,
                        locked_until=state.locked_until,
                    )
                )
            else:
                fila.failures = state.failures
                fila.window_started_at = state.window_started_at or fila.window_started_at
                fila.locked_until = state.locked_until
            session.commit()

    def clear_throttle(self, key_hash: str) -> None:
        """Un acceso correcto **borra la fila**: no queda ni el rastro de que se falló.

        Es lo que hace que el plazo declarado («quince minutos, y se borra al acertar») sea verdad y
        no una forma de hablar.
        """
        with self._session_factory() as session:
            session.execute(
                delete(LoginThrottleRecord).where(LoginThrottleRecord.key_hash == key_hash)
            )
            session.commit()

    def purge_stale_throttles(self, *, now: datetime, before: datetime) -> int:
        with self._session_factory() as session:
            borradas = affected_rows(
                session.execute(
                    delete(LoginThrottleRecord).where(
                        LoginThrottleRecord.window_started_at < before,
                        (LoginThrottleRecord.locked_until.is_(None))
                        | (LoginThrottleRecord.locked_until <= now),
                    )
                )
            )
            session.commit()
        return borradas

    # --------------------------------------------------------------- consentimiento

    def record_consent(
        self,
        *,
        now: datetime,
        policy_version: int,
        analytics: bool,
        preferences: bool,
    ) -> str:
        with self._session_factory() as session:
            fila = ConsentRecordRecord(
                id=str(uuid4()),
                decided_at=now,
                policy_version=policy_version,
                analytics=analytics,
                preferences=preferences,
            )
            session.add(fila)
            session.commit()
            return fila.id

    def consent_summary(self) -> ConsentSummary:
        with self._session_factory() as session:
            total = session.execute(
                select(func.count()).select_from(ConsentRecordRecord)
            ).scalar_one()
            con_analitica = session.execute(
                select(func.count())
                .select_from(ConsentRecordRecord)
                .where(ConsentRecordRecord.analytics.is_(True))
            ).scalar_one()
            con_preferencias = session.execute(
                select(func.count())
                .select_from(ConsentRecordRecord)
                .where(ConsentRecordRecord.preferences.is_(True))
            ).scalar_one()
            desde = session.execute(select(func.min(ConsentRecordRecord.decided_at))).scalar_one()
            version = session.execute(
                select(func.max(ConsentRecordRecord.policy_version))
            ).scalar_one()
        return ConsentSummary(
            total=int(total or 0),
            with_analytics=int(con_analitica or 0),
            with_preferences=int(con_preferencias or 0),
            policy_version=int(version or 0),
            since=desde,
        )

    # ---------------------------------------------------------------------- limpieza

    def counts(self) -> dict[str, int]:
        """Cuántas filas hay en cada tabla nueva.

        Lo usa la prueba que comprueba que con las banderas apagadas **no se escribe ni una fila**:
        una función apagada que ya ha dejado datos es una función encendida a medias.
        """
        with self._session_factory() as session:
            return {
                "accounts": int(
                    session.execute(select(func.count()).select_from(AccountRecord)).scalar_one()
                    or 0
                ),
                "account_sessions": int(
                    session.execute(
                        select(func.count()).select_from(AccountSessionRecord)
                    ).scalar_one()
                    or 0
                ),
                "password_resets": int(
                    session.execute(
                        select(func.count()).select_from(PasswordResetRecord)
                    ).scalar_one()
                    or 0
                ),
                "login_throttles": int(
                    session.execute(
                        select(func.count()).select_from(LoginThrottleRecord)
                    ).scalar_one()
                    or 0
                ),
                "consent_records": int(
                    session.execute(
                        select(func.count()).select_from(ConsentRecordRecord)
                    ).scalar_one()
                    or 0
                ),
                "analytics_events": int(
                    session.execute(
                        select(func.count()).select_from(AnalyticsEventRecord)
                    ).scalar_one()
                    or 0
                ),
            }


__all__ = ["ACCOUNT_OBJECT_TYPE", "SqlAlchemyAccountRepository"]
