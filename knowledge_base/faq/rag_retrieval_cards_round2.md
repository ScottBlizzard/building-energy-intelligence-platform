# RAG 检索卡片集 — 第二轮（Round 2）

**编写人：** 马源胜  
**日期：** 2026-05-06  
**版本：** Round 2  
**用途：** 为后端检索增强模块提供"问题 → 知识片段"的稳定映射结构，使 RAG 链路能精准定位目标段落，同时作为演示问答与接口测试的结构化索引。

---

## 使用说明

每张检索卡片包含以下字段：

| 字段 | 说明 |
|------|------|
| **问题** | 用户自然语言问法（可多种表述） |
| **关键词** | 检索时应命中的核心词（后端分词/向量匹配参考） |
| **应命中文件** | RAG 应优先召回的知识文件（文件路径） |
| **应命中段落主题** | 文件内应精确定位的章节/段落描述 |
| **预期回答要点** | 回答中必须包含的关键事实（验证用） |
| **演示适用性** | ✅ 直接演示 / ⚠️ 需配合数据 / ❌ 不适合演示 |
| **卡片 ID** | 唯一标识，格式 `RC-序号` |

---

## 第一组：数据概况类（RC-01 ～ RC-05）

### RC-01

**问题：**
- 这个系统里有多少栋建筑？
- 系统覆盖了哪些建筑？
- 当前数据集包含哪些楼？

**关键词：** `建筑数量` `building_id` `BLD-A` `BLD-B` `BLD-C` `BLD-D` `教学楼` `办公楼` `图书馆` `实验楼`

**应命中文件：**
- `data/processed/data_quality_report_round1.md`

**应命中段落主题：** §1 数据集基本情况 → 四栋建筑统计表

**预期回答要点：**
- 共 4 栋建筑
- BLD-A 综合教学楼（teaching）、BLD-B 行政办公楼（office）、BLD-C 图书信息楼（library）、BLD-D 科研实验楼（lab）
- 总记录数 1,120 条，每楼 280 条

**演示适用性：** ✅ 直接演示，适合作为开场问题

---

### RC-02

**问题：**
- 数据集时间范围是多少？
- 数据从什么时候到什么时候？
- 时间粒度是多少？

**关键词：** `时间范围` `时间粒度` `3小时` `2026-03-01` `2026-04-04` `timestamp` `35天`

**应命中文件：**
- `data/processed/data_quality_report_round1.md`

**应命中段落主题：** §1 数据集基本情况 → 基础统计表

**预期回答要点：**
- 时间范围：2026-03-01 00:00 ～ 2026-04-04 21:00（35 天）
- 时间粒度：3 小时间隔
- 每栋楼各 280 条记录

**演示适用性：** ✅ 直接演示

---

### RC-03

**问题：**
- 数据字段有哪些？
- 每条记录包含什么信息？
- 数据里有人员密度字段吗？

**关键词：** `字段` `electricity_kwh` `hvac_kwh` `cooling_load_kwh` `occupancy_density` `equipment_status` `16个字段` `数据字典`

**应命中文件：**
- `data/dictionaries/energy_records_dictionary.csv`
- `data/processed/data_quality_report_round1.md`

**应命中段落主题：** §2 字段完整性评估 → 必填字段表、可选字段表

**预期回答要点：**
- 共 16 个字段，涵盖建筑标识、时间、能耗、环境、运行状态、设备信息
- 全部字段在样例数据中无空值
- 含 occupancy_density_per_100m2（人员密度，单位：人/100m²）

**演示适用性：** ✅ 直接演示，可配合数据字典页面

---

### RC-04

**问题：**
- 数据集里有多少条异常记录？
- 异常率是多少？
- 哪些建筑有异常？

**关键词：** `异常` `abnormal` `equipment_status` `53条` `4.7%` `异常率` `R00001` `R00606`

**应命中文件：**
- `data/processed/data_quality_report_round1.md`
- `knowledge_base/manuals/anomaly_diagnosis_guide.md`

**应命中段落主题：** §4 异常数据支撑演示分析 → 三个典型案例

**预期回答要点：**
- 共 53 条异常记录，占 4.7%
- 四栋建筑均匀分布
- 典型案例：R00001（教学楼凌晨高电耗）、R00024（图书馆最低 COP=2.34）、R00606（实验楼全库最高电耗 561.85 kWh）

**演示适用性：** ✅ 非常适合，可结合异常列表页面展示

---

### RC-05

**问题：**
- COP 是什么？
- 当前系统的 COP 均值是多少？
- COP 低说明什么问题？

**关键词：** `COP` `制冷性能系数` `cooling_load_kwh` `hvac_kwh` `3.01` `2.5` `告警` `能效`

**应命中文件：**
- `knowledge_base/glossary/metrics_and_rules.md`

**应命中段落主题：** §一 核心能效指标 → COP 定义与阈值

**预期回答要点：**
- COP = cooling_load_kwh / hvac_kwh，反映空调系统制冷效率
- 当前样例数据 COP 均值约 3.01，范围 2.32～3.24
- COP < 2.5 为告警级别，需排查设备
- COP 偏低常见原因：冷冻水温差异常、设备老化、过滤网堵塞

**演示适用性：** ✅ 非常适合，COP 是演示核心指标

---

## 第二组：分析类（RC-06 ～ RC-10）

### RC-06

**问题：**
- 哪栋建筑能耗最高？
- 各建筑电耗对比
- 实验楼为什么用电最多？

**关键词：** `能耗对比` `electricity_kwh` `建筑对比` `实验楼` `BLD-D` `360.5 kWh` `高功率设备`

**应命中文件：**
- `knowledge_base/manuals/building_type_notes.md`
- `data/processed/data_quality_report_round1.md`

**应命中段落主题：** §建筑类型说明 → 科研实验楼D；§1 数据集基本情况 → 四栋建筑统计表

**预期回答要点：**
- BLD-D 实验楼电耗最高，3h 均值 360.5 kWh，最高单次 561.9 kWh
- BLD-B 办公楼最低，均值 224.6 kWh
- 实验楼高耗原因：大功率实验设备、全天候运行需求

**演示适用性：** ✅ 非常适合，建筑对比是核心演示功能

---

### RC-07

**问题：**
- 如何识别能耗异常？
- 异常判定规则是什么？
- 什么情况下会触发告警？

**关键词：** `异常判定` `告警` `阈值` `COP < 2.5` `非工时` `均值1.5倍` `equipment_status` `abnormal`

**应命中文件：**
- `knowledge_base/glossary/metrics_and_rules.md`
- `knowledge_base/manuals/anomaly_diagnosis_guide.md`

**应命中段落主题：** §三 数据质量相关指标 → 判定规则表；§3 异常判定阈值汇总

**预期回答要点：**
- 规则一：equipment_status=abnormal 直接标记
- 规则二：COP < 2.5 → 低 COP 告警
- 规则三：电耗 > 建筑历史均值 × 1.5
- 规则四：00:00-06:00 非工时电耗 > 日均 80%

**演示适用性：** ✅ 非常适合，可结合异常分析接口实时演示

---

### RC-08

**问题：**
- 图书馆出现了什么异常？
- 图书信息楼C 的 COP 为什么最低？
- 图书馆夜间用电高是什么原因？

**关键词：** `图书馆` `BLD-C` `CT-C-03` `冷却塔` `R00024` `COP=2.34` `夜间异常` `冷水温差`

**应命中文件：**
- `knowledge_base/manuals/anomaly_diagnosis_guide.md`
- `knowledge_base/manuals/equipment_maintenance_playbook.md`

**应命中段落主题：** §2 异常类型 → 类型B（低COP）和类型A（非工时高耗）；§4 CT 冷却塔维护

**预期回答要点：**
- R00024（2026-03-01 21:00）：电耗 344.02 kWh，COP=2.34（全库最低）
- 夜间高电耗（21:00 后）是图书馆主要异常模式
- 排查方向：CT-C-03 冷却塔运行状态、冷冻水供回温差是否正常

**演示适用性：** ✅ 首选演示问题，结合问答模块效果极佳

---

### RC-09

**问题：**
- 空调制冷效率如何随时间变化？
- COP 什么时候最低？
- 制冷效率和气温有关系吗？

**关键词：** `COP趋势` `时序分析` `制冷效率` `environment_temp_c` `气温` `时间变化` `hvac_kwh`

**应命中文件：**
- `knowledge_base/glossary/metrics_and_rules.md`
- `data/processed/data_quality_report_round1.md`

**应命中段落主题：** §一 核心能效指标 → COP 公式与统计；§1 数据集基本情况

**预期回答要点：**
- COP 与 environment_temp_c 负相关：气温越高，制冷负荷越大，COP 有下降趋势
- 当前样例数据 COP 均值 3.01，夜间偏低（冷负荷未减少但 hvac_kwh 未降）
- 可通过 COP 时序图观察设备性能衰退趋势

**演示适用性：** ⚠️ 需配合图表展示，纯文字回答效果有限

---

### RC-10

**问题：**
- 设备维护应该怎么做？
- AHU 空气处理机怎么保养？
- 冷水机组多久检修一次？

**关键词：** `设备维护` `AHU` `CH` `CT` `FCU` `空气处理机` `冷水机组` `冷却塔` `风机盘管` `保养` `检修`

**应命中文件：**
- `knowledge_base/manuals/equipment_maintenance_playbook.md`

**应命中段落主题：** §2-5 各设备维护章节 → 日/周/月/季保养计划

**预期回答要点：**
- AHU-A-01：日检风量，周清过滤器，月检皮带，季度全面保养
- CH-B-02：日检运行参数，月检冷冻水水质，季度化学清洗
- CT-C-03：日检水位，周清填料，月检风机，季度防腐处理
- FCU-D-04：日检风量，月清盘管，季度全检

**演示适用性：** ✅ 适合运维建议类问题演示

---

## 第三组：运维建议类（RC-11 ～ RC-15）

### RC-11

**问题：**
- 实验楼能耗怎么降低？
- 科研实验楼如何节能？
- BLD-D 用电太多怎么优化？

**关键词：** `节能` `BLD-D` `实验楼` `降耗` `FCU-D-04` `高峰管控` `分时` `实验设备`

**应命中文件：**
- `knowledge_base/manuals/building_type_notes.md`
- `knowledge_base/manuals/anomaly_diagnosis_guide.md`

**应命中段落主题：** §科研实验楼D → 能耗特征与告警阈值建议

**预期回答要点：**
- 实验楼用电峰值主要来自实验设备密集使用时段
- 建议分时排课/排实验，错开设备高峰
- FCU 风机盘管效率是关键，需定期检查盘管洁净度
- 建议告警阈值：electricity > 450 kWh/3h，COP < 2.6

**演示适用性：** ✅ 适合，可用于展示智能运维建议

---

### RC-12

**问题：**
- 办公楼 COP 为什么高于图书馆？
- 为什么行政楼能耗最低？
- 不同建筑类型能耗差异说明什么？

**关键词：** `建筑类型对比` `BLD-B` `办公楼` `COP对比` `能耗差异` `使用规律` `office` `library`

**应命中文件：**
- `knowledge_base/manuals/building_type_notes.md`

**应命中段落主题：** §6 各建筑类型能耗差异对比汇总

**预期回答要点：**
- 办公楼有明确下班时间，非工时设备自然关闭，电耗低且规律
- 图书馆夜间仍有人员活动（自习），HVAC 不能完全关停
- 建筑类型决定了合理的运营时间和告警阈值，不能一刀切

**演示适用性：** ✅ 适合，建筑类型对比是展示系统分析深度的好问题

---

### RC-13

**问题：**
- 冷却塔出现故障怎么排查？
- CT-C-03 报警应该怎么处理？
- 冷却塔填料堵塞有什么表现？

**关键词：** `冷却塔` `CT-C-03` `故障排查` `填料` `冷凝温度` `水位` `BLD-C` `图书馆`

**应命中文件：**
- `knowledge_base/manuals/equipment_maintenance_playbook.md`
- `knowledge_base/manuals/anomaly_diagnosis_guide.md`

**应命中段落主题：** §4 CT 冷却塔维护；§2 异常类型B（低COP）→ 排查步骤

**预期回答要点：**
- CT 填料堵塞 → 冷凝压力上升 → COP 下降
- 排查步骤：查水位 → 查填料状态 → 查风机转速 → 查排污
- CT-C-03 建议月度清洗填料，季度防腐处理

**演示适用性：** ✅ 适合专业运维场景演示

---

### RC-14

**问题：**
- 这套系统的数据来源是哪里？
- 样例数据是真实数据还是模拟的？
- 数据参考了哪些外部数据集？

**关键词：** `数据来源` `BDG2` `SHIFDR` `NYC LL84` `模拟数据` `合成数据` `外部数据源` `真实口径`

**应命中文件：**
- `data/processed/external_source_shortlist_round1.md`
- `docs/10-data-source-research.md`

**应命中段落主题：** §优先级汇总；§1 先说结论

**预期回答要点：**
- 当前主数据集为结构化模拟数据，非直接采集
- 字段设计参考 BDG2（建筑类型/时序/电耗）、SHIFDR（HVAC子系统）、NYC LL84（水耗披露）
- 模拟策略：真实外部数据口径参考 + 项目需求自主合成

**演示适用性：** ⚠️ 适合答辩时回答"数据真实性"质疑

---

### RC-15

**问题：**
- ΔT（冷冻水供回温差）正常范围是多少？
- 温差偏小说明什么问题？
- 冷冻水温差异常如何判断？

**关键词：** `ΔT` `温差` `冷冻水` `chilled_water_supply_temp_c` `chilled_water_return_temp_c` `4-6°C` `小温差` `大流量`

**应命中文件：**
- `knowledge_base/glossary/metrics_and_rules.md`

**应命中段落主题：** §一 核心能效指标 → ΔT 冷冻水供回温差

**预期回答要点：**
- 正常范围：ΔT = 4～6°C
- ΔT < 3°C 为小温差大流量，提示冷冻水阀门开度过大或末端负荷不足
- ΔT > 8°C 提示水量不足，可能影响冷量输送
- 可通过 chilled_water_supply_temp_c 与 return_temp_c 字段计算

**演示适用性：** ✅ 适合，是 HVAC 专业问答的典型展示

---

## 附：检索卡片覆盖矩阵

| 知识文件 | 命中卡片 |
|----------|----------|
| `data/processed/data_quality_report_round1.md` | RC-01, RC-02, RC-03, RC-04, RC-06, RC-09 |
| `knowledge_base/glossary/metrics_and_rules.md` | RC-05, RC-07, RC-09, RC-15 |
| `knowledge_base/manuals/anomaly_diagnosis_guide.md` | RC-04, RC-07, RC-08, RC-11, RC-13 |
| `knowledge_base/manuals/equipment_maintenance_playbook.md` | RC-08, RC-10, RC-13 |
| `knowledge_base/manuals/building_type_notes.md` | RC-06, RC-11, RC-12 |
| `data/dictionaries/energy_records_dictionary.csv` | RC-03 |
| `data/processed/external_source_shortlist_round1.md` | RC-14 |
| `docs/10-data-source-research.md` | RC-14 |

**统计：**
- 共 15 张检索卡片
- 直接演示 ✅：11 张
- 需配合数据 ⚠️：2 张（RC-09, RC-14）
- 不适合演示 ❌：0 张
- 覆盖知识文件：8 个
