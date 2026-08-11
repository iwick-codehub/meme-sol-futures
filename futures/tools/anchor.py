#!/usr/bin/env python3
"""Hash-anchor a contract record (MTC-style).

anchor.py seal   records/contract_001.json   -> writes records/contract_001.anchor.json
anchor.py verify records/contract_001.json   -> checks the record against its anchor

The anchor is the SHA-256 of the record's canonical JSON. Any edit to the record
after sealing fails verification; deliberate amendments re-seal and the old anchor
stays in the anchor file's history list.
"""
import hashlib
import json
import sys
from pathlib import Path


def canonical(record: dict) -> bytes:
    return json.dumps(record, sort_keys=True, separators=(",", ":")).encode()


def sha256(record: dict) -> str:
    return hashlib.sha256(canonical(record)).hexdigest()


def anchor_path(record_file: Path) -> Path:
    return record_file.with_suffix(".anchor.json")


def seal(record_file: Path) -> str:
    record = json.loads(record_file.read_text())
    digest = sha256(record)
    apath = anchor_path(record_file)
    history = []
    if apath.exists():
        prior = json.loads(apath.read_text())
        history = prior.get("history", [])
        if prior.get("sha256") and prior["sha256"] != digest:
            history.append(prior["sha256"])
    apath.write_text(json.dumps(
        {"record": record.get("record"), "sha256": digest, "history": history},
        indent=2) + "\n")
    return digest


def verify(record_file: Path) -> bool:
    record = json.loads(record_file.read_text())
    apath = anchor_path(record_file)
    if not apath.exists():
        print(f"NO ANCHOR for {record_file}")
        return False
    anchored = json.loads(apath.read_text())["sha256"]
    actual = sha256(record)
    ok = anchored == actual
    print(f"{'OK' if ok else 'MISMATCH'} {record_file.name} anchored={anchored[:16]}… actual={actual[:16]}…")
    return ok


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("seal", "verify"):
        sys.exit(__doc__)
    path = Path(sys.argv[2])
    if sys.argv[1] == "seal":
        print(f"sealed {path.name} -> {seal(path)}")
    else:
        sys.exit(0 if verify(path) else 1)
