#!/usr/bin/env python3
"""Banana Claude -- Multi-image composite via Gemini REST API.

Sends multiple reference images + one instruction to Gemini so it can
combine real people/faces into a single new image (face-preserving).
Stdlib only, no pip deps.

Usage:
    composite.py --prompt "..." --image a.jpg --image b.jpg --image c.jpg
                 [--aspect-ratio 1:1] [--resolution 2K] [--model MODEL] [--api-key KEY]
"""

import argparse
import base64
import http.client
import json
import os
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

DEFAULT_MODEL = "gemini-3.1-flash-image-preview"
OUTPUT_DIR = Path.home() / "Documents" / "nanobanana_generated"
API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".webp": "image/webp", ".gif": "image/gif"}


def composite(images, prompt, model, api_key, aspect_ratio, resolution):
    parts = [{"text": prompt}]
    for p in images:
        path = Path(p).resolve()
        if not path.exists():
            print(json.dumps({"error": True, "message": f"Image not found: {path}"}))
            sys.exit(1)
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        parts.append({"inlineData": {"mimeType": MIME.get(path.suffix.lower(), "image/jpeg"), "data": b64}})

    body = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
            "imageConfig": {"aspectRatio": aspect_ratio, "imageSize": resolution},
        },
    }
    url = f"{API_BASE}/{model}:generateContent?key={api_key}"
    data = json.dumps(body).encode("utf-8")

    result = None
    for attempt in range(3):
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                try:
                    raw = resp.read()
                except http.client.IncompleteRead as ir:
                    # Proxy can drop the final chunk terminator; the body is usually intact.
                    raw = ir.partial
            result = json.loads(raw.decode("utf-8"))
            break
        except urllib.error.HTTPError as e:
            body_txt = e.read().decode("utf-8") if e.fp else ""
            if e.code == 429 and attempt < 2:
                wait = 2 ** (attempt + 1)
                print(json.dumps({"retry": True, "attempt": attempt + 1, "wait_seconds": wait}), file=sys.stderr)
                time.sleep(wait)
                continue
            print(json.dumps({"error": True, "status": e.code, "message": body_txt}))
            sys.exit(1)
        except urllib.error.URLError as e:
            print(json.dumps({"error": True, "message": str(e.reason)}))
            sys.exit(1)

    if result is None:
        print(json.dumps({"error": True, "message": "Max retries exceeded"}))
        sys.exit(1)

    candidates = result.get("candidates", [])
    if not candidates:
        reason = result.get("promptFeedback", {}).get("blockReason", "UNKNOWN")
        print(json.dumps({"error": True, "message": f"No candidates. Reason: {reason}"}))
        sys.exit(1)

    image_data, text_response = None, ""
    for part in candidates[0].get("content", {}).get("parts", []):
        if "inlineData" in part:
            image_data = part["inlineData"]["data"]
        elif "text" in part:
            text_response = part["text"]

    if not image_data:
        reason = candidates[0].get("finishReason", "UNKNOWN")
        print(json.dumps({"error": True, "message": f"No image in response. finishReason: {reason}", "text": text_response}))
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    out = (OUTPUT_DIR / f"banana_composite_{ts}.png").resolve()
    with open(out, "wb") as f:
        f.write(base64.b64decode(image_data))
    return {"path": str(out), "model": model, "aspect_ratio": aspect_ratio,
            "resolution": resolution, "sources": [str(Path(p).resolve()) for p in images], "text": text_response}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--image", action="append", required=True, dest="images", help="Repeatable")
    ap.add_argument("--aspect-ratio", default="1:1")
    ap.add_argument("--resolution", default="2K")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--api-key", default=None)
    args = ap.parse_args()

    api_key = args.api_key or os.environ.get("GOOGLE_AI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print(json.dumps({"error": True, "message": "No API key. Set GOOGLE_AI_API_KEY or pass --api-key"}))
        sys.exit(1)

    print(json.dumps(composite(args.images, args.prompt, args.model, api_key, args.aspect_ratio, args.resolution), indent=2))


if __name__ == "__main__":
    main()
