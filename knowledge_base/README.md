# 知识库目录说明

这里放项目后续用于问答与检索增强的领域知识材料。当前已经不再只是最小占位，而是形成了第一轮可直接引用的知识素材包。

## 当前结构

- `manuals/`：设备运维手册、巡检规范、排障步骤、建筑类型说明
- `glossary/`：建筑能源和运维术语表、指标与判定规则
- `faq/`：结构化问答样例、演示问题清单

## 第一轮已完成的核心文件

### `manuals/`

- `operation_guide.md`
- `anomaly_diagnosis_guide.md`
- `equipment_maintenance_playbook.md`
- `building_type_notes.md`

### `glossary/`

- `energy_terms.md`
- `metrics_and_rules.md`

### `faq/`

- `typical_questions.md`
- `qa_bank_round1.md`
- `demo_questions_round1.md`

## 推荐引用优先级

如果后端问答或后续 RAG 只优先接一批文件，建议先接这四份：

1. `glossary/metrics_and_rules.md`
2. `manuals/anomaly_diagnosis_guide.md`
3. `manuals/equipment_maintenance_playbook.md`
4. `faq/qa_bank_round1.md`

原因很简单：这几份最贴合当前项目里已经做出来的功能，包括 COP、异常分析、设备维护建议和可直接演示的问题。

## 现阶段适合回答的问题

当前知识库已经比较适合支撑这些问题：

- 数据是不是纯随机生成的
- 当前有哪些建筑、有哪些字段
- COP 是什么，为什么会偏低
- 图书馆 / 实验楼为什么能耗更高
- 异常记录应该怎么排查
- 冷却塔、冷水机组、AHU、FCU 应该怎么维护

## 第二轮继续扩展建议

- 把 Markdown 文档切分成更小的知识片段，方便检索
- 为每条 FAQ 增加更标准的答案模板
- 增加更多设备级、连续异常型案例
- 让知识文件和真实接口返回结构建立更直接的映射
