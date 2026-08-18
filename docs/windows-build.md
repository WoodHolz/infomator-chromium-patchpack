# Windows 构建复现（MVP）

假设你已经在本机完成：

1. 从 `ungoogled-chromium` clone 得到 `build/src`
2. 已经应用了 ungoogled 的基础 patches（包括 windows 兼容补丁等）
3. 已经应用了上游维护的 `fingerprint-chromium` 补丁集

此时再应用本 patchpack：

```bash
python tools/apply_series.py ^
  --series series.windows ^
  --target "E:\path\to\ungoogled-chromium\build\src"
```

再进入你现有的 build 流程（ninja/gn 等）。

