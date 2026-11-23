#!/usr/bin/env python3
"""news-image-20261122 entrypoint (standard library only).

The front page itself (``entry.png``, 1024x1024, Sunday 22 November 2026)
was rendered at build time with the agent's image tool and is stored in
this repository. This program does no drawing and needs no third-party
package: it checks the stored PNG is whole and within the competition
limits, then reproduces it byte-for-byte at ``/output/entry.png``
(or ``$MAKEFUN_OUTPUT_DIR``), and verifies the copy matches.

Exit codes: 0 ok, 2 bad input, 3 copy mismatch.
"""

import hashlib
import os
import struct
import sys
import zlib

LIMIT_BYTES = 1048576
WANT_WIDTH = 1024
WANT_HEIGHT = 1024
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
IEND_TRAILER = b"\x00\x00\x00\x00IEND\xaeB`\x82"


def die(message, code):
    print("error: " + message, file=sys.stderr)
    return code


def validate_png(blob):
    """Return an error string, or None when the blob is a whole 1024x1024 PNG."""
    if len(blob) > LIMIT_BYTES:
        return "entry.png is %d bytes, over the %d limit" % (len(blob), LIMIT_BYTES)
    if len(blob) < 8 or blob[:8] != PNG_SIGNATURE:
        return "entry.png does not start with the PNG signature"
    if len(blob) < 33 or blob[12:16] != b"IHDR":
        return "entry.png has no IHDR chunk"
    width, height = struct.unpack(">II", blob[16:24])
    if width != WANT_WIDTH or height != WANT_HEIGHT:
        return "entry.png is %dx%d, expected 1024x1024" % (width, height)
    if blob[-12:] != IEND_TRAILER:
        return "entry.png has no IEND trailer"
    return check_chunks(blob)


def check_chunks(blob):
    """Walk the PNG chunks, verifying lengths, CRCs, and that an IDAT exists."""
    offset = 8
    seen_idat = False
    seen_iend = False
    while offset + 8 <= len(blob):
        length, ctype = struct.unpack(">I4s", blob[offset:offset + 8])
        end = offset + 12 + length
        if end > len(blob):
            return "entry.png has a truncated %s chunk" % ctype.decode("latin1")
        stored_crc = struct.unpack(">I", blob[end - 4:end])[0]
        actual_crc = zlib.crc32(blob[offset + 4:end - 4]) & 0xFFFFFFFF
        if stored_crc != actual_crc:
            return "entry.png has a bad CRC in the %s chunk" % ctype.decode("latin1")
        if ctype == b"IDAT":
            seen_idat = True
        if ctype == b"IEND":
            seen_iend = True
            if end != len(blob):
                return "entry.png has bytes after the IEND chunk"
            break
        offset = end
    if not seen_idat:
        return "entry.png has no IDAT chunk"
    if not seen_iend:
        return "entry.png has no IEND chunk"
    return None


def main(argv):
    base = os.path.dirname(os.path.abspath(__file__))
    source = os.path.join(base, "entry.png")
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    target = os.path.join(out_dir, "entry.png")
    try:
        with open(source, "rb") as handle:
            blob = handle.read()
    except OSError as exc:
        return die("cannot read entry.png: %s" % exc, 2)
    problem = validate_png(blob)
    if problem:
        return die(problem, 2)
    os.makedirs(out_dir, exist_ok=True)
    with open(target, "wb") as handle:
        handle.write(blob)
    with open(target, "rb") as handle:
        written = handle.read()
    if written != blob:
        return die("written entry.png differs from the stored bytes", 3)
    print("wrote %s (%d bytes, sha256 %s)"
          % (target, len(blob), hashlib.sha256(blob).hexdigest()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
