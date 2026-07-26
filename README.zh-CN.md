# LCCoding 1.1.0

LCCoding 是一套 **人负责产品、AI 负责工程** 的人机协同开发方法。

## 主结构

```text
Calabash：先建立，并在全过程持续演化
                    ↕
Workflow 能力端 ← Feature Integration → UI 用户端
                    ↕
                 拟真世界
                    ↓
           AI Verification + Owner 验收
                    ↓
             影响分析与同步迭代
```

## 1.1.0 新增：连接基座锁定

连接阶段必须牺牲一端的灵活性，才能让工作收敛。默认规则是：

```text
UI = 锁定
Workflow = 受控可调整
Simulation = 版本化可调整
Calabash = 持续演化并记录影响
```

UI 在设计阶段可以充分迭代；一旦进入某个 Feature 的连接阶段，Owner 已接受的
UI 就成为固定施工目标。AI 必须让 Workflow 和工程实现去适配 UI，不得为了容易
实现而改布局、删功能、换交互、改名称或降低产品质量。

只有两种方式可以改变锁定 UI：

1. Owner 主动要求；
2. AI 提交 `BASELINE_CHANGE_REQUEST`，说明冲突、证据、替代方案和影响范围，
   获得 Owner 明确批准。

未经批准修改锁定 UI，记为 `BASELINE_LOCK_VIOLATION`，该候选不能验收。

## 初始化

```bash
python lc-coding/scripts/bootstrap_lccoding.py \
  --project /path/to/project \
  --name "项目名称" \
  --profile PRODUCT
```

## 关键模板

- `FEATURE-SLICE.md`：端到端功能切片
- `INTEGRATION-BASELINE.md`：连接基座与 UI 锁定记录
- `BASELINE-CHANGE-REQUEST.md`：基座解锁/变更申请
- `SIMULATION-WORLD.md`：拟真世界
- `IMPACT-ANALYSIS.md`：影响分析
- `WORKING-CONTRACT.md`：人机工作契约
