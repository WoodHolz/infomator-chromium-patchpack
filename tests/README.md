# Tests

## 1) Runtime lock test (automated)

```bash
python tests/test_input_lock.py "E:\path\to\chrome.exe"
```

Expected result:

- `PASS: Input.setUserInputLocked behavior verified`

## 2) Manual verification (recommended)

You can also reuse your local manual bench script to validate hover/drag and native control-panel workflow.
When this patchpack becomes an independent repo, copy your validated manual bench script into:

- `tests/manual_input_lock_bench.py`

