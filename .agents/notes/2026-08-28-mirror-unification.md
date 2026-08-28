# 决策：uv.lock 包源统一为清华镜像（2026-08-28）

已实施：是

## 问题
uv.lock 全部 181 个包源与制品 URL 指向 pypi.org / files.pythonhosted.org；本机（大陆网络）访问官方源慢且偶发连不上，重锁与安装反复超时。

## 决策
uv.lock 以 `uv lock --default-index https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple` 重新生成（commit cea3f4d）。
依赖元数据零变化：版本与哈希逐行比对无差异，diff 1435 行为纯 URL 变化。
后续重新锁文件必须沿用同一 --default-index 参数，否则锁会回退到官方源。

## 替代方案（强制）
- 保持官方源：本机访问 pypi.org 慢/不稳，重试成本高，问题依旧 → 否决
- 分仓库各用各的 index，锁文件不写死：多机配置漂移，锁文件与实际安装源不一致，难排障 → 否决
- 用 uv 全局配置（uv.toml default-index）代替写进锁：依赖本机配置，换机即失效，锁文件不自洽 → 否决

## 影响
- 安装行为不变（版本与哈希一致），仅下载源变化
- 重新锁命令已同步进根 AGENTS.md 常用命令，防回退到官方源