"""
CLI Entrypoint for WhatsApp Web Transaction Scraper & Google Sheets Synchronizer.
"""
import argparse
import json
import logging
import sys
from pathlib import Path

from config import (
    DATA_DIR,
    DEFAULT_CHECKPOINT_UTR,
    GOOGLE_CREDS_FILE,
    IMAGES_DIR,
    SPREADSHEET_ID,
)
from ocr_engine import WinRTOcrEngine
from parser import TransactionParser
from sheets_syncer import SheetsSyncer
from webbridge_client import WebBridgeClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def run_scrape(args):
    client = WebBridgeClient()
    if not client.ensure_daemon():
        logger.error("Failed to connect to Kimi WebBridge daemon.")
        sys.exit(1)

    try:
        client.borrow_active_tab()
    except Exception as e:
        logger.warning(f"Active tab borrow returned: {e}. Ensure WhatsApp Web is in the foreground.")

    output_dir = Path(args.output_dir) if args.output_dir else IMAGES_DIR
    slides = client.scrape_gallery_forward(output_dir=output_dir, max_items=args.max_items)
    print(f"\n[+] Successfully scraped {len(slides)} slides into {output_dir}")


def run_ocr(args):
    images_dir = Path(args.images_dir) if args.images_dir else IMAGES_DIR
    output_json = DATA_DIR / "ocr_results.json"
    results = WinRTOcrEngine.recognize_batch(images_dir, output_json)
    print(f"\n[+] Successfully OCR'd {len(results)} images. Saved to {output_json}")


def run_parse(args):
    ocr_file = DATA_DIR / "ocr_results.json"
    if not ocr_file.exists():
        logger.error(f"OCR results file not found at {ocr_file}. Run 'ocr' first.")
        sys.exit(1)

    with open(ocr_file, "r", encoding="utf-8-sig") as f:
        ocr_data = json.load(f)

    meta_file = IMAGES_DIR / "metadata.json"
    meta_dict = {}
    if meta_file.exists():
        with open(meta_file, "r", encoding="utf-8") as f:
            for item in json.load(f):
                meta_dict[item["index"]] = item

    transactions = []
    for item in ocr_data:
        record = TransactionParser.parse_record(item, meta_dict.get(item.get("index")))
        if record:
            transactions.append(record)

    out_file = DATA_DIR / "parsed_transactions.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(transactions, f, indent=2)

    print(f"\n[+] Parsed {len(transactions)} transaction receipts. Saved to {out_file}")


def run_sync(args):
    parsed_file = DATA_DIR / "parsed_transactions.json"
    if not parsed_file.exists():
        logger.error(f"Parsed transactions file not found at {parsed_file}. Run 'parse' first.")
        sys.exit(1)

    with open(parsed_file, "r", encoding="utf-8") as f:
        transactions = json.load(f)

    syncer = SheetsSyncer(
        creds_path=args.creds or GOOGLE_CREDS_FILE,
        spreadsheet_id=args.sheet_id or SPREADSHEET_ID
    )
    checkpoint_utr = args.checkpoint_utr or DEFAULT_CHECKPOINT_UTR
    count = syncer.sync_transactions_after_utr(transactions, checkpoint_utr=checkpoint_utr)
    print(f"\n[+] Successfully synced {count} transactions to Google Sheet after UTR {checkpoint_utr}")


def run_all(args):
    logger.info("Executing end-to-end workflow: Scrape -> OCR -> Parse -> Sync...")
    run_scrape(args)
    run_ocr(args)
    run_parse(args)
    run_sync(args)


def main():
    parser = argparse.ArgumentParser(description="WhatsApp Web Transaction Scraper & Sheets Syncer")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Scrape
    p_scrape = subparsers.add_parser("scrape", help="Scrape WhatsApp Web transaction gallery")
    p_scrape.add_argument("--output-dir", default=str(IMAGES_DIR))
    p_scrape.add_argument("--max-items", type=int, default=150)
    p_scrape.set_defaults(func=run_scrape)

    # OCR
    p_ocr = subparsers.add_parser("ocr", help="Run WinRT OCR on scraped images")
    p_ocr.add_argument("--images-dir", default=str(IMAGES_DIR))
    p_ocr.set_defaults(func=run_ocr)

    # Parse
    p_parse = subparsers.add_parser("parse", help="Parse OCR outputs into structured transactions")
    p_parse.set_defaults(func=run_parse)

    # Sync
    p_sync = subparsers.add_parser("sync", help="Sync parsed transactions to Google Sheets")
    p_sync.add_argument("--creds", default=GOOGLE_CREDS_FILE)
    p_sync.add_argument("--sheet-id", default=SPREADSHEET_ID)
    p_sync.add_argument("--checkpoint-utr", default=DEFAULT_CHECKPOINT_UTR)
    p_sync.set_defaults(func=run_sync)

    # Run-all
    p_all = subparsers.add_parser("run-all", help="Run full pipeline end-to-end")
    p_all.add_argument("--output-dir", default=str(IMAGES_DIR))
    p_all.add_argument("--max-items", type=int, default=150)
    p_all.add_argument("--images-dir", default=str(IMAGES_DIR))
    p_all.add_argument("--creds", default=GOOGLE_CREDS_FILE)
    p_all.add_argument("--sheet-id", default=SPREADSHEET_ID)
    p_all.add_argument("--checkpoint-utr", default=DEFAULT_CHECKPOINT_UTR)
    p_all.set_defaults(func=run_all)

    parsed_args = parser.parse_args()
    parsed_args.func(parsed_args)


if __name__ == "__main__":
    main()
