# 时间机器与真因果运营升级记录（23 之后）

## 0. 本文定位

本文记录在 `docs/23-business-logic-closure-acceptance.md`（业务闭环验收）之后所做的全部升级，供二次验收人员或其他 AI agent 对照。23 解决了“有没有业务闭环链路”的问题；本次升级解决“这条链路是不是真业务逻辑、操作有没有真实后果”的问题。

一句话概括三块升级：

```text
① 闭环真实性修复：把演示味较重的伪造数据改成可解释的“估算口径”，修回回归 bug
② 时间机器 + 真因果：把静态数据集变成可推进的时间线，关闭工单会真实改写该设备“未来”的读数
③ 未来故障排程：保证不断推进时间总会冒出“先前正常、后来才坏”的新设备，且修过的设备永不复发
```

## 1. 升级背景与动机

23 验收时系统已能跑通“异常发现 → 派单 → 处理 → 复核 → 关闭 → 日报”链路，但存在两个本质短板：

1. **后果是假的。** 工单关闭后展示的“处理后能耗/COP”是用固定系数凭空算出来的，且数据集是 4–6 月的静态快照，关不关工单对后续数据毫无影响——演示再流畅也只是“走流程”。
2. **时间是死的。** 每次打开系统看到的都是同一批历史异常，无法体现“今天处理了、明天就好转”这种运维价值。

本次升级围绕“**让操作产生真实、可观察、可回溯的后果**”展开。

## 2. 升级① 闭环真实性修复

### 2.1 回归 bug 修复

| 文件 | 问题 | 修复 |
| --- | --- | --- |
| `frontend/vite.config.js` | 代理目标被改成 `127.0.0.1:8001`，与后端默认 `8000` 不符，开发模式前后端断连 | 改回 `8000` |
| `backend/app/schemas/work_order.py` | `WorkOrderCreate` 默认 `status="处理中"`，导致未派单工单被错误归一为 `in_progress`，跳过 `pending_confirm` | 改为 `status: Optional[str] = None`，由服务层判定 |

### 2.2 处理前后对比落地

- `WorkOrderCreate` 增加 `before_kwh` / `before_cop` 字段；前端 `DashboardView.vue` 生成工单时把异常记录的 `electricity_kwh`、`average_cop` 作为基线一并写入，使“处理前/处理后”对比在标准派单链路里真正可用（此前主链路会丢掉基线）。

### 2.3 把“伪造后果”改成“显式估算”

- `work_order_store.py` 抽出常量 `ESTIMATED_KWH_RECOVERY_FACTOR = 0.78`、`ESTIMATED_COP_RECOVERY_FACTOR = 1.15`，仅在工人勾选“恢复确认”且存在基线时才估算 `after_kwh` / `after_cop`，并 `round(_, 2)`。
- 新增 `after_is_estimated` 标志贯穿存储 (`_normalize_order`)、归一与展示。
- `analysis_service.build_operation_report` 在估算口径下给节能/COP 摘要加“预计”前缀。
- 前端在“处理前后能耗对比”标题旁显示 `处理后为估算值` 标签。

> 口径说明：系统不再谎称“实测节能 X%”，而是诚实标注“**预计**节能（基于基线与恢复系数估算）”。

## 3. 升级② 时间机器与真因果干预

### 3.1 核心服务 `simulation_service.py`（新增）

服务端维护一个“仿真时钟”状态文件 `sim_state.json`（位于运行时目录，不入库）：

| 字段 | 含义 |
| --- | --- |
| `current_date` | 当前仿真日期指针，为空表示**仿真未启动**（此时所有变换均为 no-op，旧行为/旧测试不受影响） |
| `start_date` | 本轮仿真起始日（用于锚定未来故障排程，见升级③） |
| `interventions` | 已修复设备列表，每项 `{equipment_id, from_date}` |

三个纯函数式数据变换（只接收并返回 DataFrame，不反向依赖 `data_loader`，保持依赖无环）：

- `apply_window(frame)`：隐藏 `current_date` 之后的数据——“未来”不可见。
- `apply_interventions(frame)`：对已修设备，从修复日起把读数拉回所在建筑的健康基线，使其后续不再触发任何异常规则。
- `apply(frame) = apply_window(apply_interventions(apply_injections(frame)))`：完整变换（`apply_injections` 见升级③）。

默认起始日 `DEFAULT_START_DATE = "2026-05-01"`。

### 3.2 数据管道收口

- `data_loader.py` 新增 `get_visible_dataset()`，对外作为“仿真感知”的统一数据入口；`get_filtered_dataset` 也接入窗口与干预。
- 将 `anomaly_event_service`、`admin_dashboard_service`、`assistant_service` 的取数从 `read_dataset()` 切到 `get_visible_dataset()`，确保看板、异常详情、智能问答都遵循当前仿真时间。

### 3.3 真因果链路

`work_order_store.review_work_order` 在**复核通过**时调用 `simulation_service.register_intervention(equipment_id)`：关闭工单 = 在仿真世界登记一次维修，从当天起该设备“未来”的读数被改写为正常。修了就会好，不修就持续异常。

### 3.4 接口与前端

- 新增 `/api/v1/sim` 路由：`GET /state`、`POST /start`、`POST /advance`、`POST /reset`。
- `frontend/src/lib/api.js` 新增 `fetchSimState` / `startSimulation` / `advanceSimulation` / `resetSimulation`。
- `DashboardView.vue` 新增“运营沙盘 · 时间机器”控制条：显示当前仿真日期、数据范围、干预次数，提供“开始 / 下一天 / 下一周 / 重置”。

## 4. 升级③ 未来故障排程（本次重点）

### 4.1 解决的问题

实测原始数据只有 **28 个合成设备**，且到 5/10 前**全部都已经异常过**；5/10 之后的异常 **100% 来自这些老设备，无任何“先正常、后来才坏”的新设备**。后果：若某天把当天可见异常全部修复，再不断点“下一天”将**永远不再出现新异常**（演示死局）。

### 4.2 排程机制

`simulation_service` 新增确定性“未来故障排程”，并保留“修复后不再异常”逻辑：

- 常量：`SCHEDULE_FIRST_OFFSET_DAYS = 3`、`SCHEDULE_STEP_DAYS = 3`、`SCHEDULE_PICK_EVERY = 2`。
- `_failure_schedule(...)`：把每隔一个的设备（约一半）排入未来，第一台在起始日 +3 天发病，之后每 3 天再来一台。
- `apply_injections(frame)`：被排程设备在其**发病日之前一直显示正常**（且处于不可见的未来），到发病日才突然故障。因为发病前它“看着正常又看不见”，操作者无法提前修，于是**每隔几天必然蹦出一个全新异常设备**。
- `get_scheduled_failures()`：对外暴露排程（设备 + 发病日），可用于诊断或前端提示。

变换顺序为 `window(interventions(injections(frame)))`：若操作者在发病后修了某台被排程设备，干预会从修复日起覆盖故障注入，使其恢复——排程与因果不冲突。

### 4.3 批量修复稳健性修复

异常检测用的是“高于同建筑 `均值+标准差`”的相对阈值。一次性修很多台会让基线坍缩，导致被修设备又被重新判为“相对偏高”。两处修复：

1. **冻结基线快照**：干预/注入在循环前先 `copy()` 一份原始帧再计算各自基线，互不污染。
2. **恢复到低分位**：被修设备读数恢复到所在建筑健康区间的**第 15 百分位**（`electricity_low` / `hvac_low`），稳稳落在底部。无论一次修 1 台还是全修，**被修设备都稳定离开异常列表**。

### 4.4 数据印证（start=5/01，且“5/01 当天可见异常全修”）

```text
5/04 起持续蹦新设备：AHU-A-3F-02(5/04) → AHU-A-5F-02(5/07) → AHU-C-4F-02(5/10)
                    → AHU-C-5F-02(5/13) → AHU-D-1F-02(5/16) ...
被修设备：修复日之后零异常；新坏的设备修完同样不再复发
```

## 5. 变更文件清单

### 后端

| 文件 | 变更 |
| --- | --- |
| `app/services/simulation_service.py` | **新增**：时钟状态、窗口、真因果干预、未来故障排程、低分位恢复 |
| `app/api/routes/simulation.py` | **新增**：`/sim` 接口 |
| `app/api/router.py` | 挂载 `/sim` 路由 |
| `app/services/data_loader.py` | 新增 `get_visible_dataset()`，接入仿真变换 |
| `app/services/work_order_store.py` | 估算常量、`after_is_estimated`、复核通过登记干预 |
| `app/services/analysis_service.py` | 运营日报“预计”口径 |
| `app/services/anomaly_event_service.py` | 改用 `get_visible_dataset()` |
| `app/services/admin_dashboard_service.py` | 改用 `get_visible_dataset()` |
| `app/services/assistant_service.py` | 改用 `get_visible_dataset()` |
| `app/schemas/work_order.py` | 新增 `before_kwh`/`before_cop`，修正默认 `status` |

### 前端

| 文件 | 变更 |
| --- | --- |
| `src/views/DashboardView.vue` | 时间机器控制条、处理前后对比与“估算值”标签 |
| `src/lib/api.js` | 仿真接口客户端函数 |
| `vite.config.js` | 代理端口回退 8000 |

### 测试

| 文件 | 内容 |
| --- | --- |
| `backend/tests/test_business_upgrade.py` | **新增** 8 项：基线持久化、`pending_confirm` 修正、估算值计算与四舍五入、自动确认队列幂等、日报“预计”措辞 |
| `backend/tests/test_simulation.py` | **新增** 7 项：默认不激活、窗口隐藏未来、推进揭示更多数据、干预恢复设备、**未来持续产生新异常且修复后不复发**、`/sim` 接口往返、关闭工单登记干预 |

## 6. 验收清单（在 23 基础上的增量）

### 6.1 真实性口径验收

| 编号 | 检查项 | 操作 | 期望结果 |
| --- | --- | --- | --- |
| EST-01 | 处理前基线写入 | 标准派单链路创建工单 | 工单含非空 `before_kwh` / `before_cop` |
| EST-02 | 估算值口径 | 工人勾选恢复确认并提交、管理员关闭 | `after_kwh≈before×0.78`、`after_cop≈before×1.15`，均两位小数，`after_is_estimated=true` |
| EST-03 | 未恢复确认不估算 | 工人不勾选恢复确认 | `after_is_estimated=false`，不展示伪造节能 |
| EST-04 | 日报措辞 | `GET /api/v1/analytics/operation-report` | 估算口径下摘要含“预计”字样 |
| EST-05 | 待确认状态 | 创建未派单工单 | `status=pending_confirm`（不再误判为处理中） |

### 6.2 时间机器与真因果验收

| 编号 | 检查项 | 操作 | 期望结果 |
| --- | --- | --- | --- |
| SIM-01 | 默认不激活 | 未调用 `/sim/start` 时取数 | 返回完整数据集，行为同旧版 |
| SIM-02 | 启动仿真 | `POST /api/v1/sim/start` | `state.active=true`，`current_date=start_date=2026-05-01` |
| SIM-03 | 窗口隐藏未来 | 启动后查看异常 | 可见数据最大时间戳 ≤ 当前仿真日 |
| SIM-04 | 推进时间 | `POST /api/v1/sim/advance`（days=1/7） | `current_date` 前移，可见数据增多 |
| SIM-05 | 真因果恢复 | 关闭某设备工单后继续推进 | 该设备自修复日起不再出现异常 |
| SIM-06 | 重置 | `POST /api/v1/sim/reset` | 回到未激活状态 |

### 6.3 未来故障排程验收

| 编号 | 检查项 | 操作 | 期望结果 |
| --- | --- | --- | --- |
| SCH-01 | 排程可见 | 调 `get_scheduled_failures()` 或观察推进 | 每隔约 3 天有一台“先前正常”的设备发病 |
| SCH-02 | 死局排除 | 起始日把当天可见异常全部修复，再连续推进 | 后续仍不断冒出全新异常设备（非已修设备） |
| SCH-03 | 批量修复稳健 | 一次性修复多台 | 被修设备全部稳定离开异常列表，不被相对阈值重新误判 |
| SCH-04 | 新坏设备亦可治理 | 对排程发病设备派单关闭 | 自修复日起不再复发 |

### 6.4 自动化测试与回归

| 编号 | 检查项 | 命令 | 期望结果 |
| --- | --- | --- | --- |
| TST-21 | 后端全量测试 | `python -m pytest backend\tests -q` | `101 passed`（23 基线 86 → 现 101） |
| TST-22 | 升级专项测试 | `python -m pytest backend\tests\test_business_upgrade.py backend\tests\test_simulation.py -q` | 全部通过 |
| TST-23 | 未来异常守恒 | `pytest -k test_future_keeps_producing_new_anomalies` | 通过：未来持续产新异常且修复后不复发 |

## 7. 验收结果

已执行：

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests -q
```

- 后端测试：`101 passed`（相比 23 的 `86 passed` 新增 15 项）。
- 无 lint 报错；临时诊断脚本均已清理。

## 8. 演示建议（在 23 链路上叠加）

1. `admin / admin123` 登录，进“总览”，在时间机器控制条点击“开始仿真”（落在 5/01）。
2. 在工单中心选一条异常派单，切工人账号接单、填写原因/结果并勾选恢复确认提交。
3. 切回管理员复核通过关闭——此刻已在仿真世界登记一次维修。
4. 连续点“下一天”：被修设备保持正常，**而先前正常的设备（如 AHU-A-3F-02 等）会按排程陆续发病**，形成“边修边来、修好不复发”的真实运维节奏。
5. 打开“决策报告”，展示已关闭工单计入运营日报，且节能口径标注“预计”。
6. 需要复位演示时点击“重置”。

## 9. 参数与可调项

| 参数 | 文件 | 默认 | 含义 |
| --- | --- | --- | --- |
| `DEFAULT_START_DATE` | `simulation_service.py` | `2026-05-01` | 仿真默认起始日 |
| `SCHEDULE_FIRST_OFFSET_DAYS` | `simulation_service.py` | `3` | 第一台排程设备发病距起始日的天数 |
| `SCHEDULE_STEP_DAYS` | `simulation_service.py` | `3` | 之后每台排程设备发病的间隔天数（调小=异常更密） |
| `SCHEDULE_PICK_EVERY` | `simulation_service.py` | `2` | 每隔几台抽一台进入排程（调小=排程设备更多） |
| `ESTIMATED_KWH_RECOVERY_FACTOR` | `work_order_store.py` | `0.78` | 估算处理后电耗系数 |
| `ESTIMATED_COP_RECOVERY_FACTOR` | `work_order_store.py` | `1.15` | 估算处理后 COP 系数 |
