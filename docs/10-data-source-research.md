# 数据源调研与模拟参考

## 1. 先说结论

有，确实存在和你们项目比较接近的公开建筑能耗数据集。

但没有哪一个公开数据集能**完整且轻量地**同时满足你们当前想要的所有字段：

- 多栋建筑
- 连续时序
- 电耗
- 水耗
- HVAC 相关负荷或子系统功率
- 环境变量
- 人员密度
- 设备状态
- 可直接拿来做课堂演示的整洁结构

所以最合理的策略不是“纯手编”，也不是“硬把一个外部数据集生吞进项目”，而是：

1. 用真实公开数据集当口径和规律参考
2. 结合公开方法资料确定字段范围和关系
3. 由我们自己生成一套更适合演示和系统联调的数据集

也就是说：

**最终主数据集仍然建议是自主模拟 / 合成，但模拟必须有外部真实资料作依据。**

## 2. 适合优先参考的真实数据集

### 2.1 Building Data Genome Project 2（最值得优先参考）

- 类型：真实数据集
- 官方仓库：
  - https://github.com/buds-lab/building-data-genome-project-2
- 对应论文：
  - https://www.nature.com/articles/s41597-020-00712-x

### 它是什么

这是一个非住宅建筑能耗数据集，覆盖 `1,636` 栋建筑、`3,053` 个能耗计量表，两整年小时级数据。

它包含的计量类型很有参考价值，例如：

- electricity
- heating / cooling water
- steam
- irrigation
- solar

同时还配有建筑元数据和天气数据。

### 它为什么适合你们

它是我目前找到的最适合做“多建筑、时序能耗、建筑类型差异、异常分析和统计展示参考”的真实数据源。

你们现在项目里的这些设计，可以直接向它借鉴：

- 建筑类型设计
- 小时级时间粒度
- 电耗 / 冷热水 / 水等多类 meter 思路
- 多建筑对比分析
- 天气与能耗关系

### 它的限制

它并不直接给你们下面这些字段：

- 人员密度
- 设备状态 normal / abnormal
- 设备编号
- 明确的课堂演示型异常标签

所以它更适合做“真实口径参考”，不适合直接变成你们最终提交数据的唯一来源。

### 我对它的建议用法

- 把它当作**多建筑真实能耗结构参考**
- 参考它的建筑类型、计量类型和时间粒度
- 如果后续想做更真实的模拟，可以抽它的一小部分建筑走势来模仿

## 3. 适合参考的细粒度 HVAC 真实数据

### 3.1 SHIFDR（适合 HVAC / 需求响应 / 异常行为参考）

- 类型：真实数据集
- 官方数据入口：
  - https://deepblue.lib.umich.edu/data/collections/vh53ww273?locale=en
- 相关新闻说明：
  - https://news.engin.umich.edu/2024/01/large-open-dataset-aims-to-improve-understanding-of-building-electricity-demand-response/

### 它是什么

这是 University of Michigan 相关团队公开的 HVAC 需求响应数据集，强调：

- 设备级 / 子系统级功率
- whole-building electric load
- building automation system 数据
- demand response event 前后行为

### 它为什么适合你们

你们项目里最“难编真”的部分，其实不是总电耗，而是：

- HVAC 负荷变化
- 设备异常时的响应形态
- demand response / 调控类事件

SHIFDR 对这部分特别有帮助，因为它给的是更接近真实楼宇控制场景的数据，而不是只有总表。

### 它的限制

- 它更偏 HVAC / demand response 研究，不是通用多建筑管理大盘数据
- 水耗字段不是它的重点
- 对课堂项目来说，它更适合当“异常和 HVAC 行为参考”，而不是直接当总数据主表

### 我对它的建议用法

- 用来参考 HVAC 事件和异常变化形态
- 用来写知识库里“设备调节 / 异常响应 / 运维建议”相关内容
- 用来支持你们后续异常解释逻辑，而不是硬拿来当最终主表

## 4. 适合参考的真实建筑能耗 / 水耗披露数据

### 4.1 NYC Local Law 84 建筑能耗与水耗披露

- 类型：真实数据 / 官方公开披露
- 官方说明：
  - https://www.nyc.gov/site/buildings/codes/energy-and-water-data.page
- 官方开放数据页面：
  - https://data.cityofnewyork.us/w/5zyy-y8am/25te-f2tw?cur=fwHo4YLj-8S
- 官方 benchmarking report：
  - https://www.nyc.gov/site/finance/property/nyc-energy-benchmarking-report.page

### 它是什么

这是纽约市的建筑能耗 / 水耗基准管理和公开披露体系的一部分，重点在：

- whole-building energy
- water consumption
- benchmarking
- building type / reporting rules / utility aggregation

### 它为什么适合你们

你们当前数据字段里有：

- electricity
- water
- building type

而 NYC 这套资料能帮你们做两件非常实用的事：

1. 给“电耗 + 水耗”的存在提供真实政策与行业背景
2. 给你们写数据字典、知识库和说明文档时提供参考口径

### 它的限制

- 这类数据更偏年度 / 披露 / benchmark 口径
- 不擅长给你们小时级动态曲线
- 对设备状态和 HVAC 子系统也不够细

### 我对它的建议用法

- 用来支撑水耗字段和 benchmark 思路
- 用来参考不同 building property type 的表达方式
- 用来写“我们为什么同时考虑 energy 和 water”这部分说明

## 5. 适合模拟但不是“真实采集”的高价值参考

### 5.1 AlphaBuilding（非常强的高保真模拟参考）

- 类型：高保真合成数据
- 官方入口：
  - https://data.openei.org/submissions/2977
- DOI：
  - https://doi.org/10.25984/1784722

### 它是什么

AlphaBuilding 是一个很强的建筑运行合成数据集，包含：

- HVAC
- lighting
- MELs
- occupant counts
- environmental parameters
- whole-building and end-use energy

时间粒度达到 `10` 分钟。

### 它为什么适合你们

你们现在其实就在做“受真实规律约束的模拟数据”，而 AlphaBuilding 正好是这个方向的高级参考样本。

### 它的限制

- 它非常大，官方说明数据约 `1.2 TB`
- 对你们课程项目来说，直接吃进去不现实

### 我对它的建议用法

- 不把它当直接输入数据
- 把它当“如何合理模拟 occupancy / HVAC / 环境 / end-use 关系”的参考

## 6. 适合做建筑类型与负荷形态参考的官方模型资料

### 6.1 NREL End-Use Load Profiles

- 官方入口：
  - https://www.nrel.gov/buildings/end-use-load-profiles.html

这个数据源来自大量 building energy models 的输出，提供 `15` 分钟粒度 end-use load profile。

### 适合怎么用

- 参考日内负荷分布
- 参考 end-use 分解方式
- 参考不同 building stock 的 aggregate profile

### 6.2 NREL ComStock

- 官方入口：
  - https://www.nrel.gov/buildings/comstock.html

ComStock 是 DOE / NREL 面向美国商业建筑 stock 的高保真建模体系。

### 适合怎么用

- 参考 building archetype 和 building stock 差异
- 参考“为什么同类建筑也会因为特征不同而负荷不同”
- 支撑你们的模拟逻辑说明

### 6.3 DOE Commercial Reference Building Models

- 技术报告入口：
  - https://research-hub.nrel.gov/en/publications/us-department-of-energy-commercial-reference-building-models-of-t

### 适合怎么用

- 参考教学楼、办公楼、实验楼等 archetype 的合理性
- 作为你们 building_type 设计和参数差异的背景依据

## 7. 对当前仓库最实际的建议

## 建议结论

当前仓库最合理的策略是：

- **主数据集继续用自主模拟**
- **模拟规则参考真实数据和官方资料**
- **如果需要引用真实数据集，就引用小部分样例、元数据、结构说明或趋势，不强行整套接入**

## 推荐优先级

### 第一优先级

- BDG2
- SHIFDR
- NYC LL84 / benchmarking report

这三类最能支撑你们“真实参考”的说法。

### 第二优先级

- AlphaBuilding
- NREL End-Use Load Profiles
- ComStock
- DOE Reference Buildings

这几类最能支撑你们“合理模拟”的说法。

## 8. 和当前字段的建议映射

| 当前字段 | 最值得参考的外部来源 | 用法建议 |
| --- | --- | --- |
| `building_type` | BDG2, DOE Reference Buildings, NYC benchmarking | 参考建筑类型分类 |
| `electricity_kwh` | BDG2, NYC benchmarking | 参考电耗范围和走势 |
| `water_m3` | NYC benchmarking | 参考水耗存在性与 benchmark 背景 |
| `hvac_kwh` | SHIFDR, AlphaBuilding, End-Use Load Profiles | 参考 HVAC 子系统强度与时序变化 |
| `cooling_load_kwh` | AlphaBuilding, ComStock | 参考 end-use 和 cooling 负荷关系 |
| `environment_temp_c` | BDG2 weather, AlphaBuilding | 参考气象变化与能耗关系 |
| `humidity_rh` | AlphaBuilding | 参考环境变量建模 |
| `occupancy_density_per_100m2` | AlphaBuilding, DOE archetype schedules | 参考人员密度与负荷波动关系 |
| `equipment_status` | SHIFDR + 自定义规则 | 不太可能直接拿到，需要自己设计 |
| `equipment_id` | 自定义 | 主要是系统演示字段，可自行规范 |

## 9. 对项目内负责同学的具体建议

### 给马源胜

你最该优先读这份文档，然后按下面思路补你的素材包：

1. 用 BDG2 参考多建筑、多时序、多 meter 的结构
2. 用 SHIFDR 参考 HVAC 与异常 / 需求响应场景
3. 用 NYC LL84 参考 energy + water benchmark 背景
4. 用 AlphaBuilding / NREL 资料参考如何把模拟写得更像真的

你不需要现在就去下载全部数据。

你第一轮更重要的是：

- 先把知识库和数据说明写扎实
- 先把“为什么这样模拟”说清楚
- 先把演示能问的问题准备好

### 给王天一

你不一定需要深入研究全部外部数据，但至少应该知道：

- 当前样例数据是“受真实资料约束的模拟”
- 所以后端接口不要假设外部数据字段天然完整
- 后续如果加导出或分析，不要把逻辑写死在某一个外部数据集格式上

### 给周由

你只需要知道一件事：

- 当前前端展示的数据主表仍然是自建模拟数据
- 但它不是瞎编，而是有真实公开数据和官方资料做参考

这意味着前端文案可以更自信地表述为：

- “参考公开建筑能耗数据与 benchmark 口径构建”
- 而不是“纯随机生成”

## 10. 建议下一步

最实用的下一步不是去下载十几个数据集，而是：

1. 马源胜先基于这份文档补 `data/processed/` 和 `knowledge_base/`
2. 在知识库里明确写出哪些规则来自真实资料参考
3. 第二轮如果还有时间，再考虑抽取一个真实数据子集做对比或展示附件

## 11. 参考链接

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

