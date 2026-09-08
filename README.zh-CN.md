# LCCoding 4.0.0

由 Owner 掌握产品方向、AI 完成工程闭环，并通过分段验收与集中独立安全闭环形成受保护交付。

## 方法概览

Source clauses: [LC-PHASE-001](SPEC.md#lc-phase-001), [LC-PHASE-002](SPEC.md#lc-phase-002), [LC-PHASE-003](SPEC.md#lc-phase-003), [LC-PHASE-004](SPEC.md#lc-phase-004), [LC-PHASE-005](SPEC.md#lc-phase-005)

```text
Owner Proposal
→ LCCoding Applicability Assessment
→ Proposal Readiness 与 Product Service Strategy
→ Project Initialization
→ Calabash Draft
→ Service Route Map
→ [先建立 Simulation World foundation → 共享 Workflow ∥ 适用的 route/service surface ∥ 人可观察结果]
→ Mandatory Calabash Upgrade
→ Product Baseline
→ route-bound Feature Slice 与 Real Product Integration（真实产品集成）
→ 每个 Run 的 Independent layered Verification 与 Owner Acceptance
→ route-faithful Real User Journey Acceptance（真实用户旅程验收）
→ 集中安全闭环与安全后 Owner 验收
→ Delivery Preparation
→ Delivery
```

五个人类阶段是 Initial（`INITIAL`）、Product Formation（`PRODUCT_FORMATION`）、Real Product Integration（真实产品集成）、Real User Journey Acceptance（`REAL_USER_JOURNEY_ACCEPTANCE`，真实用户旅程验收）和 Delivery Preparation（`DELIVERY_PREPARATION`）。精确 2.6/2.7 兼容读取仍可使用第三阶段 ID `ENGINEERING_RUNS`，但它不是人类阶段名。

进入生命周期前，LCCoding 先判断整个产品或一个完整且有边界的产品范围是否适合本方法；不适合时给出 `OTHER_METHOD_RECOMMENDED`，但不会否定底层工程工作。被接纳的产品记录 `PLATFORM_COMPLETION`、`AGENT_COLLABORATIVE`，或两者并存的 `MIXED`，再由 Calabash 在同一份 Service Route Map 中定义必需的直接产品、Personal Agent 与 Service Center 路径。

为保持精确 3.0 读取兼容，`[先建立 Simulation World foundation → Workflow 能力端 ∥ UI 产品呈现端分别推进]` 仍表示直接产品路径的 formation 形态，但不支配 4.0 route-aware 写入。

## 产品与执行摘要

Source clauses: [LC-FORM-001](SPEC.md#lc-form-001), [LC-FORM-002](SPEC.md#lc-form-002), [LC-FORM-003](SPEC.md#lc-form-003), [LC-INTEG-001](SPEC.md#lc-integ-001), [LC-RUN-001](SPEC.md#lc-run-001), [LC-RUN-003](SPEC.md#lc-run-003)

Product Formation 先建立至少一个最小、真实可运行、带版本的 Simulation World foundation；之后共享 Workflow 与 Service Route Map 承诺的 route/service surface 才作为真实产品端分别独立向前建设，只有路径本身承诺图形界面时才要求 UI。后续 route-bound Feature Slice 从真实入口到人可观察业务结果逐条证明必需路径，并复用未受影响的共享 Workflow/Backend/Core 证据。

对于精确 3.0 直接产品 formation 路径，Workflow 与 UI 才作为同等产品端分别独立向前建设，跨层连接与贯通证明仍由后续 Feature Slice 和 UI-locked Integration 负责。这一保留的读取含义不会把 UI 强加到其他 4.0 路径。

集成 Runs 被接受后，第四阶段从每条必需路径的真实外部入口出发，执行有边界的真实用户旅程图；有意义的可见操作用截图证明，非可视 Agent 步骤用绑定候选的消息、任务、授权事件、产物、平台效果、结果交付与审计事件证明。每条被接受的路径最终都必须让人类受益者看到并理解业务结果，随后才能进入交付准备。

SLK、CLK、GLK 与其他已登记兼容方法组成 cross-phase execution axis（跨阶段执行轴），not a lifecycle node（不是生命周期节点），也不是方法全集。Run 只把证据交回调用阶段，详细含义由 SPEC 定义。

## 方法来源、适配与贡献

Source clauses: [LC-AUTH-001](SPEC.md#lc-auth-001), [LC-AUTH-002](SPEC.md#lc-auth-002)

LCCoding 源自 Owner 的个人能力、知识结构和经常处理的项目实践。其他人可以借鉴并按自己的能力、知识范围和项目条件微调，同时保持清晰的权威和证据边界。

欢迎讨论和贡献。Owner 维护的仓库仍是规范主线；外部调整是贡献或明确标识的变体，不能静默替换规范含义。

## 权威与专题导航

Source clauses: [LC-AUTH-002](SPEC.md#lc-auth-002)

- 权威入口：[SPEC](SPEC.md)、[Constitution](CONSTITUTION.md)、[操作 Skill](lc-coding/SKILL.md)。
- 起步导航：[固定生命周期与比例深度](SPEC.md#lc-auth-002)、[Proposal Readiness](lc-coding/references/proposal-readiness.md)、[Project Initialization](lc-coding/references/project-initialization.md)。
- 产品施工：[Feature Slice 与集成](lc-coding/references/feature-slice-and-integration.md)、[执行方法选择](lc-coding/references/loop-method-selection.md)。
- Agent-native 集成：[专题操作导航](lc-coding/references/agent-native-integration.md)。
- 证据与交付：[Loop Owner Acceptance](lc-coding/references/loop-acceptance-boundary.md)、[漏洞闭环](lc-coding/references/vulnerability-closure.md)、[交付治理](lc-coding/references/delivery-governance.md)。
- 内置 BI：[方法/产品合同](lc-coding/references/built-in-bi.md)；[实现、构建与测试导航](lc-coding/bi/README.md)。
- 语言：[English overview](README.md)。

## 验证

Source clauses: [LC-AUTH-002](SPEC.md#lc-auth-002)

在仓库根目录运行 `python lc-coding/tests/run_tests.py` 与 `python lc-coding/scripts/validate_repository.py .`。
