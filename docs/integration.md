# Integration Guide

## Patch Order (must keep)

Apply patches in this exact order:

1. `ungoogled-chromium` base patches (platform-specific included)
2. upstream `fingerprint-chromium` patch set
3. this repo's `series.windows` (currently only `infomator-kernel-input-lock`)

If order is changed, input-lock behavior or fingerprint behavior may break.

## Windows Example

```bash
# 1) apply ungoogled patches (your existing process)
# 2) apply fingerprint-chromium patches (upstream process)

# 3) apply infomator patchpack
python tools/apply_series.py ^
  --series series.windows ^
  --target "E:\path\to\ungoogled-chromium\build\src"
```

## Runtime Expectation

After patch application and build:

- Human input on page is blocked while lock is active
- CDP `Input.dispatch*` still works while lock is active
- Human input is restored after unlock

## Notes

- This repo does **not** vendor upstream fingerprint patches.
- Keep this repo focused on Infomator-owned patches only.
