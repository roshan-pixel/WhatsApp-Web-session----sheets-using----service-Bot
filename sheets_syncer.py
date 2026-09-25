"""
Google Sheets Synchronizer using Service Account credentials.
Updates target spreadsheets with parsed transaction records following a specific checkpoint UTR.
"""
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import gspread
from google.oauth2.service_account import Credentials

from config import (
    DEFAULT_CHECKPOINT_UTR,
    GOOGLE_CREDS_FILE,
    SPREADSHEET_ID,
    SPREADSHEET_NAME,
    WORKSHEET_NAME,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


class SheetsSyncer:
    def __init__(
        self,
        creds_path: str = GOOGLE_CREDS_FILE,
        spreadsheet_id: str = SPREADSHEET_ID,
        spreadsheet_name: str = SPREADSHEET_NAME,
        worksheet_name: str = WORKSHEET_NAME
    ):
        self.creds_path = Path(creds_path)
        self.spreadsheet_id = spreadsheet_id
        self.spreadsheet_name = spreadsheet_name
        self.worksheet_name = worksheet_name
        self.client: Optional[gspread.Client] = None
        self.sheet: Optional[gspread.Spreadsheet] = None
        self.ws: Optional[gspread.Worksheet] = None

    def connect(self) -> None:
        """Authenticate using Service Account JSON and open target worksheet."""
        if not self.creds_path.exists():
            raise FileNotFoundError(f"Service account file not found at: {self.creds_path}")

        logger.info(f"Authenticating with service account credentials from {self.creds_path}...")
        creds = Credentials.from_service_account_file(str(self.creds_path), scopes=SCOPES)
        self.client = gspread.authorize(creds)

        try:
            if self.spreadsheet_id:
                self.sheet = self.client.open_by_key(self.spreadsheet_id)
            else:
                self.sheet = self.client.open(self.spreadsheet_name.strip())
            logger.info(f"Connected to Spreadsheet: '{self.sheet.title}' (ID: {self.sheet.id})")
        except Exception as e:
            logger.error(f"Failed to open spreadsheet: {e}")
            raise

        try:
            self.ws = self.sheet.worksheet(self.worksheet_name)
        except gspread.WorksheetNotFound:
            self.ws = self.sheet.sheet1
        logger.info(f"Active worksheet: '{self.ws.title}'")

    def find_checkpoint_row(self, checkpoint_utr: str = DEFAULT_CHECKPOINT_UTR) -> int:
        """
        Locate the 1-indexed row number containing the checkpoint UTR.
        Returns the row index where this UTR is found, or the last non-empty row if not found.
        """
        all_values = self.ws.get_all_values()
        for row_idx, row in enumerate(all_values):
            for cell in row:
                if checkpoint_utr in cell:
                    logger.info(f"Found checkpoint UTR '{checkpoint_utr}' at Row {row_idx + 1}")
                    return row_idx + 1

        # Fallback to last populated row
        for row_idx in range(len(all_values) - 1, -1, -1):
            if any(cell.strip() for cell in all_values[row_idx]):
                logger.info(f"Checkpoint UTR not found. Appending after last row {row_idx + 1}")
                return row_idx + 1
        return len(all_values)

    def sync_transactions_after_utr(
        self,
        transactions: List[Dict[str, Any]],
        checkpoint_utr: str = DEFAULT_CHECKPOINT_UTR
    ) -> int:
        """
        Filters transactions to only those following the checkpoint UTR,
        and batch writes them to the sheet in format:
        [Amount, Date, To Banking Name, Reference Name, UTR No]
        """
        if not self.ws:
            self.connect()

        # Locate checkpoint in our list
        start_idx = 0
        found_checkpoint = False
        for i, tx in enumerate(transactions):
            if tx.get("utr") == checkpoint_utr:
                start_idx = i + 1
                found_checkpoint = True
                break

        records_to_add = transactions[start_idx:] if found_checkpoint else transactions
        if not records_to_add:
            logger.info(f"No new transactions found after UTR {checkpoint_utr}.")
            return 0

        logger.info(f"Preparing to insert {len(records_to_add)} transactions...")

        # Format rows for HISSAB KITAB:
        # Col A: Amount, Col B: Date, Col C: To Banking Name, Col D: Reference Name, Col E: UTR No
        rows_to_insert = []
        for tx in records_to_add:
            amt_str = str(tx.get("amount", "")).replace("₹", "").replace(",", "").strip()
            date_str = str(tx.get("date", "")).strip()
            to_name = str(tx.get("to_name", "DSR 7 WELLNESS CENTRE")).strip()
            ref_name = str(tx.get("reference_name") or tx.get("for_person") or "").strip()
            utr_no = str(tx.get("utr", "")).strip()

            rows_to_insert.append([amt_str, date_str, to_name, ref_name, utr_no])

        checkpoint_row = self.find_checkpoint_row(checkpoint_utr)
        start_row = checkpoint_row + 1
        
        # Check if downstream row is already populated (e.g. CASH, totals, or formulas)
        existing_downstream = self.ws.row_values(start_row)
        if any(cell.strip() for cell in existing_downstream):
            logger.info(f"Downstream row {start_row} already contains data. Inserting {len(rows_to_insert)} rows to preserve formulas/summary...")
            self.ws.insert_rows(
                rows_to_insert,
                row=start_row,
                value_input_option="USER_ENTERED",
                inherit_from_before=True
            )
        else:
            end_row = start_row + len(rows_to_insert) - 1
            cell_range = f"A{start_row}:E{end_row}"
            logger.info(f"Batch updating range {cell_range}...")
            self.ws.update(
                range_name=cell_range,
                values=rows_to_insert,
                value_input_option="USER_ENTERED"
            )
        logger.info(f"Successfully synced {len(rows_to_insert)} rows to Google Sheets!")
        return len(rows_to_insert)
