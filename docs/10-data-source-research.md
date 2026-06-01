# 数据源调研与模拟依据报告

## 1. 调研结论

建筑能耗管理领域存在多类公开数据集和官方参考资料，可用于支撑本项目的数据字段设计、模拟规则和业务解释。但公开数据通常存在以下限制：

- 部分数据集只包含整栋建筑能耗，不包含设备状态和楼层信息。
- 部分数据集偏向 HVAC、需求响应或研究场景，不适合作为完整系统主表。
- 部分官方披露数据为年度或月度统计，不适合直接支撑小时级演示。
- 部分高保真模拟数据规模较大，不适合课程项目直接接入。

因此，本项目采用“公开真实资料作为口径依据，自主生成适合系统联调和课程演示的样例数据集”的策略。当前主数据集仍为自主模拟数据，但字段设置、建筑类型、能耗规律、HVAC 行为和异常解释均参考公开数据集与行业资料，避免纯随机生成。

## 2. 主要参考数据源

### 2.1 Building Data Genome Project 2

类型：真实建筑能耗数据集。

参考链接：

- https://github.com/buds-lab/building-data-genome-project-2
- https://www.nature.com/articles/s41597-020-00712-x

该数据集覆盖大量非住宅建筑和多类能源计量表，包含电力、冷热水、蒸汽、灌溉和太阳能等计量类型，并配有建筑元数据和天气数据。其价值主要体现在多建筑、长时序、多计量类型和建筑类型差异分析。

对本项目的参考价值：

- 支撑多建筑能耗数据结构设计。
- 支撑小时级或准小时级时序分析思路。
- 支撑建筑类型、天气和能耗关系的解释。
- 支撑建筑对比、趋势分析和异常基线设计。

限制：

- 不直接提供本项目所需的人员密度、设备编号、设备状态和课程演示型异常标签。
- 更适合作为真实能耗结构参考，不适合作为唯一主数据源直接接入。

### 2.2 SHIFDR

类型：HVAC、需求响应和建筑自动化系统相关真实数据集。

参考链接：

- https://deepblue.lib.umich.edu/data/collections/vh53ww273?locale=en
- https://news.engin.umich.edu/2024/01/large-open-dataset-aims-to-improve-understanding-of-building-electricity-demand-response/

该数据集关注建筑电力需求响应、HVAC 行为和楼宇自动化系统数据，对设备运行变化和异常响应逻辑具有参考价值。

对本项目的参考价值：

- 支撑 HVAC 负荷变化和设备异常行为的设计。
- 支撑异常解释中关于调控、负荷突增和系统响应的业务描述。
- 支撑知识库中设备调节、异常响应和运维建议内容。

限制：

- 数据主题更偏 HVAC 和 demand response，不是完整的多建筑能源管理大盘数据。
- 水耗、楼层维度和设备工单信息需要项目自行设计。

### 2.3 NYC Local Law 84 建筑能耗与水耗披露

类型：官方建筑能耗与水耗披露资料。

参考链接：

- https://www.nyc.gov/site/buildings/codes/energy-and-water-data.page
- https://data.cityofnewyork.us/w/5zyy-y8am/25te-f2tw?cur=fwHo4YLj-8S
- https://www.nyc.gov/site/finance/property/nyc-energy-benchmarking-report.page

NYC LL84 是建筑能耗和水耗 benchmarking 的典型公开资料，重点在整栋建筑年度能耗、水耗、建筑类型和政策披露口径。

对本项目的参考价值：

- 支撑同时考虑电耗和水耗的字段设计。
- 支撑 benchmarking、建筑类型和能源绩效评价的说明。
- 支撑数据字典、知识库和经济分析中关于节能管理价值的论证。

限制：

- 时间粒度偏年度或披露口径，不适合直接生成小时级动态曲线。
- 不提供设备状态、楼层异常和 HVAC 子系统详细数据。

### 2.4 AlphaBuilding

类型：高保真建筑运行模拟数据集。

参考链接：

- https://data.openei.org/submissions/2977
- https://doi.org/10.25984/1784722

AlphaBuilding 包含 HVAC、照明、插座负荷、人员数量、环境参数、整栋建筑和 end-use energy 等内容，时间粒度较细，适合参考如何构建受真实规律约束的合成数据。

对本项目的参考价值：

- 支撑人员密度、环境变量、HVAC 和 end-use 之间的关系设计。
- 支撑模拟数据并非纯随机生成的说明。
- 支撑后续若接入更高保真模拟数据时的扩展方向。

限制：

- 数据规模较大，不适合课程项目直接全量接入。
- 本项目更适合借鉴其建模思路，而非直接使用完整数据。

### 2.5 NREL End-Use Load Profiles

参考链接：

- https://www.nrel.gov/buildings/end-use-load-profiles.html

该资料提供 end-use load profile，可用于参考日内负荷分布、用能分项和不同建筑 stock 的聚合曲线。

### 2.6 NREL ComStock

参考链接：

- https://www.nrel.gov/buildings/comstock.html

ComStock 是面向商业建筑存量的高保真建模体系，可用于参考建筑原型、建筑存量差异和不同类型建筑的负荷变化规律。

### 2.7 DOE Commercial Reference Building Models

参考链接：

- https://research-hub.nrel.gov/en/publications/us-department-of-energy-commercial-reference-building-models-of-t

该资料可用于参考教学楼、办公楼、实验楼等典型建筑原型，为本项目建筑类型和参数差异提供背景依据。

## 3. 与本项目字段的映射关系

| 项目字段 | 参考来源 | 用途 |
| --- | --- | --- |
| `building_type` | BDG2、DOE Reference Buildings、NYC benchmarking | 建筑类型分类和建筑差异说明 |
| `electricity_kwh` | BDG2、NYC benchmarking、NREL profiles | 电耗范围、趋势和周期性设计 |
| `water_m3` | NYC benchmarking | 水耗字段存在性和基准管理背景 |
| `hvac_kwh` | SHIFDR、AlphaBuilding、NREL profiles | HVAC 子系统负荷和异常变化参考 |
| `cooling_load_kwh` | AlphaBuilding、ComStock | cooling load 与能耗关系 |
| `environment_temp_c` | BDG2 weather、AlphaBuilding | 天气和能耗关系 |
| `humidity_rh` | AlphaBuilding | 环境变量建模 |
| `occupancy_density_per_100m2` | AlphaBuilding、DOE schedules | 人员密度与负荷波动关系 |
| `equipment_status` | SHIFDR 业务场景 + 项目自定义规则 | 设备状态、异常标签和工单逻辑 |
| `equipment_id` | 项目自定义规则 | 系统演示、设备定位和工单关联 |

## 4. 当前数据策略

本项目不直接把某一个外部数据集作为完整主表，而是采用以下数据策略：

1. 使用公开真实数据集确定建筑能耗、时间序列、建筑类型和能耗分项的合理口径。
2. 使用 HVAC 和高保真模拟资料确定设备异常、人员密度、环境变量和负荷变化关系。
3. 生成适合课程演示的统一样例数据集，保证字段齐全、结构稳定、接口联调方便。
4. 在文档中明确说明数据为“参考真实公开资料构建的模拟样例数据”，避免将模拟数据误表述为真实采集数据。

当前样例数据已经扩展为 `2,976` 条记录，覆盖 `2026-03-01 00:00` 至 `2026-06-01 21:00`，包含 4 栋建筑和多楼层分析维度，可支撑总览、查询、统计分析、异常诊断、工单和决策报告功能。

## 5. 对系统设计的支撑作用

数据源调研对本项目产生以下支撑：

- 支撑 SRS 中关于数据集、数据字段和分析范围的需求描述。
- 支撑 SDS 中关于 CSV 样例数据、派生字段、异常规则和知识库的设计说明。
- 支撑 SEE 中关于节能收益、benchmarking 和运维价值的经济分析。
- 支撑 SEM 中关于数据真实性风险和数据质量控制的风险管理。
- 支撑项目展示时对“为什么采用模拟数据，但仍有真实依据”的解释。

## 6. 后续扩展建议

若项目后续继续迭代，可按以下方向扩展：

- 选取 BDG2 中少量建筑作为对照数据，用于展示真实能耗曲线与项目样例数据的相似性。
- 使用 SHIFDR 或 AlphaBuilding 的局部数据增强 HVAC 异常解释。
- 引入真实天气数据，提高环境变量与能耗关系的可信度。
- 将当前 CSV 数据迁移到数据库，并保留外部数据来源字段和数据版本信息。
- 在知识库中补充更多来自公开数据和官方报告的运维规则。

## 7. 参考链接

- Building Data Genome Project 2:
  - https://github.com/buds-lab/building-data-genome-project-2
  - https://www.nature.com/articles/s41597-020-00712-x
- SHIFDR:
  - https://deepblue.lib.umich.edu/data/collections/vh53ww273?locale=en
  - https://news.engin.umich.edu/2024/01/large-open-dataset-aims-to-improve-understanding-of-building-electricity-demand-response/
- NYC LL84:
  - https://www.nyc.gov/site/buildings/codes/energy-and-water-data.page
  - https://data.cityofnewyork.us/w/5zyy-y8am/25te-f2tw?cur=fwHo4YLj-8S
  - https://www.nyc.gov/site/finance/property/nyc-energy-benchmarking-report.page
- AlphaBuilding:
  - https://data.openei.org/submissions/2977
  - https://doi.org/10.25984/1784722
- NREL End-Use Load Profiles:
  - https://www.nrel.gov/buildings/end-use-load-profiles.html
- NREL ComStock:
  - https://www.nrel.gov/buildings/comstock.html
- DOE Commercial Reference Buildings:
  - https://research-hub.nrel.gov/en/publications/us-department-of-energy-commercial-reference-building-models-of-t
