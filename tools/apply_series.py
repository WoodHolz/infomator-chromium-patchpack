#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Apply GNU patch series to an existing source tree.

This repo intentionally contains only *your* patches (no ungoogled base patches).
So the target source tree must already be ungoogled-ready.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path


def find_patch_bin() -> Path:
  patch_bin_env = os.environ.get("PATCH_BIN")
  if patch_bin_env:
    p = Path(patch_bin_env)
    if p.exists():
      return p
    which = shutil.which(patch_bin_env)
    if which:
      return Path(which)
  which = shutil.which("patch")
  if not which:
    raise RuntimeError("Could not find 'patch' binary in PATH, or set PATCH_BIN.")
  return Path(which)


def parse_series(series_path: Path) -> list[str]:
  lines = series_path.read_text(encoding="utf-8", errors="ignore").splitlines()
  out: list[str] = []
  for line in lines:
    s = line.strip()
    if not s or s.startswith("#"):
      continue
    out.append(s)
  return out


def main() -> int:
  ap = argparse.ArgumentParser()
  ap.add_argument("--series", required=True, type=Path)
  ap.add_argument("--target", required=True, type=Path)
  ap.add_argument("--patch-bin", default=None, type=Path)
  args = ap.parse_args()

  patch_bin = args.patch_bin or find_patch_bin()
  if not patch_bin.exists():
    raise RuntimeError(f"patch bin not found: {patch_bin}")

  patches = parse_series(args.series)
  target = args.target.resolve()
  series_root = args.series.parent.resolve()

  for i, rel_patch in enumerate(patches, start=1):
    patch_path = Path(rel_patch)
    if not patch_path.is_absolute():
      patch_path = series_root / patch_path
    patch_path = patch_path.resolve()
    if not patch_path.exists():
      raise RuntimeError(f"patch not found: {patch_path} (from series line {i})")

    cmd = [
      str(patch_bin),
      "-p1",
      "--ignore-whitespace",
      "-i",
      str(patch_path),
      "-d",
      str(target),
      "--no-backup-if-mismatch",
    ]
    print(f"[{i}/{len(patches)}] Applying {patch_path.name}")
    subprocess.run(cmd, check=True)

  return 0


if __name__ == "__main__":
  raise SystemExit(main())

