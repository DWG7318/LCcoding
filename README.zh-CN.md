# LCCoding 2.4.1

**由 Owner 掌握产品方向、AI 完成工程闭环，并通过分段验收避免把所有人工工作堆到最后的企业级产品开发方法。**

## 主干不变

```text
Owner Proposal
      ↓
Proposal Readiness Check
      ↓
Project Initialization
      ↓
Calabash Draft
      ↓
[先建立 Simulation World foundation → Workflow 能力端 ∥ UI 产品呈现端分别推进]
      ↓
Mandatory Calabash Upgrade
      ↓
Product Baseline
      ↓
Feature Slice
      ↓
锁定 UI 的 Feature Integration
      ↓
SLK / CLK / GLK
      ↓
独立、分层、尽量不重复的 Verification
      ↓
Owner Acceptance
      ↓
Delivery
```


主干节点没有增加；具体含义是：

- 每个正常 Loop Run 在 `SLK / CLK / GLK` 内部完成 `D0–D3 → Loop Owner Acceptance`；
- 所有正常 Run 验收后，主干中的 `Verification` 承载集中漏洞审计、修复、独立复验与关闭；
- 主干中的 `Owner Acceptance` 是安全修复后的 Post-Security Owner Acceptance；
- Delivery 先做当前客户的 Delivery Method Q&A。

这里需要特别说明：**SLK、CLK、GLK 内部本来就有 Owner/Human Acceptance，而且必须保留。**它不是 Handoff，也不能被 LCCoding 合并成最后一次大验收。

## 既有工程接管

Project Initialization 支持 `NEW` 与 `EXISTING` 两种模式，但不会增加新生命周期。EXISTING 保留原有仓库、Git 历史、当前版本、材料和可信证据；旧有“已完成”只能记为 `CLAIMED_UNATTESTED`，不能直接越过 LCCoding 的证据边界。

进入工程前，Owner 决定 `CONTINUE`、`NARROW_REDIRECT`、`HOLD` 或 `TERMINATE`。可运行 UI 是 Owner 理解现状的第一认知锚点，但不是完成证据；AI 必须从可见入口反向还原 Workflow、状态、数据、权限、异常与恢复，并为不可见行为提供独立证据。只有真实缺口才进入现有 Feature Slice 与 Loop Run。

接管仍属于 Project Initialization，只输出 `READY`、`BLOCKED` 或 `NOT_CONTINUING`。`status.json` 是唯一权威的持久项目状态；Project Health 是评估证据，`PHASE-STATUS.json` 只是派生视图。这里不得写入 runtime 或 Agent 会话状态。

## 固定主干、按风险调深浅

所有强制主干节点始终保留。Project Fingerprint 中的产品不确定性、系统耦合、真实风险、不可逆性和新颖性决定分析、材料与证据深度。`UNKNOWN` 是允许记录的待判定状态，必须继续评估并采用保守的更深覆盖，不能被视为 all-low 或最终充分判断。充分证据应引用复用；简单工作可以简洁，高风险工作必须加深；`recommended_loop` 只负责执行拓扑。

## Simulation-first 产品形成

在现有 Workflow/UI/Simulation 节点内，必须先有至少一个最小、真实可运行、带版本的 Simulation World foundation。它一开始不必完善，也不是一次性冻结；项目可以增加多个同级 Simulation 逻辑子树，但不得嵌套 Simulation 子项。Simulation 始终保持 `VERSIONED_MUTABLE`。

基础 Simulation 存在后，Workflow 与 UI 才作为同等产品端分别独立向前建设，也可以并行推进；二者都必须形成真实、可运行、可检查的结果，不能只停留在计划、空壳或 mock。Product Formation 继续同步三者的产品语义与场景，但不要求前期接通或共同联调。跨层连接与贯通证明仍由后续 Feature Slice 和 UI-locked Integration 负责，Feature Slice 既有的 Workflow 继承和改进职责保持不变。

一个总项目默认只有一个 Git/GitHub 仓库，内部可以有多个 UI、Workflow、Simulation 逻辑子树，每个已实现子树有组件版本和内容 hash。每个 CORE Workflow 与已实现 EXTRA Workflow 都必须直接提供 API 与 MCP 两类接口，并共用同一能力逻辑；未实现 EXTRA 不创建空目录或空接口。Owner 确认一条至少贯穿一个 Simulation、一个 CORE Workflow 和一个 UI 的产品主线，只决定优先施工方向，不降低其他 CORE。worktree 只是可选隔离手段，不是产品结构。

## 内置 BI 与 Windows 独立窗口

LCCoding 2.4.1 保持内置只读 BI、独立 300×480 Windows 窗口、四阶段主视图与既有视觉不变，只在现有 Product Baseline 和 Loop Run · D0–D3 步骤增加受保护 Open 报告，并把 Simulation、Workflow、UI 报告适配为诚实的复数子树、API/MCP、版本记录、锁定和产品主线摘要。

BI 只负责可见性，不是第二套权威状态或执行系统。2.4.1 桌面窗口仍只显示已授权的合成去敏 Snapshot；真实项目适配器尚未实现。它不读取或修改项目文件，不暴露原始身份/证据，不解析下层方法材料，也不控制 Agent 或 runtime；缺失事实显示为“未知”或“未记录”。完整投影与安全边界见 [`lc-coding/references/built-in-bi.md`](lc-coding/references/built-in-bi.md)。

## Slice 执行准入与 Owner gap

Feature Slice 只有在产品级 Execution Coverage Preflight 通过后才能进入 SLK/CLK/GLK。尚未证明的跨层连接必须由最薄但生产级的首个贯通 Run 证明，或引用充分的既有证据；该 Run 失败时不得继续扩展。LCCoding只定义准入和交接，GO/CELL 内部仍归选定 Loop。

Owner 的 rework、definition change 或 defer 会得到稳定 gap ID。阻断性 gap 必须沿 Impact Analysis 或 Calabash 路由、修正 Run、受影响 D0–D3、增量复验和 Owner 再验收关闭；权威状态只索引开放 gap 与证据指针，不成为 gap 档案库。

## 逻辑子树基线保护

Product Baseline 锁定总项目精确 commit、每个已实现 UI/Workflow/Simulation 子树的名称、路径、组件版本、内容 hash、组合关系和 Owner 确认的产品主线。`UI=LOCKED` 钉住适用 UI 子树在同一总项目 commit 下的身份；每个 Slice 在开工前与验收前比较该子树，只有经批准的 Baseline Change Request 才能更新锁定基线。

## 两种 Owner Acceptance

### 1. Loop Owner Acceptance

每个正常的 SLK、CLK、GLK Run 在 D3 通过后，由该 Run 的 Supervisor 组织 Owner 验收。

```text
Run D3 PASS
      ↓
Supervisor 准备候选、账号、场景和步骤
      ↓
LOOP_OWNER_ACCEPTANCE
```

一个 Feature Slice 包含多个 Run 时，Owner 按 Run 分段验收。每次只看一个已经完成的小范围结果，不把所有内容堆到项目末尾。

有效结果：

```text
LOOP_OWNER_ACCEPTED
LOOP_PRODUCT_REWORK
LOOP_PRODUCT_DEFINITION_CHANGE
LOOP_OWNER_DEFERRED
```

只有所有 Required Run 都取得 `LOOP_OWNER_ACCEPTED`，才形成进入集中安全阶段的 Accepted Candidate。

### 2. Post-Security Owner Acceptance

所有正常 Run 验收完成后，立即进行一次集中的漏洞审计。漏洞修复会改变最终 Candidate，因此安全闭环后必须再进行一次 Owner Acceptance。

这一次不是重验整个项目，而是：

- 复用全部 Loop Owner Acceptance Receipt；
- 只检查安全修复影响到的 UI、Workflow 和关键路径；
- 对没有改变的已验收区域不重复验收；
- 至少走一条关键端到端 Smoke Route；
- 确认安全修复没有破坏此前接受的产品行为。

输出：

```text
POST_SECURITY_OWNER_ACCEPTED
POST_SECURITY_PRODUCT_REWORK
POST_SECURITY_OWNER_DEFERRED
```

## 四个阶段

阶段只是给主干分段，不创建第二套生命周期：

| 阶段 | 覆盖范围 | 出口 Gate |
|---|---|---|
| `INITIAL` | Owner Proposal、PRC、Project Initialization | `INITIAL_READY`，进入 Calabash Draft |
| `PRODUCT_FORMATION` | Calabash Draft、Workflow、UI、Simulation World | `CALABASH_UPGRADE_READY`，进入 Mandatory Calabash Upgrade |
| `ENGINEERING_RUNS` | Calabash Upgrade、Product Baseline、Feature Slice、Integration、单个 Loop Run、D0–D3 | 每个 Run 输出 `LOOP_OWNER_ACCEPTANCE_READY`；全部通过后输出 `ALL_REQUIRED_RUNS_ACCEPTED` |
| `DELIVERY_PREPARATION` | 集中漏洞审计、修复、独立复验、Post-Security Owner Acceptance、交付方式问答和 Package 检查 | `DELIVERY_READY` |

`ENGINEERING_RUNS` 是可重复阶段：一个 Run 验收后，如果还有 Run，就继续下一轮；不会等到所有 Run 做完以后才让 Owner 一次性验收。

## 集中漏洞检测与排除

漏洞检测不分散成多次正式安全验收，而是在所有正常 Run 已经 Owner-Accepted 后集中进行一次。

### 独立 Security Auditor

必须建立一个新的独立 Security Auditor Agent：

- 未参与该 Candidate 的 Worker 工作；
- 未担任 Checker；
- 未签发 D2/D3；
- 未担任 Run Supervisor；
- 未替 Owner 做前面的产品验收；
- 使用独立 Context、Workspace 和 Evidence。

Security Auditor 负责审计和复验，**不能自己修自己发现的问题**。

### 集中流程

```text
ALL_REQUIRED_RUNS_ACCEPTED
      ↓
CENTRALIZED_VULNERABILITY_AUDIT
      ↓
Security Findings
      ↓
独立工程角色完成 Security Remediation
      ↓
Security Auditor Re-audit
      ↓
VULNERABILITY_CLOSED
      ↓
POST_SECURITY_OWNER_ACCEPTANCE
      ↓
Delivery Method Q&A
```

第一次集中审计要覆盖最终 Accepted Candidate 的完整已定义攻击面，不只是增量扫描。D0–D3 已有的安全证据可以复用，但它们不能替代集中安全结论。

修复后只重跑被修改 Candidate 影响到的 D0–D3 Evidence 和安全检查；Security Auditor 负责最终复验并签发 Closure Receipt。

以下问题必须关闭：

- Critical / High 漏洞；
- Secret Exposure；
- Authentication Bypass；
- Privilege Escalation；
- Cross-customer / Cross-tenant Data Leakage。

## Verification 去重

```text
D0  Worker Self-Check
D1  Checker CELL Acceptance
D2  独立 GO Verification
D3  独立 Stage / Run / Final Verification
```

每层只验证自己的 Claim。高层引用低层 Receipt，只在 Candidate 改变、证据过期或矛盾、环境变化、组合改变结果、回归范围扩大或存在明确风险时重复检查。

正式漏洞审计不嵌入每个 D0–D3 层级。局部安全断言可以存在，但集中 Security Auditor 才拥有最终漏洞结论权。

## 交付方式确认

Post-Security Owner Acceptance 通过后，必须针对当前客户执行 Delivery Method Q&A，不能盲目套用默认方式。

AI 先读取 Owner Policy、Project Profile、客户合同和已确认事项，只询问本次尚未确定的内容，并给出推荐答案与选项。至少确认：

- SaaS、我方托管、客户私有部署、安装包或其他模式；
- 实际包含和排除的资产；
- 源码、修改权、转移权和部署范围；
- Runtime、基础设施和网络；
- 数据迁移、备份和责任；
- LCagent、LCapi 等内部依赖如何使用但不交付；
- License、期限、席位、站点、升级、支持和维护；
- 上线、回滚、凭证和后续运维。

内部 LC 资产禁交付规则仍然是 Owner Policy，不作为普通客户选项。
