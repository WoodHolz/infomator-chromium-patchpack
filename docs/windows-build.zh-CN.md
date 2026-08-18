[English](windows-build.md) | **中文**

# Windows 构建复现

当前生产基线：Chromium **144.0.7559.132**，宿主为 `ungoogled-chromium-windows`。

不要把 fingerprint 或 Infomator 补丁提交进 `ungoogled-chromium-windows`。那个仓库保持原版。额外补丁分别来自另外两个仓库。

## 补丁顺序（必须遵守）

1. `ungoogled-chromium` 核心 series
2. `ungoogled-chromium-windows` 的 Windows series（该仓库的 `patches/series`）
3. 上游 `fingerprint-chromium` 的 `extra/fingerprint/*.patch`（下面 16 个文件）
4. 本仓库：`series.windows`（输入闸）
5. Domain substitution
6. `gn gen` + `ninja`

输入闸补丁要求：在 ungoogled + fingerprint + Windows 补丁之后、**domain substitution 之前**打。

## `build.py` 陷阱

在 `ungoogled-chromium-windows` 里：

| 命令 | 行为 |
|---|---|
| `python build.py`（不带 `--ci`） | 重新 clone / reset `build\src`，**只打** ungoogled + Windows series，然后 domain substitution，再编译。不会打 fingerprint 和 Infomator 补丁。 |
| `python build.py --ci` | 若已有 `build\src\BUILD.gn`，跳过 clone/reset。用于已经打过额外补丁的树做增量编译。 |

还想保留现有源码树时，不要跑无 `--ci` 的 `build.py`。

Chromium 解包后的 GNU patch：

`E:\ungoogled-chromium-windows\build\src\third_party\git\usr\bin\patch.exe`

---

## A. 增量（`build\src` 里已经有 fingerprint + 输入闸）

在 **Developer Command Prompt for VS** 里：

```cmd
cd E:\ungoogled-chromium-windows
python build.py --ci
```

或只跑 ninja：

```cmd
cd E:\ungoogled-chromium-windows\build\src
third_party\ninja\ninja.exe -C out\Default chrome
```

---

## B. 从干净 Windows 树全量重建

`build.py` 不会在 Windows 补丁和 domain substitution 之间停下。额外补丁必须插在这个位置。

下面是常见本机路径，按你的实际位置改：

| 仓库 | 典型路径 |
|---|---|
| ungoogled-chromium-windows | `E:\ungoogled-chromium-windows` |
| fingerprint-chromium | `E:\fingerprint-chromium` |
| 本 patchpack | `E:\infomator-chromium-patchpack` |

### 1) 先准备只含 ungoogled + Windows 补丁的 `build\src`

按上游 `ungoogled-chromium-windows` 做到 Chromium 已 clone/解包，并且 **ungoogled series 和 Windows `patches/series` 都已打上**。

在 **domain substitution 之前**停住。可行做法：

- 本地跑 `build.py` 的前半段（clone、下载、prune、unpack、两次 `patches.apply_patches`），然后从下面第 2 步继续。不要把对 `build.py` 的改动提交进 Windows 仓库。
- 或者一次性构建：临时把 fingerprint + Infomator 补丁列在 `ungoogled-chromium-windows/patches/series` **末尾**（文件来自另外两个仓库或一次性副本），跑 `python build.py`，编完后**删掉这些副本**，保持 Windows 仓库干净。这是宿主树上的捷径，不是对外发布的流程。

### 2) 打上游 fingerprint 补丁

只打 `extra/fingerprint/`，不要把 fingerprint-chromium 整份 `patches/series` 再打一遍（会重复打 ungoogled 补丁）。

顺序：

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

源目录：`E:\fingerprint-chromium\patches\extra\fingerprint\`

示例（cmd）：

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

fingerprint 补丁的 Chromium 标签要和 Windows 树一致（例如 `144.0.7559.132`）。

### 3) 打本 patchpack

```cmd
cd E:\infomator-chromium-patchpack
set PATCH_BIN=E:\ungoogled-chromium-windows\build\src\third_party\git\usr\bin\patch.exe
python tools\apply_series.py --series series.windows --target E:\ungoogled-chromium-windows\build\src
```

### 4) Domain substitution，然后编译

把 `ungoogled-chromium-windows` 的 `build.py` 后半段做完：domain substitution、rust/gn bootstrap、`gn gen`、ninja（`chrome`、`chromedriver`、`mini_installer`）。

若 `build\src` 已经按步骤 1–4 准备好（且已有 `out\Default`）：

```cmd
cd E:\ungoogled-chromium-windows
python build.py --ci
```

打包：

```cmd
cd E:\ungoogled-chromium-windows
python package.py
```

### 5) 验证

```cmd
cd E:\infomator-chromium-patchpack
python tests\test_input_lock.py "E:\ungoogled-chromium-windows\build\src\out\Default\chrome.exe"
python tests\manual_input_lock_bench.py "E:\ungoogled-chromium-windows\build\src\out\Default\chrome.exe"
```

见 [tests/README.zh-CN.md](../tests/README.zh-CN.md)。

## 产物说明

`package.py` 打出的便携 zip 才是 desktop-client 要 vendor 的 `infomator-chromium`（`chrome.exe` 在包根目录）。安装包 exe 不是 vendor 载荷。
