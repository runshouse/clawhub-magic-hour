#!/usr/bin/env python3
"""Animate an image (local path or public https URL) into a video with Magic Hour.

Local files are uploaded automatically by the SDK. Prints one JSON object:
{project_id, status, model, url, urls, credits_charged, width, height, fps}
"""

from __future__ import annotations

import argparse
import os
import sys
import warnings
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as c  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("image", help="Local image path (png/jpg/webp) or public https:// URL")
    p.add_argument("prompt", help="How the image should move (camera motion, subject action)")
    p.add_argument("--model", default=c.DEFAULT_VIDEO_MODEL, help="Video model id (default: wan-2.2, free)")
    p.add_argument("--duration", type=int, default=5, help="Seconds (must be allowed by the model; default 5)")
    p.add_argument("--resolution", default="480p", choices=c.RESOLUTIONS)
    p.add_argument("--name", default=None)
    p.add_argument("--download-dir", default=None, help="Download the mp4 into this directory")
    p.add_argument("--no-wait", action="store_true", help="Return immediately with status=queued")
    p.add_argument("--timeout", type=float, default=None)
    return p


def main(argv=None) -> None:
    args = build_parser().parse_args(argv)
    warn = c.validate_video(args.model, args.duration, args.resolution)
    if warn:
        print(f"warning: {warn}", file=sys.stderr)

    def go():
        if args.image.startswith("http://"):
            c.fail("Use a public HTTPS image URL, not HTTP")
        if args.image.startswith("https://"):
            if not urlparse(args.image).hostname:
                c.fail("A public HTTPS image URL must include a hostname")
        elif not args.image.startswith("api-assets/"):
            image_path = Path(args.image)
            if image_path.is_symlink() or not image_path.is_file():
                c.fail("The selected image must be a regular file, not a symlink or directory")
            image_format = {".png": "PNG", ".jpg": "JPEG", ".jpeg": "JPEG", ".webp": "WEBP"}.get(image_path.suffix.lower())
            if image_format is None:
                c.fail("Select a PNG, JPEG, or WebP image")
            if not 0 < image_path.stat().st_size <= 20 * 1024 * 1024:
                c.fail("The selected image must be nonempty and at most 20 MiB (this helper's local upload limit)")
            try:
                from PIL import Image
            except ImportError:
                c.fail("Image validation requires Pillow. Run: pip install Pillow==12.3.0")
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("error", Image.DecompressionBombWarning)
                    with Image.open(image_path, formats=["PNG", "JPEG", "WEBP"]) as image:
                        if image.format != image_format:
                            raise ValueError("Image contents do not match the selected file extension")
                        image.verify()
                    with Image.open(image_path, formats=["PNG", "JPEG", "WEBP"]) as image:
                        image.load()
            except (OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
                c.fail(f"Invalid selected image: {exc}")
        client = c.get_client(timeout=args.timeout)
        resp = client.v1.image_to_video.generate(
            assets={"image_file_path": args.image},
            end_seconds=float(args.duration),
            style={"prompt": args.prompt},
            model=args.model,
            resolution=args.resolution,
            name=args.name or f"clawhub i2v: {args.prompt[:60]}",
            wait_for_completion=not args.no_wait,
            **c.download_kwargs(args.download_dir),
        )
        out = c.serialize(resp, model=args.model, kind="video")
        out["estimated_credits"] = c.estimate_credits(args.model, args.duration)
        return out

    c.run(go)


if __name__ == "__main__":
    main()
