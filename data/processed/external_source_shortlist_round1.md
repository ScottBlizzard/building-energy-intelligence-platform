# 外部数据源简明清单 — 第一轮

**编写人：** 马源胜  
**日期：** 2026-04-23  
**版本：** Round 1  
**目的：** 整理与本项目直接相关的外部数据源，说明各来源与当前数据的对应关系，以及第二轮 AI 集成时可优先参考哪些来源。

---

## 1. 优先级汇总（一览）

| 来源 | 优先级 | 最适合用途 |
|---|---|---|
| BDG2（Building Data Genome Project 2）| ⭐⭐⭐ 最高 | 多建筑时序能耗结构参考、建筑类型分类 |
| SHIFDR | ⭐⭐⭐ 最高 | HVAC 异常行为形态、需求响应事件参考 |
| NYC LL84 | ⭐⭐ 高 | 电耗+水耗同步采集合理性依据、建筑基准参考 |
| AlphaBuilding | ⭐⭐ 高 | 合理模拟 occupancy / HVAC / 环境关系 |
| NREL EULP | ⭐ 中 | 建筑类型负荷形态参考、end-use 分解参考 |

---

## 2. BDG2 — Building Data Genome Project 2

### 基本信息

- **类型：** 真实数据集（非住宅建筑真实采集）
- **规模：** 1,636 栋建筑，3,053 个计量表，两年小时级数据
- **来源：**
  - GitHub 仓库：https://github.com/buds-lab/building-data-genome-project-2
  - 论文：https://www.nature.com/articles/s41597-020-00712-x

### 与本项目的对应关系

| 本项目字段/设计 | BDG2 对应 |
|---|---|
| building_type（teaching/office/library/lab） | BDG2 建筑类型分类（Education/Office/Public Assembly 等） |
| timestamp（3 小时粒度） | BDG2 为 1 小时粒度，本项目稍粗，思路对应 |
| electricity_kwh | BDG2 electricity meter |
| hvac_kwh + cooling_load_kwh | BDG2 cooling_water / heating_water meter |
| environment_temp_c | BDG2 配有 weather data（干球温度） |
| 多建筑并行采集 | BDG2 多建筑结构完全对应 |

### 当前样例数据哪些已参考 BDG2 口径

- 小时级时间粒度（本项目 3 小时是 BDG2 1 小时的合并版）
- 多建筑并行、各建筑 280 条记录均匀分布
- 建筑类型设计（教学楼/办公楼对应 BDG2 Education/Office）

### 哪些字段未来可用 BDG2 增强

- 更细粒度时序曲线（升级到 1 小时粒度时，可用 BDG2 真实建筑走势做形态参考）
- 建筑类型扩展（BDG2 还有 Lodging/Retail/Healthcare 等类型）

### 第二轮建议用法

1. 用于验证"我们的 3 小时粒度数据，日内高峰低谷走势是否与 BDG2 真实数据一致"
2. 如需扩充建筑数量，可参考 BDG2 中 Education 类建筑的真实形态

---

## 3. SHIFDR — HVAC 需求响应数据集

### 基本信息

- **类型：** 真实数据集（HVAC 子系统 + 需求响应）
- **来源机构：** University of Michigan 相关团队
- **数据入口：** https://deepblue.lib.umich.edu/data/collections/vh53ww273
- **相关说明：** https://news.engin.umich.edu/2024/01/large-open-dataset-aims-to-improve-understanding-of-building-electricity-demand-response/

### 与本项目的对应关系

| 本项目设计 | SHIFDR 对应 |
|---|---|
| hvac_kwh 单字段 | SHIFDR 提供设备级 / 子系统级功率，细粒度更高 |
| equipment_status=abnormal | SHIFDR 中 demand response 事件前后设备行为变化 |
| COP 异常告警 | SHIFDR 提供 HVAC 调控效果前后对比，可验证 COP 变化形态 |

### 当前样例数据哪些已参考 SHIFDR

- 异常类型 A（非工作时段高能耗）设计了参考 SHIFDR 设备行为模式
- 异常诊断指南中"设备未关机或误触发"的设计参考了 SHIFDR 中 BAS 调度失效场景

### 当前样例数据哪些未能体现（SHIFDR 口径）

- SHIFDR 中有连续多时段的 demand response 事件（例如：发出调控指令后，HVAC 在接下来 4 小时内的响应变化）
- 当前样例中的异常为**单点异常**，缺乏连续事件序列

### 第二轮建议用法

1. 用于知识库中"需求响应"和"HVAC 调控"相关内容的描述参考
2. 第二轮若要增加"连续异常型"数据，可参考 SHIFDR 中的事件前后变化形态
3. 可用 SHIFDR 的设备行为特征改进 `anomaly_diagnosis_guide.md` 中的 HVAC 调控场景描述

---

## 4. NYC Local Law 84（纽约市建筑能耗与水耗披露）

### 基本信息

- **类型：** 官方政策性公开数据（年度 benchmark 口径）
- **官方说明：** https://www.nyc.gov/site/buildings/codes/energy-and-water-data.page
- **开放数据页面：** https://data.cityofnewyork.us/w/5zyy-y8am/25te-f2tw

### 与本项目的对应关系

| 本项目设计 | NYC LL84 对应 |
|---|---|
| electricity_kwh + water_m3 同步采集 | NYC LL84 同时要求 energy + water 披露 |
| building_type 分类 | NYC LL84 有 property type 分类 |
| 能耗比较分析 | NYC LL84 以 Energy Star score / EUI 为基准 |

### 当前样例数据哪些参考了 NYC LL84

- **water_m3 字段的存在** 有 NYC LL84 等政策性需求支撑（能耗和水耗同时监控在国际上有成熟实践）
- 建筑类型命名参考了 benchmarking 中的常见分类思路

### 当前样例数据哪些未能体现

- NYC LL84 是年度口径，当前数据是 3 小时粒度，不直接可比
- 缺少建筑面积字段，无法计算 EUI（kWh/m²·年）与 NYC LL84 基准比较

### 第二轮建议用法

1. 答辩时解释"为什么同时采集电耗和水耗"：可引用 NYC LL84 背景
2. 若增加建筑面积字段，可参考 NYC LL84 中各 building type 的典型 EUI 范围

---

## 5. AlphaBuilding

### 基本信息

- **类型：** 高保真合成数据集（基于仿真模型生成）
- **数据入口：** https://data.openei.org/submissions/2977
- **DOI：** https://doi.org/10.25984/1784722
- **包含：** HVAC / 照明 / MELs / 人员 / 环境变量，10 分钟粒度

### 与本项目的对应关系

| 本项目字段/设计 | AlphaBuilding 对应 |
|---|---|
| occupancy_density_per_100m2 | AlphaBuilding 有 occupant counts 字段 |
| environment_temp_c + humidity_rh | AlphaBuilding 有 environmental parameters |
| hvac_kwh | AlphaBuilding 有 HVAC end-use |
| cooling_load_kwh | AlphaBuilding 有 cooling 相关字段 |

### 当前样例数据哪些参考了 AlphaBuilding

- `occupancy_density` 与 HVAC 电耗的正相关设计（白天人多 → 制冷需求高）参考了 AlphaBuilding 的仿真逻辑
- 环境温度与 HVAC 负荷的正相关关系同样参考了此类高保真模拟的规律

### 第二轮建议用法

1. 验证当前数据中 occupancy/HVAC/环境变量关系是否符合高保真模拟规律
2. 若需增加 10 分钟粒度数据（进阶功能），可参考 AlphaBuilding 的时间分辨率

---

## 6. NREL End-Use Load Profiles

### 基本信息

- **类型：** 基于建筑能耗模型生成的合成数据
- **官方入口：** https://www.nrel.gov/buildings/end-use-load-profiles.html
- **粒度：** 15 分钟

### 与本项目的对应关系

| 本项目设计 | NREL EULP 对应 |
|---|---|
| electricity_kwh（总电耗） | NREL EULP 提供 end-use 分解（照明/插座/HVAC 分开） |
| 建筑类型 EUI 参考 | NREL EULP 有各建筑类型的 aggregate load profile |
| 日内负荷曲线设计 | NREL EULP 的日内负荷形态是当前模拟数据的间接参考 |

### 当前样例数据哪些参考了 NREL EULP

- 实验楼（BLD-D）电耗显著高于其他建筑的设计，参考了 NREL 中 Laboratory 类建筑 EUI 高于 Office 2～3 倍的结论
- 各建筑日内高峰时段（09:00-15:00）的设定参考了 NREL EULP 的日内负荷分布形态

### 第二轮建议用法

1. 若需拆分 `electricity_kwh` 为子项（照明/插座/HVAC），参考 NREL EULP 的 end-use 比例
2. 答辩时解释"为什么实验楼电耗是办公楼的 1.6 倍"：引用 NREL EULP 基准

---

## 7. 各来源与知识库文件对应关系

| 外部来源 | 已支撑的知识库内容 |
|---|---|
| BDG2 | `building_type_notes.md` 各建筑 BDG2 类比说明 |
| SHIFDR | `anomaly_diagnosis_guide.md` 类型 A（非工作时段高能耗）设计背景 |
| NYC LL84 | `metrics_and_rules.md` EUI 参考范围表 |
| AlphaBuilding | `anomaly_diagnosis_guide.md` occupancy 与 HVAC 关系说明 |
| NREL EULP | `building_type_notes.md` 实验楼高能耗说明 |
