**English** | [中文](windows-build.zh-CN.md)

# Windows rebuild

Baseline used in production: Chromium **144.0.7559.132** on `ungoogled-chromium-windows`.

Do **not** commit fingerprint or Infomator patches into `ungoogled-chromium-windows`. That tree stays vanilla. Extra patches come from the other two repos.

## Patch order (required)

1. `ungoogled-chromium` core series
2. `ungoogled-chromium-windows` Windows series (`patches/series` in that repo)
3. Upstream `fingerprint-chromium` `extra/fingerprint/*.patch` (16 files below)
4. This repo: `series.windows` (input lock)
5. Domain substitution
6. `gn gen` + `ninja`

Input lock is written to apply after ungoogled + fingerprint + Windows patches, and **before domain substitution**.

## `build.py` trap

In `ungoogled-chromium-windows`:

| Command | What it does |
|---|---|
| `python build.py` (no `--ci`) | Re-clones / resets `build\src`, applies **only** ungoogled + Windows series, then domain substitution, then compiles. Fingerprint and Infomator patches are **not** applied. |
| `python build.py --ci` | Skips clone/reset if `build\src\BUILD.gn` already exists. Use this for incremental compiles on a tree that is already patched. |

Never run a no-`--ci` `build.py` on a tree you still want to keep.

GNU patch binary after Chromium is unpacked:

`E:\ungoogled-chromium-windows\build\src\third_party\git\usr\bin\patch.exe`

---

## A. Incremental (existing `build\src` already has fingerprint + input lock)

Developer Command Prompt for VS:

```cmd
cd E:\ungoogled-chromium-windows
python build.py --ci
```

Or ninja only:

```cmd
cd E:\ungoogled-chromium-windows\build\src
third_party\ninja\ninja.exe -C out\Default chrome
```

---

## B. Full rebuild from a clean Windows tree

`build.py` does not stop between Windows patches and domain substitution. Extra patches must be inserted at that point.

Paths below match a typical local layout; change them if yours differs.

| Repo | Typical path |
|---|---|
| ungoogled-chromium-windows | `E:\ungoogled-chromium-windows` |
| fingerprint-chromium | `E:\fingerprint-chromium` |
| this patchpack | `E:\infomator-chromium-patchpack` |

### 1) Prepare vanilla `build\src` with ungoogled + Windows patches only

Follow upstream `ungoogled-chromium-windows` until Chromium is cloned/unpacked and **both** ungoogled series and Windows `patches/series` have been applied.

Stop **before** domain substitution. Practical options:

- Run the first half of `build.py` locally (clone, downloads, prune, unpack, two `patches.apply_patches` calls), then continue from step 2 below. Do not commit local `build.py` edits.
- Or, for a one-shot build only: temporarily list the fingerprint + Infomator patches at the **end** of `ungoogled-chromium-windows/patches/series` (files live in the other repos or a throwaway copy). Run `python build.py`, then **delete those copies** so the Windows repo stays clean. This is a host-tree shortcut, not the published workflow.

### 2) Apply upstream fingerprint patches

Apply **only** `extra/fingerprint/` — not the entire fingerprint-chromium `patches/series` (that would re-apply ungoogled patches).

Order:

```
000-add-fingerprint-switches.patch
001-disable-runtime.enable.patch
002-user-agent-fingerprint.patch
003-audio-fingerprint.patch
005-hardware-concurrency-fingerprint.patch
006-font-fingerprint.patch
007-shadow-root.patch
009-webdriver.patch
010-headless.patch
011-gpu-info.patch
012-canvas-get-image-data.patch
013-canvas-toDataURL.patch
014-client-rects.patch
015-canvas-measure-text.patch
016-webgl-readPixels.patch
018-timezone.patch
```

Source directory: `E:\fingerprint-chromium\patches\extra\fingerprint\`

Example (cmd):

```cmd
set PATCH_BIN=E:\ungoogled-chromium-windows\build\src\third_party\git\usr\bin\patch.exe
set SRC=E:\ungoogled-chromium-windows\build\src
set FP=E:\fingerprint-chromium\patches\extra\fingerprint

for %%F in (
  000-add-fingerprint-switches.patch
  001-disable-runtime.enable.patch
  002-user-agent-fingerprint.patch
  003-audio-fingerprint.patch
  005-hardware-concurrency-fingerprint.patch
  006-font-fingerprint.patch
  007-shadow-root.patch
  009-webdriver.patch
  010-headless.patch
  011-gpu-info.patch
  012-canvas-get-image-data.patch
  013-canvas-toDataURL.patch
  014-client-rects.patch
  015-canvas-measure-text.patch
  016-webgl-readPixels.patch
  018-timezone.patch
) do "%PATCH_BIN%" -p1 --ignore-whitespace -i "%FP%\%%F" -d "%SRC%" --no-backup-if-mismatch
```

Keep fingerprint patches on the same Chromium tag as the Windows tree (for example `144.0.7559.132`).

### 3) Apply this patchpack

```cmd
cd E:\infomator-chromium-patchpack
set PATCH_BIN=E:\ungoogled-chromium-windows\build\src\third_party\git\usr\bin\patch.exe
python tools\apply_series.py --series series.windows --target E:\ungoogled-chromium-windows\build\src
```

### 4) Domain substitution, then compile

Finish the remainder of `ungoogled-chromium-windows` `build.py`: domain substitution, rust/gn bootstrap, `gn gen`, ninja (`chrome`, `chromedriver`, `mini_installer`).

If `build\src` is already fully prepared (steps 1–4 done, `out\Default` exists):

```cmd
cd E:\ungoogled-chromium-windows
python build.py --ci
```

Package:

```cmd
cd E:\ungoogled-chromium-windows
python package.py
```

### 5) Verify

```cmd
cd E:\infomator-chromium-patchpack
python tests\test_input_lock.py "E:\ungoogled-chromium-windows\build\src\out\Default\chrome.exe"
python tests\manual_input_lock_bench.py "E:\ungoogled-chromium-windows\build\src\out\Default\chrome.exe"
```

See [tests/README.md](../tests/README.md).

## Vendor note

The portable zip from `package.py` is what desktop-client vendors as `infomator-chromium` (`chrome.exe` at the package root). The installer exe is not the vendor payload.
