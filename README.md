# infomator-chromium-patchpack

单一来源的补丁仓库：只维护你们自己的补丁（当前仅 `infomator-kernel-input-lock`）。

下游构建方（Windows/Linux/mac）通常流程是：
1. 先用 `ungoogled-chromium` 自己的基础 patches（含 windows 兼容补丁）构建源码
2. 再应用上游维护的 `fingerprint-chromium` 补丁集
3. 最后应用本仓库的补丁序列（`series.windows` / 未来可扩展 linux/darwin）
4. 编译得到浏览器产物

本仓库不包含 `ungoogled-chromium/windows/*.patch` 等基础补丁。

## 目录约定

当前仓库内应包含：

- `patches/infomator-kernel-input-lock/0001-input-lock.patch`
- `series.windows`（补丁顺序）

说明：

- `fingerprint-chromium` 补丁内容本体不放在这里，由其上游项目维护
- `series.windows` 只描述“在 fingerprint 之后，额外应用哪些 infomator 自有补丁”

## 应用补丁（Windows 示例）

```bash
python tools/apply_series.py ^
  --series series.windows ^
  --target "E:\path\to\ungoogled-chromium\build\src"
```

底层使用 `GNU patch`，等价于：

`patch -p1 --ignore-whitespace -i <patch> -d <source-tree> --no-backup-if-mismatch`

## 验证

自动：

```bash
python tests/test_input_lock.py "E:\path\to\chrome.exe"
```

可视化（Tk 控制面板 + Chrome 测试页）：

```bash
python tests/manual_input_lock_bench.py "E:\path\to\chrome.exe"
```

