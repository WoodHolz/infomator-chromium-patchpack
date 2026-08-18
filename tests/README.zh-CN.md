[English](README.md) | **中文**

# 测试

## 1) 自动锁定测试

```cmd
python tests\test_input_lock.py "E:\path\to\chrome.exe"
```

预期：

- `PASS: Input.setUserInputLocked behavior verified`

## 2) 可视化 / 手工 bench（推荐）

双窗口：Chrome 测试页做人的 click / hover / 拖拽 / 键盘；原生 Tk 控制面板做锁定开关和 CDP 模拟。

```cmd
python tests\manual_input_lock_bench.py "E:\path\to\chrome.exe"
```

步骤：

1. 未锁定基线：在测试页操作，trusted* 应增加
2. 锁定后：测试页人工操作应被阻断
3. 锁定下：在 Tk 面板点 CDP Hover / Click / Key，测试页仍应响应
4. 解锁后：测试页人工操作恢复
