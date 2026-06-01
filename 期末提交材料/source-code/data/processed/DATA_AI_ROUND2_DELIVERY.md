# 马源胜第二轮交付说明

**交付人：** 马源胜  
**交付日期：** 2026-05-06  
**版本：** Round 2  
**对应任务文件：** `第二次任务/02-给马源胜-数据与AI.md`

---

## 一、本轮新增文件清单

| 文件路径 | 文件类型 | 主要用途 | 主要受益方 |
|----------|----------|----------|------------|
| `knowledge_base/faq/rag_retrieval_cards_round2.md` | Markdown | RAG 检索卡片集（15张） | 王天一（后端检索）+ 许奕（整合验收） |
| `knowledge_base/faq/assistant_eval_round2.md` | Markdown | 问答助手评测素材（15条） | 许奕（质量验收）+ 演示验证 |
| `data/processed/round2_dataset_upgrade_plan.md` | Markdown | 数据增强方向规划（7个方向） | 许奕（下轮数据决策） |
| `data/processed/anomaly_scenario_catalog_round2.csv` | CSV | 结构化异常场景目录（12条） | 王天一（后端测试）+ 许奕 |
| `data/processed/building_profile_reference_round2.csv` | CSV | 建筑档案参考数据（4栋） | 王天一（接口扩展）+ 许奕 |
| `data/processed/qa_evaluation_set_round2.csv` | CSV | 问答评测集（20条） | 许奕（问答验收）+ 王天一（检索调试） |
| `knowledge_base/manuals/continuous_anomaly_patterns_round2.md` | Markdown | 连续异常模式说明（4种模式+3个演示场景） | 王天一（问答引用）+ 演示 |
| `knowledge_base/glossary/building_area_and_eui_notes_round2.md` | Markdown | 建筑面积与EUI说明 | 许奕（数据字典扩展）+ 王天一（新接口参考） |

**合计：** 8 个新文件，覆盖全部 6 个必交文件 + 2 个选做文件。

---

## 二、按用途分类说明

### 偏"后端检索"的文件

这两个文件设计目的是让后端更容易实现问题 → 知识段落的精准定位：

**1. `knowledge_base/faq/rag_retrieval_cards_round2.md`**
- 15 张结构化检索卡片，每张含：问题变体、关键词列表、应命中文件路径、应命中段落主题
- 后端做向量检索时，可以用关键词列表构建查询向量
- 可直接作为"问题 → 知识文件"映射索引使用，无需解析自然语言

**2. `data/processed/anomaly_scenario_catalog_round2.csv`**
- 12 条异常场景，每条包含触发字段、触发条件、触发值、严重程度
- 后端可将此 CSV 作为规则库，用于匹配用户提问中的场景关键词
- `diagnosis_guide_ref` 字段直接指向 anomaly_diagnosis_guide.md 的对应章节

---

### 偏"问答评测"的文件

这两个文件用于验证问答系统的回答质量是否达标：

**3. `knowledge_base/faq/assistant_eval_round2.md`**
- 15 条评测条目，每条含：最低合格回答、优秀回答要素、不应出现的内容
- 许奕验收问答质量时可直接对照"最低合格"标准打分
- 5 条 🔴高优先级条目是演示前必须测试的基准线

**4. `data/processed/qa_evaluation_set_round2.csv`**
- 20 条结构化评测问题，含 `expected_sources`、`expected_keywords`、`expected_answer_points`
- 可直接导入脚本做自动化评测（对比关键词覆盖率）
- 包含 4 类问题：事实类(8条)、分析类(6条)、建议类(2条)、边界类(4条)

---

### 偏"数据增强规划"的文件

这三个文件定义了下一步数据集应该怎么改：

**5. `data/processed/round2_dataset_upgrade_plan.md`**
- 7 个增强方向，每个方向包含：建议字段、建议值范围、参考依据、实施优先级
- 🔴高优先级 3 项：节假日标记(D-01)、建筑面积(D-02)、人员密度细化(D-03)
- 附有"给许奕的实施路径建议"，第三轮优先做 D-01 和 D-02

**6. `data/processed/building_profile_reference_round2.csv`**
- 4 栋建筑的完整参考档案，含建议面积、告警阈值、EUI 估算值
- 可作为建筑元数据表扩展进系统
- `floor_area_m2` 列支持直接解锁 EUI 计算

**7. `knowledge_base/glossary/building_area_and_eui_notes_round2.md`**
- 解释为什么需要建筑面积字段，如何计算 EUI
- 对标 BDG2、NYC LL84、NREL EULP 的 EUI 参考值
- 明确指出当前 EUI 估算偏低的原因（春季样例，非全年）

**8. `knowledge_base/manuals/continuous_anomaly_patterns_round2.md`**
- 定义 4 种连续异常模式（P1低COP/P2非工时高耗/P3白天过载/P4复合型）
- 包含 3 个可直接用于演示的场景规格（SEQ-001/002/003）
- 与 `anomaly_scenario_catalog_round2.csv` 中的连续异常场景直接对应

---

## 三、边界合规声明

本轮所有修改：
- ✅ 只写入 `knowledge_base/` 和 `data/processed/`
- ✅ 未修改 `data/samples/energy_records.csv`（主样例数据）
- ✅ 未修改 `data/dictionaries/energy_records_dictionary.csv`（数据字典）
- ✅ 未修改 `docs/` 下任何文件
- ✅ 未修改 `backend/`、`frontend/`、`scripts/` 目录
- ✅ 未修改 `.gitignore` 或其他根目录文件（第一轮瑕疵不再重犯）

---

## 四、给许奕的整合建议

### 优先整合（高价值、低成本）

1. **将 `building_profile_reference_round2.csv` 中的 `floor_area_m2` 纳入数据字典**  
   只需在 `data/dictionaries/energy_records_dictionary.csv` 中增加一行

2. **将 `rag_retrieval_cards_round2.md` 作为问答接口的检索索引**  
   后端问答接口目前用规则引用知识文件，下一步可把检索卡片的关键词作为匹配规则扩展

3. **将 `qa_evaluation_set_round2.csv` 的 20 条问题作为问答模块验收标准**

### 可放后续迭代

4. 节假日标记字段（D-01）实施需要修改主 CSV，建议单独安排

5. 连续异常场景（SEQ-001/002/003）需要新增几行样例数据，建议第三轮统一处理

---

## 五、文件间引用关系图

```
rag_retrieval_cards_round2.md
    ├── → data_quality_report_round1.md (RC-01~04, RC-06, RC-09)
    ├── → metrics_and_rules.md (RC-05, RC-07, RC-09, RC-15)
    ├── → anomaly_diagnosis_guide.md (RC-04, RC-07, RC-08, RC-11, RC-13)
    ├── → equipment_maintenance_playbook.md (RC-08, RC-10, RC-13)
    ├── → building_type_notes.md (RC-06, RC-11, RC-12)
    └── → external_source_shortlist_round1.md (RC-14)

assistant_eval_round2.md
    └── 与 rag_retrieval_cards_round2.md 配对使用（检索卡片定义"命中什么"，评测素材定义"回答对不对"）

qa_evaluation_set_round2.csv
    └── eval_id_ref 字段 → assistant_eval_round2.md 中的对应条目

anomaly_scenario_catalog_round2.csv
    ├── is_continuous=true → continuous_anomaly_patterns_round2.md
    └── diagnosis_guide_ref → anomaly_diagnosis_guide.md

building_profile_reference_round2.csv
    └── floor_area_m2 → building_area_and_eui_notes_round2.md (EUI计算依据)

round2_dataset_upgrade_plan.md
    ├── D-02 → building_area_and_eui_notes_round2.md
    └── D-05 → continuous_anomaly_patterns_round2.md
```
