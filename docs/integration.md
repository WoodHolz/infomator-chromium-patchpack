**English** | [中文](integration.zh-CN.md)

# Integration Guide

## Patch order (must keep)

1. `ungoogled-chromium` base patches (platform-specific included)
2. Upstream `fingerprint-chromium` `extra/fingerprint` set
3. This repo’s `series.windows` (currently only `infomator-kernel-input-lock`)
4. Domain substitution, then compile

If this order changes, input-lock or fingerprint behavior may break.

Windows clone / `build.py` / fingerprint file list: [Windows build](windows-build.md).

## Apply Infomator series

```cmd
set PATCH_BIN=E:\ungoogled-chromium-windows\build\src\third_party\git\usr\bin\patch.exe
python tools\apply_series.py --series series.windows --target E:\ungoogled-chromium-windows\build\src
```

Do this **before** domain substitution.

## Runtime expectation

After patches and build:

- Human input on the page is blocked while lock is active
- CDP `Input.dispatch*` still works while lock is active
- Human input is restored after unlock
- Agent command: `Input.setUserInputLocked({locked: true|false})`
- Do **not** use `Input.setIgnoreInputEvents` — that also drops CDP input
- Unlock is **not** done in `InputHandler::Disable()` (desktop-client detaches CDP after send)

## Notes

- This repo does **not** vendor upstream fingerprint patches.
- Keep this repo focused on Infomator-owned patches only.
