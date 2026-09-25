"""
Parser module for extracting UPI/Google Pay transaction fields from OCR outputs.
Extracts: UTR No, Date, To Banking Name, Reference Name, Amount.
"""
import logging
import re
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class TransactionParser:
    @staticmethod
    def parse_utr(text: str) -> str:
        """Extract 12-digit UPI transaction reference ID."""
        upi_match = re.search(r'(?:UPI transaction ID|UPI Ref(?:erence)?(?: No)?\.?)\s*([0-9]{10,14})', text, re.IGNORECASE)
        if upi_match:
            return upi_match.group(1).strip()
        twelve_digits = re.findall(r'\b[0-9]{12}\b', text)
        return twelve_digits[0] if twelve_digits else ""

    @staticmethod
    def parse_date(text: str, fallback_header: str = "") -> str:
        """Extract transaction date and time."""
        date_match = re.search(
            r'([0-9]{1,2})\s+([A-Za-z]{3,9})\s+([0-9]{4})[,\s]+([0-9]{1,2}):([0-9]{2})\s*(am|pm)?',
            text,
            re.IGNORECASE
        )
        if date_match:
            day, month, year, hour, minute, ampm = date_match.groups()
            ampm = ampm.lower() if ampm else "pm"
            hour = int(hour)
            return f"{int(day):02d} {month.capitalize()} {year} {hour:02d}:{minute} {ampm}"
        return fallback_header.replace(" at ", " ") if fallback_header else ""

    @staticmethod
    def parse_to_name(text: str) -> str:
        """Extract beneficiary/merchant name."""
        if "DSR 7 WELLNESS CENTRE" in text:
            return "DSR 7 WELLNESS CENTRE"
        to_match = re.search(r'To:\s*([^\n\r]+)', text)
        if to_match:
            candidate = to_match.group(1)
            candidate = re.split(r'(\.{2,}|@|[0-9]{2,}-|PhonePe|Google Pay)', candidate)[0].strip()
            if candidate:
                return candidate
        to_match2 = re.search(r'To\s+([A-Z0-9\s]{4,30})(?:Pay again|Completed|\n|\r)', text)
        if to_match2:
            return to_match2.group(1).strip()
        return "DSR 7 WELLNESS CENTRE"

    @staticmethod
    def parse_reference_name(lines: List[str], text: str) -> str:
        """Extract the specific customer / payer reference name."""
        # Check in line right above 'Pay again'
        for i, line in enumerate(lines):
            if "pay again" in line.lower() and i > 0:
                sub = lines[i - 1].strip()
                if not re.match(r'^[0-9,.\s₹M\?]+$', sub):
                    return sub
                elif i > 1:
                    return lines[i - 2].strip()

        # From: NAME
        from_match = re.search(r'From:\s*([^\n\r(]+)', text)
        if from_match:
            return from_match.group(1).strip()
        return ""

    @staticmethod
    def parse_amount(text: str, lines: List[str]) -> Optional[float]:
        """Extract transaction amount as float."""
        # Rupee symbol or M/? variants in OCR
        amt_match = re.search(r'[₹M\?]\s*([0-9,]+(?:\.[0-9]{2})?)', text)
        if amt_match:
            try:
                clean_num = amt_match.group(1).replace(",", "")
                return float(clean_num)
            except ValueError:
                pass

        # Check line right under 'To ...'
        for i, line in enumerate(lines):
            if line.strip().startswith("To ") and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                clean = re.sub(r'^[₹M\?,\s]+', '', next_line).replace(",", "")
                try:
                    return float(clean)
                except ValueError:
                    pass
        return None

    @classmethod
    def parse_record(cls, ocr_data: Dict[str, Any], meta: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Parse a full transaction screenshot record."""
        text = ocr_data.get("text", "")
        lines = ocr_data.get("lines", [])
        meta = meta or {}

        utr = cls.parse_utr(text)
        if not utr:
            # Skip non-receipt slides (e.g. invoice summary slips without UTR)
            return None

        date = cls.parse_date(text, meta.get("header", ""))
        to_name = cls.parse_to_name(text)
        ref_name = cls.parse_reference_name(lines, text)
        amt = cls.parse_amount(text, lines)
        if amt is None:
            img_path_str = ocr_data.get("image_path") or (meta.get("image_path") if meta else None)
            if img_path_str and Path(img_path_str).exists():
                try:
                    from ocr_engine import WinRTOcrEngine
                    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                        crop_tmp = Path(tmp.name)
                    WinRTOcrEngine.crop_amount_region(Path(img_path_str), crop_tmp)
                    crop_ocr = WinRTOcrEngine.recognize_single(crop_tmp)
                    crop_tmp.unlink(missing_ok=True)
                    for cl in crop_ocr.get("lines", []):
                        clean = re.sub(r'^[₹M\?,\s]+', '', cl).replace(",", "").strip()
                        try:
                            amt = float(clean)
                            break
                        except ValueError:
                            pass
                except Exception as e:
                    logger.debug(f"Crop amount fallback skipped: {e}")

        return {
            "index": ocr_data.get("index"),
            "filename": ocr_data.get("filename"),
            "utr": utr,
            "date": date,
            "to_name": to_name,
            "reference_name": ref_name,
            "amount": amt,
            "raw_text": text
        }
