import asyncio
import logging
from datetime import date, datetime
from decimal import Decimal

import gspread
from gspread.utils import rowcol_to_a1
from sqlalchemy import text

from bot.config import settings
from bot.db.base import async_session

logger = logging.getLogger(__name__)

VIEW_NAME = "v_tableau_daily_journal"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def _clean(value):
    """Приводить значення з Postgres до того, що приймає Google Sheets."""
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, (list, tuple)):
        value = ", ".join(str(v) for v in value)
    if isinstance(value, str) and value[:1] in ("=", "+", "-", "@"):
        return "'" + value  # щоб текст не став формулою
    return value


async def fetch_journal_rows() -> tuple[list, list]:
    """Читає View з бази (з відсіканням за датою). У таблицю нічого не пише."""
    query = f"SELECT * FROM {VIEW_NAME}"
    params = {}
    if settings.google_sync_until:
        query += " WHERE checkin_date <= :until"
        params["until"] = date.fromisoformat(settings.google_sync_until)
    query += " ORDER BY checkin_date"

    async with async_session() as session:
        result = await session.execute(text(query), params)
        header = list(result.keys())
        rows = [[_clean(v) for v in row] for row in result.fetchall()]
    return header, rows


def _write_sheet(header: list, rows: list) -> None:
    """Синхронна частина (gspread не async): записує дані й прибирає залишки."""
    gc = gspread.service_account(filename=settings.google_credentials_path, scopes=SCOPES)
    ws = gc.open_by_key(settings.google_sheet_id).worksheet(settings.google_sheet_tab)

    values = [header] + rows
    n_rows, n_cols = len(values), len(header)

    # 1) спочатку записуємо нові дані поверх старих
    ws.update(range_name="A1", values=values, value_input_option="USER_ENTERED")

    # 2) потім прибираємо старі рядки внизу й колонки праворуч, якщо їх стало менше
    if ws.row_count > n_rows:
        ws.batch_clear([f"A{n_rows + 1}:{rowcol_to_a1(ws.row_count, ws.col_count)}"])
    if ws.col_count > n_cols:
        ws.batch_clear([f"{rowcol_to_a1(1, n_cols + 1)}:{rowcol_to_a1(ws.row_count, ws.col_count)}"])


async def sync_journal_to_sheets() -> int:
    """Оновлює вкладку в Google Sheets даними з бази. Повертає кількість днів."""
    if not settings.google_credentials_path or not settings.google_sheet_id:
        raise RuntimeError("Google Sheets не налаштовано в .env")

    header, rows = await fetch_journal_rows()
    await asyncio.to_thread(_write_sheet, header, rows)
    logger.info("Google Sheets оновлено: %s рядків", len(rows))
    return len(rows)