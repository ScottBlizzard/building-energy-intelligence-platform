# 问答素材库 — 第一轮（Round 1）

**编写人：** 马源胜  
**日期：** 2026-04-23  
**版本：** Round 1  
**说明：** 本文档提供 AI 问答模块的素材库，供后端问答接口规则化引用，并作为后续 RAG 链路的知识检索基础。

---

## 使用说明

每条问答按以下结构组织：

- **问题（Q）**：自然语言问法
- **答案方向（A）**：建议回答内容要点（非逐字答案）
- **应引用的知识文件**：RAG 引用时的优先文件
- **演示适用性**：✅ 适合 / ⚠️ 需要配合数据 / ❌ 不适合直接演示

---

## 第一组：数据概况类（5 个）

### Q1：这个系统里有哪些建筑的数据？

**答案方向：**
- 共 4 栋建筑：综合教学楼A（teaching）、行政办公楼B（office）、图书信息楼C（library）、科研实验楼D（lab）
- 总记录数 1,120 条，时间范围 2026-03-01 至 2026-04-04
- 每栋建筑各有 280 条记录，时间粒度为 3 小时

**应引用文件：**
- `data/processed/data_quality_report_round1.md`（第 1 节）

**演示适用性：** ✅ 适合作为演示开场问题，展示数据概览

---

### Q2：数据里每条记录包含哪些字段？

**答案方向：**
- 建筑标识：building_id / building_name / building_type
- 时间：timestamp
- 能耗：electricity_kwh / water_m3 / hvac_kwh / cooling_load_kwh
- 环境：environment_temp_c / humidity_rh
- 运行：chilled_water_supply_temp_c / chilled_water_return_temp_c / occupancy_density_per_100m2
- 设备：equipment_id / equipment_status（normal/abnormal）
- 共 16 个字段，全部必填字段在样例数据中均有值

**应引用文件：**
- `data/dictionaries/energy_records_dictionary.csv`

**演示适用性：** ✅ 适合，可配合数据字典页面展示

---

### Q3：当前数据集覆盖哪些场景？

**答案方向：**
- 覆盖：多建筑类型对比、连续时序、日内高峰/低谷、设备异常标记、COP 计算
- 不覆盖：节假日行为差异（无节假日标记）、季节性大范围变化、分项计量（照明/插座）
- 样例数据已可支撑全部接口联调和课堂演示

**应引用文件：**
- `data/processed/data_quality_report_round1.md`（第 3 节）

**演示适用性：** ✅ 适合，可在答辩时回答"数据局限性"提问

---

### Q4：数据里有多少条异常记录？

**答案方向：**
- 共 53 条 equipment_status=abnormal 的记录
- 占总记录 4.7%，四栋建筑均匀分布
- 异常主要集中在电耗偏高型，无传感器故障型
- 典型案例：R00001（教学楼，凌晨高电耗）、R00606（实验楼，全库最高电耗 561.85 kWh）

**应引用文件：**
- `data/processed/data_quality_report_round1.md`（第 4 节）
- `knowledge_base/manuals/anomaly_diagnosis_guide.md`

**演示适用性：** ✅ 非常适合，可结合异常列表页面现场展示

---

### Q5：当前数据集的 COP 均值是多少？

**答案方向：**
- 当前样例数据 COP 均值约 3.01
- COP 计算方法：cooling_load_kwh / hvac_kwh
- 范围：2.32（最低，图书楼C夜间异常）～ 3.24（最高）
- COP < 2.5 的记录为告警级别

**应引用文件：**
- `knowledge_base/glossary/metrics_and_rules.md`（第一节 COP 部分）

**演示适用性：** ✅ 非常适合，COP 是演示核心指标，可直接展示

---

## 第二组：分析类（5 个）

### Q6：哪栋建筑的能耗最高？

**答案方向：**
- 科研实验楼D 电耗最高，3 小时均值 360.5 kWh，最高单次 561.85 kWh
- 其次是图书信息楼C（均值 304.3 kWh）
- 行政办公楼B 最低（均值 224.6 kWh）
- 原因：实验楼有大量高功率实验设备，图书馆人流量大且运行时间长

**应引用文件：**
- `knowledge_base/manuals/building_type_notes.md`
- `data/processed/data_quality_report_round1.md`（第 1 节统计表）

**演示适用性：** ✅ 非常适合，建筑对比分析是核心演示功能

---

### Q7：如何识别某建筑出现了能耗异常？

**答案方向：**
- 方法一：查看 equipment_status=abnormal 的记录
- 方法二：计算该时段 COP，若低于 2.5 则告警
- 方法三：比较电耗是否超过建筑历史均值 × 1.5
- 方法四：非工作时段（00:00-06:00）电耗超过建筑日均的 80%

**应引用文件：**
- `knowledge_base/glossary/metrics_and_rules.md`（第三节判定阈值表）
- `knowledge_base/manuals/anomaly_diagnosis_guide.md`

**演示适用性：** ✅ 非常适合，可结合异常分析接口实时演示

---

### Q8：图书信息楼C 最近出现了什么异常？

**答案方向：**
- 共有约 13～14 条异常记录，分布在整个时间段内
- 典型案例：R00024（2026-03-01 21:00），electricity=344.02 kWh，COP=2.34，为全库最低 COP
- 夜间高电耗（21:00 后）为该楼最主要的异常模式
- 建议排查：冷却塔CT-C-03 运行状态、冷水温差是否正常

**应引用文件：**
- `knowledge_base/manuals/anomaly_diagnosis_guide.md`（类型 A 和类型 B）
- `knowledge_base/manuals/equipment_maintenance_playbook.md`（第 4 节 CT 部分）

**演示适用性：** ✅ 非常适合，问答模块演示首选问题

---

### Q9：空调系统的制冷效率如何随时间变化？

**答案方向：**
- 通过 COP 随时间的变化趋势来观察
- 高峰时段（09:00-18:00）由于负荷高，COP 相对稳定（接近均值 3.0）
- 深夜/低负荷时段（00:00-03:00）若出现低 COP，往往与设备部分负荷低效或异常相关
- 趋势图可通过 `/api/v1/analytics/time-summary` 获取后在前端绘制

**应引用文件：**
- `knowledge_base/glossary/metrics_and_rules.md`（COP 判定规则）

**演示适用性：** ⚠️ 需要前端趋势图配合，单独文字回答效果有限

---

### Q10：科研实验楼D 为什么电耗这么高？

**答案方向：**
- 主要原因：实验室类建筑功率密度高，拥有大量高能耗仪器（离心机、电炉、加速器等）
- 与 NREL EULP 数据一致：实验楼 EUI 典型值是办公建筑的 2～3 倍
- 设备 FCU-D-04 为风机盘管，多个实验室独立调温，HVAC 灵活性需求高
- 最高单次电耗 561.85 kWh（R00606），发生在 2026-03-19 15:00，下午高峰期

**应引用文件：**
- `knowledge_base/manuals/building_type_notes.md`
- `data/processed/external_source_shortlist_round1.md`（NREL EULP 部分）

**演示适用性：** ✅ 适合，体现了建筑类型与能耗的关联分析

---

## 第三组：运维建议类（5 个）

### Q11：发现空调制冷效率下降，应该怎么排查？

**答案方向：**
1. 先确认 COP 是否低于 2.5 阈值
2. 检查供回水温差 ΔT：若 < 3°C，排查流量问题；若 > 7°C，排查冷量不足
3. 检查冷水机组冷凝器清洁状态（结垢会降低 COP）
4. 检查制冷剂是否泄漏（压力表数值）
5. 如 COP 呈趋势性下降而非单点异常，安排专业维保

**应引用文件：**
- `knowledge_base/manuals/anomaly_diagnosis_guide.md`（类型 B）
- `knowledge_base/manuals/equipment_maintenance_playbook.md`（第 3 节 CH 部分）
- `knowledge_base/glossary/metrics_and_rules.md`（冷水温差判定）

**演示适用性：** ✅ 非常适合，展示知识库与问答联动效果

---

### Q12：深夜发现某建筑还在大量用电，应该怎么处理？

**答案方向：**
1. 确认时段：00:00-06:00 且 occupancy_density < 10，属于非工作时段高能耗
2. 查看对应设备状态是否为 abnormal
3. 检查空调系统是否未关机（BAS 调度是否执行了夜间关机策略）
4. 检查是否有 IT 设备或实验设备持续运行
5. 联系楼管人员现场确认；必要时远程关闭空调系统

**应引用文件：**
- `knowledge_base/manuals/anomaly_diagnosis_guide.md`（类型 A）

**演示适用性：** ✅ 非常适合，结合 R00001 / R00642 等真实异常记录演示

---

### Q13：冷却塔应该多久维护一次？有哪些重点？

**答案方向：**
- 每日：检查水温、有无漏水、风机状态
- 每周：布水器清洁、水质检查
- 每月：集水盘清洗、水质处理（防藻）
- 每季度：填料全面清洗、风机叶片检查
- 重点：夏季高温期应增加水质处理频率，防止藻类繁殖影响冷却效果

**应引用文件：**
- `knowledge_base/manuals/equipment_maintenance_playbook.md`（第 4 节 CT 部分）

**演示适用性：** ✅ 适合，运维建议类问答的典型样本

---

### Q14：如何预防实验楼的高峰电耗超标？

**答案方向：**
- 制定用电高峰期管理规定：错峰安排大功率实验
- 实施需求响应策略：在高峰期临时提高空调设定温度 1～2°C
- 监控 electricity_kwh 超过阈值时发送告警
- 配合 HVAC 优化：FCU 按需调节而非全开
- 参考 SHIFDR 数据中的 demand response 实践

**应引用文件：**
- `knowledge_base/manuals/building_type_notes.md`（实验楼特性）
- `data/processed/external_source_shortlist_round1.md`（SHIFDR 部分）

**演示适用性：** ⚠️ 需要配合说明，单独演示略抽象；建议与告警接口结合展示

---

### Q15：这套系统的知识库后续怎么和大模型结合使用？

**答案方向：**
- 当前阶段：知识库为 Markdown 文档，问答接口使用规则化逻辑，匹配关键词后返回预设答案
- 下一阶段：将 Markdown 文档切分为知识片段，建立向量索引（如 FAISS 或 ChromaDB）
- 最终形态：用户提问 → 向量检索相关片段 → 大模型基于检索内容生成答案（RAG）
- 建议优先向量化的文件：本文档（qa_bank_round1.md）、`metrics_and_rules.md`、`anomaly_diagnosis_guide.md`

**应引用文件：**
- `docs/02-technical-solution.md`（第 5 节智能问答演进路径）
- `knowledge_base/glossary/metrics_and_rules.md`（RAG 定义）

**演示适用性：** ✅ 非常适合作为演示结尾问题，展示系统扩展性

---

## 附：问答覆盖矩阵

| 编号 | 类型 | 核心知识文件 | 演示适合性 |
|---|---|---|---|
| Q1 | 数据概况 | data_quality_report | ✅ |
| Q2 | 数据概况 | 数据字典 | ✅ |
| Q3 | 数据概况 | data_quality_report | ✅ |
| Q4 | 数据概况 | data_quality_report + anomaly_guide | ✅ |
| Q5 | 数据概况 | metrics_and_rules | ✅ |
| Q6 | 分析 | building_type_notes | ✅ |
| Q7 | 分析 | metrics_and_rules + anomaly_guide | ✅ |
| Q8 | 分析 | anomaly_guide + maintenance_playbook | ✅ |
| Q9 | 分析 | metrics_and_rules | ⚠️ |
| Q10 | 分析 | building_type_notes + external_source | ✅ |
| Q11 | 运维建议 | anomaly_guide + maintenance_playbook | ✅ |
| Q12 | 运维建议 | anomaly_guide | ✅ |
| Q13 | 运维建议 | maintenance_playbook | ✅ |
| Q14 | 运维建议 | building_type_notes + external_source | ⚠️ |
| Q15 | 运维建议 | technical-solution + metrics_and_rules | ✅ |
