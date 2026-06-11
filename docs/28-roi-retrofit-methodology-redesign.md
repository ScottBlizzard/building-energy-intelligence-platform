# 28 · 改造分析（ROI）方法学重构设计

> 目的：把"节能改造经济性分析"从**演示级**升级为**经济学上站得住脚**的实现，做到数据真实、口径一致、方法规范，能正面回答懂经济学的评审追问。
> 状态：**已实现（2026-06-12，L2 数据清洗）**。`roi_service.py` 已按本文 §2/§3 重写：实测门控、增量法投资、能效差节能率、8% 折现率 + 5/8/10% 敏感性、EAA、动态回收期、含碳价情景；`decision_service` 候选池文案区分"已建单累计损失/可见异常估损"；前端 `ROIPanel.vue` 展示 EAA/动态回收期/折现率/口径标注与"无数据"徽标。预算季节系数口径见 `docs/29 §3.2`。
> 关联：`docs/19-SEE-software-economic-evaluation.md`（经济评价）、`docs/23`、`docs/24`、`docs/29`（验收）。

---

## 0. 一句话目标

改造分析里出现的每一个数字，都能用"实测能耗 + 公开参数 + 规范方法"复算出来；不存在凭空兜底、不存在自相矛盾、不同寿命方案用正确口径比较。

---

## 1. 现状问题清单（重构前基线）

| # | 严重度 | 问题 | 位置 |
|---|---|---|---|
| 1 | 🔴 | 对该楼**不存在/不运行**的设备也算 ROI（实测电耗=0 仍用铭牌典型值出结果） | `roi_service._retrofit_candidates` 的 `max(total_kwh, power_kw*runtime)` |
| 2 | 🔴 | 顶部方案卡（兜底典型值）与对比表（真实值）**基线口径不一致** → 同设备"4.4 年回本" vs "永不回本" | `_retrofit_candidates` vs `analyze_roi_project` |
| 3 | 🔴 | **硬造收益**：节省≤0 时强行塞 `annual_cost*0.15` | `roi_service.py` `analyze_roi_project` |
| 4 | 🟠 | 节能率写死（变频20%/高效35%/智能12%/综合28%），无依据、无能效差调节 | `_RETROFIT_OPTIONS` |
| 5 | 🟠 | 不同寿命（8/12/14/15 年）方案**直接比原始 NPV**，未用 EAA/共同周期 | `compare_scenarios` |
| 6 | 🟡 | 折现率 5% 偏松，无敏感性分析 | `_ANNUAL_DISCOUNT_RATE` |
| 7 | 🟡 | 电价 15 年恒定、碳减排未货币化 | 全局假设 |
| 8 | 🟡 | 投资用全价，未用"增量法"（到寿命更换应只算高效差价） | `_RETROFIT_OPTIONS` cost_per_kw |
| 9 | ⚪ | 改造候选池"损失约 0 元"=旧工单无 `wasted_cost_yuan`（已在 #6 修复，重置后消失） | `decision_service.find_roi_candidates_from_repeated_anomalies` |
| 10 | ⚪ | 设备诊断遍历全数据集设备类型，展示该楼没有的设备并标"低效" | `roi_service.build_equipment_audit` |

---

## 2. 目标方法学（核心公式）

### 2.1 基线能耗（必须真实）
被改造设备的年化电耗以**实测**为准：

```
annual_kwh = observed_kwh / observed_days * 365
```

- `observed_kwh` = 该楼该设备类型在可见窗口内的实测电耗（沙盘可见数据）。
- **若 equipment_count == 0 或 observed_kwh == 0 → 不产生该设备的改造方案**（从源头消除问题 1/2/10）。
- 不再使用 `max(实测, 铭牌典型)` 兜底；典型值只允许作为"数据不足提示"，且必须显式标注 `basis = "行业典型基线（实测不足）"`，并默认**不参与推荐结论**。

### 2.2 年节省（节能率有据 + 能效差调节）
```
base_saving_pct  = 规范/文献给定的措施基准节能率
adj_saving_pct   = base_saving_pct * efficiency_gap_factor
annual_energy_saving_kwh  = annual_kwh * adj_saving_pct
annual_cost_saving_yuan   = annual_energy_saving_kwh * price_t   # price_t 见 2.5
annual_net_cashflow_t     = annual_cost_saving_yuan - delta_oNm  # 增量运维
```

- `efficiency_gap_factor`：当前能效越差、可挖潜越大。建议用当前 COP 与目标 COP 的差归一化，例如
  `gap = clamp((cop_target - cop_now)/cop_target, 0.5, 1.3)`；COP 已达标的设备拿不到满额节能率。
- **删除 `if saving<=0: saving=cost*0.15`**。净节省≤0 就如实输出"不经济"。

### 2.3 投资（增量法）
```
若“到寿命更换”：investment = 高效型与标准型差价（efficiency premium）
若“提前更换”  ：investment = 全价 - 旧设备残值(按剩余寿命直线折旧)
变频/智能控制 ：investment = 改造直接成本（本就是增量投入）
```

- 在 `_EQUIPMENT_BASELINE` 增补 `standard_replacement_cost`（标准型）与 `high_eff_premium`（高效差价）。
- 文档中标明每个单价的口径来源（参数估算/询价区间）。

### 2.4 折现率与判据
- **基准折现率 r = 8%**（《建设项目经济评价方法与参数（第三版）》社会折现率）。
- 同时输出 **r = 5% / 8% / 10%** 三档敏感性。

```
NPV  = -I0 + Σ_{t=1..n}  CF_t / (1+r)^t
IRR  : 令 NPV(IRR)=0
EAA  = NPV * [ r(1+r)^n / ((1+r)^n - 1) ]      # 等额年值，跨寿命可比
简单回收期   = I0 / 年净节省（首年）
动态回收期   = 使 Σ 折现CF ≥ I0 的最小年数
```

判据（互斥方案）：
1. 先筛 `NPV(8%) > 0`；
2. 在可行集里**按 EAA 最大**推荐（因为各方案寿命不同，EAA 才公平）；
3. 回收期只作辅助展示，不作主判据。

### 2.5 电价与碳（情景）
```
price_t = price_0 * (1 + esc)^(t-1)     # esc 默认 3%/年，可关闭
含碳价情景：年收益再加 annual_energy_saving_kwh * grid_factor * carbon_price
            grid_factor=0.5703 kgCO2/kWh, carbon_price 默认 ¥/吨（可配置）
```

- 输出"不含碳价/含碳价"两套结论，碳价默认作为加分情景而非主结论。

---

## 3. 对代码的具体改动（实现清单）

### 3.1 `roi_service.py`
- `_building_equipment_stats`：保持实测年化；**新增 `has_real_data` 标志**（equipment_count>0 且 observed_kwh>0）。
- `build_equipment_audit`：`equipment_types` 改为"**该楼实际出现过的类型**"（按 `building_id` 过滤后再 unique），不再遍历全数据集；无数据设备不展示或标注"无此设备/数据不足"，COP=0 不得判"低效"。
- `_retrofit_candidates`：
  - 删除 `max(实测, 典型)`；`has_real_data=False` 时**不产出方案**（或产出但 `basis="典型基线估算"` 且 `advisory_only=True`）。
  - 节能率改为 `adj_saving_pct`（2.2）。
  - 投资改为增量法（2.3）。
  - 增补 `eaa_yuan`、`discounted_payback_years`、`saving_basis` 字段。
- `analyze_roi_project`：
  - 删除 `annual_saving = annual_cost*0.15` 兜底。
  - 折现率默认 8%；`_sensitivity_cases` 增加"折现率敏感性"（5/8/10%）维度。
  - 现金流支持电价递增 `esc`；增加 `with_carbon` 情景输出。
  - 返回新增：`eaa_yuan`、`discounted_payback_years`、`discount_rate`、`price_escalation`、`carbon_price`、`saving_basis`、`investment_basis`。
- `compare_scenarios`：
  - 排序改为 `NPV>0` 过滤后 **按 EAA 最大** 选 best；
  - `recommendation` 文案改用 EAA 口径，并标注折现率与是否含碳价。

### 3.2 `decision_service.py`（改造候选池）
- `find_roi_candidates_from_repeated_anomalies`：损失字段已随 #6 修复，无需改逻辑；建议在 `reason` 里区分"累计已建单损失"与"可见异常估损"，避免重置前出现 0。

### 3.3 `budget_service.py`（口径说明，非本次重点）
- 季节系数与同月基线**重复计入季节性**的问题单独评估（见 `docs` 后续条目）；本次至少在 UI/文案标明"预算=节能目标线（运行水平×目标系数），超额=按现状运行将超目标"。

### 3.4 前端 `DashboardView.vue` / ROI 组件
- 顶部方案卡与对比表**共用同一份后端结果**（消除两套口径）。
- 展示 NPV、IRR、EAA、动态回收期、折现率档位、是否含碳价、`saving_basis/investment_basis` 来源标注。
- 实测不足的设备显示"数据不足，仅供参考"徽标，不给"推荐/不推荐"硬结论。

---

## 4. 数据契约（关键新增字段）

`analyze_roi_project` 返回新增：
```
discount_rate: float            # 0.08
price_escalation: float         # 0.03
carbon_price_yuan_per_ton: float
npv_yuan / irr_pct              # 既有
eaa_yuan: float                 # 新增，跨寿命可比
discounted_payback_years: float # 新增
saving_basis: str               # "实测×能效差调节后的措施节能率"
investment_basis: str           # "增量差价" / "全价-残值" / "改造直接成本"
scenarios_carbon: {...}         # 含碳价情景
sensitivity: [{discount_rate, npv, eaa, payback}...]
```

---

## 5. 边界与防呆
- `observed_days` 过小（如沙盘首日）→ 年化波动大：年化电耗优先用"同月历史"而非"单日×365"，或对样本天数<7 给出"样本不足"提示。
- 设备无实测 → 不产推荐，不进对比表。
- 净节省≤0 → 如实"不经济"，结论"不推荐"。
- IRR 在常规现金流（先出后入）下唯一，保留二分；净节省≤0 时不报 IRR。

---

## 6. 测试计划（pytest）
1. `test_roi_skips_equipment_without_real_data`：该楼无冷却塔 → 不出现冷却塔方案；对比表与顶部卡一致。
2. `test_roi_no_fabricated_saving`：净节省≤0 时结论为"不推荐"，不出现 0.15 兜底。
3. `test_roi_eaa_ranking`：寿命不同的两方案，按 EAA 排序结果正确（构造一个 NPV 高但寿命长、EAA 反而低的反例）。
4. `test_roi_discount_sensitivity`：5/8/10% 三档 NPV 单调递减。
5. `test_roi_incremental_investment`：到寿命更换用差价、提前更换扣残值。
6. `test_equipment_audit_building_scoped`：审计只含该楼实际设备类型，COP=0 不判低效。
7. 回归：`test_business_upgrade`、`test_simulation` 全过。

---

## 7. 答辩防守要点（速查）
- **折现率**："基准用社会折现率 8%，并做 5/8/10% 敏感性。"
- **不同寿命怎么比**："用等额年值 EAA，而不是直接比 NPV。"
- **高效更换成本**："用增量法——到寿命更换只算高效差价；提前更换扣旧设备残值。"
- **节能率依据**："基准引用措施规范，并按当前 COP 能效差下调，能效已达标的设备不给满额。"
- **回收期**："只作辅助；主判据是 NPV>0 且 EAA 最大；另给动态回收期。"
- **电价/碳**："主结论按电价 3%/年递增、不含碳价；另给含碳价加分情景。"

---

## 8. 实现顺序建议
1. 后端 `roi_service` 口径统一 + 删兜底 + 设备范围收敛（消 🔴1/2/3/10）。
2. 加 EAA / 动态回收期 / 折现率敏感性（补 🟠5/🟡6）。
3. 增量法投资 + 电价递增 + 碳情景（补 🟡7/8）。
4. 前端共用结果、展示新指标与来源标注。
5. 预算季节系数口径单独评估。
