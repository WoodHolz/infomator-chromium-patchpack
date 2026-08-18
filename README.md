**English** | [中文](README.zh-CN.md)

# infomator-chromium-patchpack

Single source of Infomator-owned Chromium patches. This repo currently ships only `infomator-kernel-input-lock`.

Downstream builders (Windows / Linux / macOS) apply patches in this order:

1. `ungoogled-chromium` base patches (including platform-specific Windows patches)
2. Upstream `fingerprint-chromium` extra fingerprint patches
3. This repo’s series (`series.windows` today; linux/darwin series can be added later)
4. Compile the browser

This repo does **not** vendor `ungoogled-chromium` or `fingerprint-chromium` patch files.

## Layout

- `patches/infomator-kernel-input-lock/0001-input-lock.patch`
- `series.windows` — Infomator patches only, applied **after** fingerprint
- `tools/apply_series.py` — GNU `patch -p1` driver
- `docs/windows-build.md` — full Windows rebuild steps
- `docs/integration.md` — patch order and runtime expectations
- `tests/` — automated lock test and visual Tk bench

## Apply this patchpack (Windows)

The source tree must already have ungoogled + Windows patches **and** the upstream fingerprint set. Apply this series **before domain substitution**.

```cmd
cd E:\infomator-chromium-patchpack
set PATCH_BIN=E:\ungoogled-chromium-windows\build\src\third_party\git\usr\bin\patch.exe
python tools\apply_series.py --series series.windows --target E:\ungoogled-chromium-windows\build\src
```

Equivalent GNU patch flags:

`patch -p1 --ignore-whitespace -i <patch> -d <source-tree> --no-backup-if-mismatch`

Full clone / fingerprint / `build.py --ci` details: [Windows build](docs/windows-build.md).

## Verify

Automated:

```cmd
python tests\test_input_lock.py "E:\path\to\chrome.exe"
```

Visual (Chrome test page + native Tk lock / CDP panel):

```cmd
python tests\manual_input_lock_bench.py "E:\path\to\chrome.exe"
```
