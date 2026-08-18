**English** | [中文](README.zh-CN.md)

# Tests

## 1) Automated lock test

```cmd
python tests\test_input_lock.py "E:\path\to\chrome.exe"
```

Expected:

- `PASS: Input.setUserInputLocked behavior verified`

## 2) Visual / manual bench (recommended)

Two windows: the Chrome test page is for human click / hover / drag / keyboard; the native Tk panel is for lock/unlock and CDP simulation.

```cmd
python tests\manual_input_lock_bench.py "E:\path\to\chrome.exe"
```

Steps:

1. Unlocked baseline: operate on the test page; trusted* counters should increase
2. After lock: human actions on the test page should be blocked
3. While locked: Tk panel CDP Hover / Click / Key should still affect the test page
4. After unlock: human actions on the test page work again
