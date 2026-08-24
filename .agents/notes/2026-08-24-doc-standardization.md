# 决策：文档与结构标准化（2026-08-24）

已实施：是

## 问题
项目长期只有用户文档（README / README_zh / ARCHITECTURE），缺少被 Agent 自动注入的规则层；源码子目录无双件，Agent 进入目录无法自动获知约束。

## 决策
按 maintenance-flow 技能补齐根 AGENTS.md 仪表盘（≤30 行）与源码子目录（core/ capture/ export/ vlm/ tests/）的 AGENTS.md + README.md 双件；决策记录统一放 .agents/notes/。
根 README.md 与 README_zh.md 保持用户文档职责不动；docs/ARCHITECTURE.md 位置合规，仅小幅补全文件地图。

## 替代方案（强制）
- 只补根 AGENTS.md，不建子双件：层级约束仍要人翻找，进入子目录的 Agent 无自动上下文，违背注入机制设计 → 否决
- 合并进单一 CONTRIBUTING.md：README/AGENTS 职责混淆，自动注入会整体携带无关长文 → 否决
- 给 results/、docs/ 也建双件：输出目录与已有文档（ARCHITECTURE/PHILOSOPHY/DEPLOYMENT）无需重复，维护成本大于收益 → 否决

## 影响
新增 11 个文档文件；不改变任何功能代码；既有用户文档内容保持不动；验证快照以实际运行 pytest 数字为准。