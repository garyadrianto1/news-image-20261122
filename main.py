#!/usr/bin/env python3
"""news-image-20261122 entry program (standard library only).

Copies the pre-rendered front page ``entry.png`` (1024x1024, Sunday
22 November 2026) to ``/output/entry.png`` (or ``$MAKEFUN_OUTPUT_DIR``).
The image itself is drawn at build time by experiments/draw_round1.py;
this program only validates the PNG and reproduces it byte-for-byte,
so the grading sandbox needs nothing beyond the standard library.
"""
import hashlib
import os
import struct
import sys

MAX_BYTES = 1048576
EXPECT_W, EXPECT_H = 1024, 1024
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def fail(msg, code):
    print(f"error: {msg}", file=sys.stderr)
    return code


def check_png(data):
    if len(data) > MAX_BYTES:
        return f"entry.png is {len(data)} bytes, over the {MAX_BYTES} limit"
    if len(data) < 8 or data[:8] != PNG_MAGIC:
        return "entry.png is not a PNG file"
    if len(data) < 33 or data[12:16] != b"IHDR":
        return "entry.png has no IHDR chunk"
    width, height = struct.unpack(">II", data[16:24])
    if (width, height) != (EXPECT_W, EXPECT_H):
        return f"entry.png is {width}x{height}, expected 1024x1024"
    if data[-12:] != b"\x00\x00\x00\x00IEND\xaeB`\x82":
        return "entry.png has no IEND trailer"
    return None


def main(argv):
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(here, "entry.png")
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    dst = os.path.join(out_dir, "entry.png")
    try:
        with open(src, "rb") as fh:
            data = fh.read()
    except OSError as exc:
        return fail(f"cannot read entry.png: {exc}", 2)
    problem = check_png(data)
    if problem:
        return fail(problem, 2)
    os.makedirs(out_dir, exist_ok=True)
    with open(dst, "wb") as fh:
        fh.write(data)
    with open(dst, "rb") as fh:
        back = fh.read()
    if back != data:
        return fail("written entry.png does not match the source bytes", 3)
    digest = hashlib.sha256(data).hexdigest()
    print(f"wrote {dst} ({len(data)} bytes, sha256 {digest})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
