[English](README.md) | **中文**

# infomator-chromium-patchpack

Infomator 自有 Chromium 补丁的单一来源。当前只包含 `infomator-kernel-input-lock`。

下游构建方（Windows / Linux / macOS）按这个顺序打补丁：

1. `ungoogled-chromium` 基础补丁（含 Windows 平台补丁）
2. 上游 `fingerprint-chromium` 的 extra fingerprint 补丁
3. 本仓库序列（目前是 `series.windows`；以后可加 linux/darwin）
4. 编译浏览器

本仓库**不收录** `ungoogled-chromium` 或 `fingerprint-chromium` 的补丁文件。

## 目录

- `patches/infomator-kernel-input-lock/0001-input-lock.patch`
- `series.windows` — 仅 Infomator 补丁，必须在 fingerprint **之后**打
- `tools/apply_series.py` — GNU `patch -p1` 驱动
- `docs/windows-build.zh-CN.md` — Windows 全量构建步骤
- `docs/integration.zh-CN.md` — 补丁顺序与运行时预期
- `tests/` — 自动锁定测试和可视化 Tk bench

## 应用本 patchpack（Windows）

源码树必须已经打过 ungoogled + Windows 补丁，以及上游 fingerprint 集。本序列要在 **domain substitution 之前**打。

```cmd
cd E:\infomator-chromium-patchpack
set PATCH_BIN=E:\ungoogled-chromium-windows\build\src\third_party\git\usr\bin\patch.exe
python tools\apply_series.py --series series.windows --target E:\ungoogled-chromium-windows\build\src
```

等价 GNU patch 参数：

`patch -p1 --ignore-whitespace -i <patch> -d <source-tree> --no-backup-if-mismatch`

完整的 clone / fingerprint / `build.py --ci` 说明见 [Windows 构建](docs/windows-build.zh-CN.md)。

## 验证

自动：

```cmd
python tests\test_input_lock.py "E:\path\to\chrome.exe"
```

可视化（Chrome 测试页 + 原生 Tk 锁定 / CDP 面板）：

```cmd
python tests\manual_input_lock_bench.py "E:\path\to\chrome.exe"
```
