# LCCoding 2.6.0

由 Owner 掌握产品方向、AI 完成工程闭环，并通过分段验收与集中独立安全闭环形成受保护交付。

## 方法概览

Source clauses: [LC-PHASE-001](SPEC.md#lc-phase-001), [LC-PHASE-002](SPEC.md#lc-phase-002), [LC-PHASE-003](SPEC.md#lc-phase-003), [LC-PHASE-004](SPEC.md#lc-phase-004)

```text
Proposal Readiness
→ Project Initialization
→ Calabash Draft
→ [先建立 Simulation World foundation → Workflow 能力端 ∥ UI 产品呈现端分别推进]
→ Mandatory Calabash Upgrade
→ Product Baseline
→ Feature Slice
→ 锁定 UI 的 Real Product Integration（真实产品集成）
→ 独立分层 Verification
→ Owner Acceptance
→ Delivery
```

四个人类阶段是 Initial（`INITIAL`）、Product Formation（`PRODUCT_FORMATION`）、Real Product Integration / 真实产品集成（兼容状态 ID `ENGINEERING_RUNS`）和 Delivery Preparation（`DELIVERY_PREPARATION`）。`ENGINEERING_RUNS` 只解释机器兼容状态，不是人类阶段名。

## 产品与执行摘要

Source clauses: [LC-FORM-001](SPEC.md#lc-form-001), [LC-FORM-002](SPEC.md#lc-form-002), [LC-FORM-003](SPEC.md#lc-form-003), [LC-INTEG-001](SPEC.md#lc-integ-001), [LC-RUN-001](SPEC.md#lc-run-001), [LC-RUN-003](SPEC.md#lc-run-003)

Product Formation 先建立至少一个最小、真实可运行、带版本的 Simulation World foundation；之后 Workflow 与 UI 才作为同等产品端分别独立向前建设。跨层连接与贯通证明仍由后续 Feature Slice 和 UI-locked Integration 负责。

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
- 证据与交付：[Loop Owner Acceptance](lc-coding/references/loop-acceptance-boundary.md)、[漏洞闭环](lc-coding/references/vulnerability-closure.md)、[交付治理](lc-coding/references/delivery-governance.md)。
- 内置 BI：[方法/产品合同](lc-coding/references/built-in-bi.md)；[实现、构建与测试导航](lc-coding/bi/README.md)。
- 语言：[English overview](README.md)。

## 验证

Source clauses: [LC-AUTH-002](SPEC.md#lc-auth-002)

在仓库根目录运行 `python lc-coding/tests/run_tests.py` 与 `python lc-coding/scripts/validate_repository.py .`。
