# -*- coding: utf-8 -*-
"""
sheets.py - Google Sheets persistence layer for FlipFlow
All reads and writes to the permanent inventory sheet go through here.
"""
import streamlit as st
import json
from datetime import datetime

SHEET_NAME = "FlipFlow Inventory"
HEADERS = [
    "id", "item_name", "actual_cost", "suggested_price", "est_profit",
    "margin_pct", "status", "sell_price", "real_profit", "fb_title",
    "fb_description", "condition", "market_score", "notes", "created_at"
]

def _get_sheet():
    """Return the worksheet, creating headers if brand new."""
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        st.error("Missing packages: gspread and google-auth. Check requirements.txt.")
        st.stop()

    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        gc = gspread.authorize(creds)
    except Exception as e:
        st.error(f"Google auth failed: {e}")
        st.stop()

    try:
        sh = gc.open(SHEET_NAME)
    except Exception:
        sh = gc.create(SHEET_NAME)
        # Share with the user's email so they can see it
        try:
            email = st.secrets.get("OWNER_EMAIL", "")
            if email:
                sh.share(email, perm_type="user", role="writer")
        except Exception:
            pass

    ws = sh.sheet1

    # Bootstrap headers if empty
    existing = ws.row_values(1)
    if not existing or existing[0] != "id":
        ws.clear()
        ws.append_row(HEADERS)

    return ws


def load_from_sheets():
    """Load all inventory rows from Google Sheets."""
    try:
        ws = _get_sheet()
        records = ws.get_all_records()
        return records
    except Exception as e:
        st.warning(f"Could not load from Google Sheets: {e}")
        return []


def save_item_to_sheets(item: dict):
    """Append a new item row to Google Sheets."""
    try:
        ws = _get_sheet()
        row = [str(item.get(h, "")) for h in HEADERS]
        ws.append_row(row, value_input_option="USER_ENTERED")
        return True
    except Exception as e:
        st.warning(f"Could not save to Google Sheets: {e}")
        return False


def update_item_in_sheets(item: dict):
    """Find row by id and update it."""
    try:
        ws = _get_sheet()
        cell = ws.find(item["id"])
        if cell:
            row_num = cell.row
            row = [str(item.get(h, "")) for h in HEADERS]
            ws.update(f"A{row_num}:{chr(64+len(HEADERS))}{row_num}", [row])
        return True
    except Exception as e:
        st.warning(f"Could not update Google Sheets: {e}")
        return False


def delete_item_from_sheets(item_id: str):
    """Delete a row by id."""
    try:
        ws = _get_sheet()
        cell = ws.find(item_id)
        if cell:
            ws.delete_rows(cell.row)
        return True
    except Exception as e:
        st.warning(f"Could not delete from Google Sheets: {e}")
        return False


def sheets_available() -> bool:
    """Check if Google Sheets credentials are configured."""
    try:
        _ = st.secrets["gcp_service_account"]
        return True
    except (KeyError, FileNotFoundError):
        return False
