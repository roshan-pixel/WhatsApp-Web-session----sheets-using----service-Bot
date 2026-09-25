"""
Client for interacting with real browser sessions via Kimi WebBridge.
Handles tab borrowing, carousel navigation, center-distance image detection,
and zero-taint HTML5 canvas frame extraction.
"""
import base64
import json
import logging
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests

from config import (
    IMAGES_DIR,
    SESSION_NAME,
    WEBBRIDGE_DAEMON_URL,
    WEBBRIDGE_STATUS_URL,
    WHATSAPP_WEB_URL,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class WebBridgeClient:
    def __init__(self, daemon_url: str = WEBBRIDGE_DAEMON_URL, session: str = SESSION_NAME):
        self.daemon_url = daemon_url
        self.session = session

    def check_daemon_status(self) -> Dict[str, Any]:
        """Check if WebBridge daemon is running and extension is connected."""
        try:
            resp = requests.get(WEBBRIDGE_STATUS_URL, timeout=5)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            logger.warning(f"Daemon check failed: {e}")
        return {"running": False, "extension_connected": False}

    def ensure_daemon(self) -> bool:
        """Silently auto-start the daemon if not running."""
        status = self.check_daemon_status()
        if status.get("running") and status.get("extension_connected"):
            return True

        logger.info("Starting Kimi WebBridge daemon...")
        try:
            daemon_bin = Path.home() / ".kimi-webbridge" / "bin" / "kimi-webbridge.exe"
            if daemon_bin.exists():
                subprocess.run([str(daemon_bin), "start"], check=False, capture_output=True)
                time.sleep(1.5)
                status = self.check_daemon_status()
                return bool(status.get("running") and status.get("extension_connected"))
        except Exception as e:
            logger.error(f"Failed to start daemon: {e}")
        return False

    def send_cmd(self, action: str, args: Dict[str, Any]) -> Any:
        """Send an action command to the WebBridge daemon."""
        payload = {
            "action": action,
            "args": args,
            "session": self.session
        }
        resp = requests.post(self.daemon_url, json=payload, timeout=25)
        data = resp.json()
        if not data.get("ok"):
            err = data.get("error", {})
            raise RuntimeError(f"WebBridge action '{action}' failed: {err.get('message', data)}")
        return data.get("data")

    def borrow_active_tab(self, url: str = WHATSAPP_WEB_URL) -> Dict[str, Any]:
        """
        Borrow the foreground WhatsApp tab from the user's browser.
        Matches the hostname (e.g. web.whatsapp.com).
        """
        logger.info(f"Borrowing active tab matching: {url}")
        return self.send_cmd("find_tab", {"url": url, "active": True})

    def evaluate_js(self, code: str) -> Any:
        """Run JavaScript in the context of the active tab page."""
        res = self.send_cmd("evaluate", {"code": code})
        val = res.get("value")
        if isinstance(val, str) and (val.startswith("{") or val.startswith("[")):
            try:
                return json.loads(val)
            except json.JSONDecodeError:
                pass
        return val

    def get_current_header(self) -> str:
        """Extract the timestamp/date header text from the top-left viewer bar."""
        code = """(() => {
            const headerEl = Array.from(document.querySelectorAll('div, span')).find(
                el => el.innerText && /\\d{1,2}\\/\\d{1,2}\\/\\d{4}/.test(el.innerText) && el.children.length === 0
            );
            return headerEl ? headerEl.innerText.trim() : '';
        })()"""
        return self.evaluate_js(code) or ""

    def extract_active_slide(self) -> Optional[Dict[str, Any]]:
        """
        Extract the image from the currently active slide in the viewer.
        
        Uses the Center-Distance algorithm:
        In carousel components like WhatsApp Web, virtual slides remain in the DOM.
        Sorting candidate images by minimum absolute distance from the horizontal
        center of the viewport:
            abs((rect.left + rect.width / 2) - window.innerWidth / 2)
        guarantees selection of the true active slide regardless of aspect ratio.
        
        The image is drawn to an offscreen HTML5 canvas and exported as base64 PNG,
        preserving full natural resolution without screenshot distortion.
        """
        code = """(() => {
            const centerScreenX = window.innerWidth / 2;
            const imgs = Array.from(document.querySelectorAll('img')).filter(img => {
                const r = img.getBoundingClientRect();
                return r.top < 700 && r.height > 50 && r.width > 50 && img.naturalWidth > 100;
            });
            if (!imgs.length) return JSON.stringify({ error: 'no candidate image found' });

            imgs.sort((a, b) => {
                const ra = a.getBoundingClientRect();
                const rb = b.getBoundingClientRect();
                const distA = Math.abs((ra.left + ra.width / 2) - centerScreenX);
                const distB = Math.abs((rb.left + rb.width / 2) - centerScreenX);
                return distA - distB;
            });

            const active = imgs[0];
            const canvas = document.createElement('canvas');
            canvas.width = active.naturalWidth;
            canvas.height = active.naturalHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(active, 0, 0);

            const nextBtn = document.querySelector('button[aria-label="Next"]');
            const prevBtn = document.querySelector('button[aria-label="Previous"]');
            const headerEl = Array.from(document.querySelectorAll('div, span')).find(
                el => el.innerText && /\\d{1,2}\\/\\d{1,2}\\/\\d{4}/.test(el.innerText) && el.children.length === 0
            );

            return JSON.stringify({
                src: active.src,
                naturalWidth: active.naturalWidth,
                naturalHeight: active.naturalHeight,
                header: headerEl ? headerEl.innerText.trim() : '',
                hasNext: !!nextBtn,
                nextDisabled: nextBtn ? (nextBtn.disabled || nextBtn.getAttribute('aria-disabled') === 'true') : true,
                hasPrev: !!prevBtn,
                prevDisabled: prevBtn ? (prevBtn.disabled || prevBtn.getAttribute('aria-disabled') === 'true') : true,
                dataUrl: canvas.toDataURL('image/png')
            });
        })()"""
        return self.evaluate_js(code)

    def click_next(self) -> bool:
        """Click the 'Next' button to advance the gallery rightward."""
        code = """(() => {
            const nextBtn = document.querySelector('button[aria-label="Next"]');
            if (nextBtn && !nextBtn.disabled && nextBtn.getAttribute('aria-disabled') !== 'true') {
                nextBtn.click();
                return true;
            }
            return false;
        })()"""
        return bool(self.evaluate_js(code))

    def click_previous(self) -> bool:
        """Click the 'Previous' button to navigate backwards."""
        code = """(() => {
            const prevBtn = document.querySelector('button[aria-label="Previous"]');
            if (prevBtn && !prevBtn.disabled && prevBtn.getAttribute('aria-disabled') !== 'true') {
                prevBtn.click();
                return true;
            }
            return false;
        })()"""
        return bool(self.evaluate_js(code))

    def scrape_gallery_forward(self, output_dir: Path = IMAGES_DIR, max_items: int = 150) -> List[Dict[str, Any]]:
        """
        Scroll through all open transactions to the rightmost end.
        Saves each full-resolution transaction slide to disk and records metadata.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        collected = []
        idx = 0

        logger.info(f"Starting gallery scan to the right (max {max_items} slides)...")

        while idx < max_items:
            state = self.extract_active_slide()
            if not state or "error" in state:
                logger.error(f"Failed to extract slide at index {idx}: {state}")
                break

            current_src = state["src"]
            header = state["header"]
            has_next = state["hasNext"]
            next_disabled = state["nextDisabled"]

            # Save base64 image to disk
            _, encoded = state["dataUrl"].split(",", 1)
            img_bytes = base64.b64decode(encoded)
            filename = f"tx_{idx}.png"
            filepath = output_dir / filename
            with open(filepath, "wb") as f:
                f.write(img_bytes)

            entry = {
                "index": idx,
                "filename": filename,
                "path": str(filepath),
                "header": header,
                "src": current_src,
                "width": state["naturalWidth"],
                "height": state["naturalHeight"]
            }
            collected.append(entry)
            logger.info(f"[{idx:02d}] Saved {filename} ({state['naturalWidth']}x{state['naturalHeight']}) | {header}")

            if not has_next or next_disabled:
                logger.info("Reached end of gallery: Next button is disabled or missing.")
                break

            # Click next
            if not self.click_next():
                logger.info("Cannot click Next. Reached boundary.")
                break

            # Settle and wait for transition
            changed = False
            for attempt in range(25):
                time.sleep(0.3)
                check_code = """(() => {
                    const centerScreenX = window.innerWidth / 2;
                    const imgs = Array.from(document.querySelectorAll('img')).filter(img => {
                        const r = img.getBoundingClientRect();
                        return r.top < 700 && r.height > 50 && r.width > 50 && img.naturalWidth > 100;
                    });
                    imgs.sort((a, b) => {
                        const ra = a.getBoundingClientRect();
                        const rb = b.getBoundingClientRect();
                        return Math.abs((ra.left + ra.width / 2) - centerScreenX) - Math.abs((rb.left + rb.width / 2) - centerScreenX);
                    });
                    return imgs[0] ? imgs[0].src : '';
                })()"""
                new_src = self.evaluate_js(check_code)
                if new_src and new_src != current_src:
                    changed = True
                    time.sleep(0.3)
                    break
                if attempt == 10:
                    self.click_next()

            if not changed:
                logger.info(f"Slide did not change after clicking Next at index {idx}. Reached end.")
                break

            idx += 1

        meta_file = output_dir / "metadata.json"
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(collected, f, indent=2)

        logger.info(f"Scrape completed! Total slides collected: {len(collected)}")
        return collected
