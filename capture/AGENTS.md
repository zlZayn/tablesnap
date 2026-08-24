# capture/ — 规则层

继承根规则，见 [../AGENTS.md](../AGENTS.md)。

capture/ 特有约束：
- tkinter 只能在主线程运行；键盘 hook 回调必须经 `root.after(0, ...)` 调度回 GUI 线程
- 选区行为（暗化、角标、边框、最小尺寸、字号）参数来自 [core/config.py](../core/README.md)，不在本目录硬编码
- 不写“有什么文件/怎么改”，那是 [README.md](README.md) 的职责