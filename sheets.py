# -*- coding: utf-8 -*-
"""Google Sheets persistence layer for FlipFlow.

Gracefully degrades to no-ops if credentials are not configured.
Configure by adding to .streamlit/secrets.toml:

    [gcp_service_account]
    type = "service_account"
    project_id = "..."
    private_key_id = "..."
    private_key = "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n"
    client_email = "..."
    client_id = "..."
    auth_uri = "https://accounts.google.com/o/oauth2/auth"
    token_uri = "https://oauth2.googleapis.com/token"
    auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
    client_x509_cert_url = "..."

    [flipflow]
    sheet_id = "your-google-sheet-id"
    worksheet = "items"   # optional, defaults to "items"

Share the sheet with the service-account `client_email` as Editor.
"""

from __future__ import annotations

import streamlit as st

HEADERS = [
    "id", "item_name", "actual_cost", "suggested_price", "est_profit", "margin_pct",
    "status", "sell_price", "real_profit", "fb_title", "fb_description",
    "condition", "market_score", "notes", "created_at",
]


@st.cache_resource(show_spinner=False)
def _get_worksheet():
    """Return a gspread Worksheet, or None if not configured / unavailable."""
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except Exception:
        return None

    try:
        sa_info = st.secrets["gcp_service_account"]
        sheet_id = st.secrets["flipflow"]["sheet_id"]
        worksheet_name = st.secrets["flipflow"].get("worksheet", "items")
    except Exception:
        return None

    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_info(dict(sa_info), scopes=scopes)
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(sheet_id)
        try:
            ws = sh.worksheet(worksheet_name)
        except Exception:
            ws = sh.add_worksheet(title=worksheet_name, rows=1000, cols=len(HEADERS))
            ws.append_row(HEADERS)
        existing = ws.row_values(1)
        if existing != HEADERS:
            if not existing:
                ws.append_row(HEADERS)
            else:
                ws.update("A1", [HEADERS])
        return ws
    except Exception:
        return None


def sheets_available() -> bool:
    return _get_worksheet() is not None


def _row_from_item(item: dict) -> list:
    return [str(item.get(h, "")) for h in HEADERS]


def _item_from_row(row: dict) -> dict:
    return {h: row.get(h, "") for h in HEADERS}


def load_from_sheets() -> list[dict]:
    ws = _get_worksheet()
    if ws is None:
        return []
    try:
        rows = ws.get_all_records()
        return [_item_from_row(r) for r in rows if r.get("id")]
    except Exception:
        return []


def save_item_to_sheets(item: dict) -> bool:
    ws = _get_worksheet()
    if ws is None:
        return False
    try:
        ws.append_row(_row_from_item(item), value_input_option="USER_ENTERED")
        return True
    except Exception:
        return False


def update_item_in_sheets(item: dict) -> bool:
    ws = _get_worksheet()
    if ws is None or not item.get("id"):
        return False
    try:
        cell = ws.find(str(item["id"]))
        if not cell:
            return save_item_to_sheets(item)
        ws.update(f"A{cell.row}", [_row_from_item(item)])
        return True
    except Exception:
        return False


def delete_item_from_sheets(item_id: str) -> bool:
    ws = _get_worksheet()
    if ws is None or not item_id:
        return False
    try:
        cell = ws.find(str(item_id))
        if cell:
            ws.delete_rows(cell.row)
            return True
    except Exception:
        pass
    return False
