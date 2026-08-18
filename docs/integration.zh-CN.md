[English](integration.md) | **中文**

# 集成说明

## 补丁顺序（必须遵守）

1. `ungoogled-chromium` 基础补丁（含平台补丁）
2. 上游 `fingerprint-chromium` 的 `extra/fingerprint` 集
3. 本仓库 `series.windows`（当前仅 `infomator-kernel-input-lock`）
4. Domain substitution，然后编译

顺序改了，输入闸或指纹行为可能坏掉。

Windows 的 clone / `build.py` / fingerprint 文件列表见 [Windows 构建](windows-build.zh-CN.md)。

## 应用 Infomator 序列

```cmd
set PATCH_BIN=E:\ungoogled-chromium-windows\build\src\third_party\git\usr\bin\patch.exe
python tools\apply_series.py --series series.windows --target E:\ungoogled-chromium-windows\build\src
```

必须在 **domain substitution 之前**打。

## 运行时预期

补丁打上并编译后：

- 锁定时，页面上的真人输入被拦截
- 锁定时，CDP `Input.dispatch*` 仍然有效
- 解锁后，真人输入恢复
- Agent 命令：`Input.setUserInputLocked({locked: true|false})`
- **不要**用 `Input.setIgnoreInputEvents`，那条会把 CDP 一起丢掉
- **不要**在 `InputHandler::Disable()` 里解锁（desktop-client 发完就会 detach CDP）

## 说明

- 本仓库不收录上游 fingerprint 补丁。
- 只维护 Infomator 自有补丁。
