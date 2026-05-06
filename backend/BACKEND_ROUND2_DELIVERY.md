# 后端独立增强包交付说明（第二轮）

负责人：王天一
交付日期：2026-05-06

---

## 一、后端现在能跑什么（第二轮增强后）

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/health` | GET | 健康检查 |
| `/api/v1/overview` | GET | 首页总览指标 |
| `/api/v1/dataset-meta` | GET | 字段列表、建筑选项、时间范围 |
| `/api/v1/buildings` | GET | 建筑列表 |
| `/api/v1/records` | GET | 原始记录查询 |
| `/api/v1/analytics/time-summary` | GET | 时段汇总 |
| `/api/v1/analytics/building-comparison` | GET | 建筑间对比 |
| `/api/v1/analytics/cop-ranking` | GET | COP 排名 |
| `/api/v1/analytics/anomalies` | GET | 异常明细 |
| `/api/v1/analytics/anomaly-reasons` | GET | 异常原因计数 |
| `/api/v1/analytics/building-detail` | GET | **新增** 建筑深度分析 |
| `/api/v1/assistant/query` | POST | 问答（增强：规则回答 + 知识库检索） |
| `/api/v1/export/csv` | GET | CSV 导出 |

测试：46 项全部通过。

## 二、我改了哪些文件

| 文件 | 改动内容 |
|------|----------|
| `app/api/routes/assistant.py` | 集成 `search_and_format_citations`，问答回复自动检索知识库补充引用 |
| `app/api/router.py` | 注册新增的 `building_detail` 路由 |

## 三、我新增了哪些文件

| 文件 | 用途 |
|------|------|
| `app/services/knowledge_search_service.py` | 知识检索服务：读取 knowledge_base/ 文件，按章节分词索引，关键词匹配检索 |
| `app/services/building_detail_service.py` | 建筑深度分析服务：单建筑总能耗/COP/异常统计 |
| `app/api/routes/building_detail.py` | 建筑深度分析路由 `GET /api/v1/analytics/building-detail` |
| `tests/test_knowledge_search_service.py` | 知识检索服务测试（7 项） |
| `tests/test_building_detail_endpoint.py` | 建筑深度分析接口测试（6 项） |
| `BACKEND_ROUND2_DELIVERY.md` | 本交付说明 |

## 四、我新增了哪些接口或服务

### 1. 知识检索服务 (`knowledge_search_service.py`)

- 读取 `knowledge_base/` 目录下所有 .md 文件（只读，不修改）
- 按 `##` 标题分章节建立内存索引
- 支持中英文混合关键词分词匹配
- `search_knowledge(query, top_k)` — 返回排序结果
- `search_and_format_citations(question)` — 返回引用和摘要
- 已集成到问答接口中：每条回答除原有硬编码引用外，自动补充知识库检索到的相关引用

### 2. 建筑深度分析接口 (`GET /api/v1/analytics/building-detail`)

- 必填参数：`building_id`
- 可选参数：`start_time`、`end_time`
- 返回结构：
  - `building_id`、`building_name`、`building_type`
  - `record_count`、`time_range`
  - `totals`（electricity_kwh、water_m3、hvac_kwh、cooling_load_kwh）
  - `average_cop`
  - `anomaly_count`
  - `top_anomaly_reasons`（前 5 条异常原因及计数）
  - `recent_records`（最近 5 条原始记录）
- 不存在的 building_id 返回 404

## 五、我测试了什么

### 新增测试（13 项）

**知识检索服务（7 项）：**
- 基础检索返回结果
- 结果有评分
- COP/能效关键词匹配
- 维护关键词匹配
- `search_and_format_citations` 返回结构完整性
- 空查询边界处理
- 缓存清理不影响结果

**建筑深度分析接口（6 项）：**
- 缺少 building_id 返回 422
- 有效 building_id 返回完整字段
- totals 包含必要字段
- 无效 building_id 返回 404
- 时间筛选正常工作
- 全部 4 栋建筑均可正常查询

### 旧接口回归确认

全部 33 项第一轮测试 + 整合后新增测试 **无一失败**。

## 六、哪些能力是"第二轮增强"

| 能力 | 状态 |
|------|------|
| 知识检索服务（关键词匹配） | **第二轮新增** |
| 知识检索集成到问答接口 | **第二轮新增** |
| 建筑深度分析接口 | **第二轮新增** |
| 建筑总能耗/COP/异常统计 | **第二轮新增** |
| CSV 导出接口 | 第一轮已有，本轮回归确认稳定 |

## 七、哪些地方我故意没动

1. **未接入真实大模型**：检索服务当前只做关键词匹配，未接 LLM。这是第三轮的内容
2. **未改 assistant_service.py**：问答的硬编码分支逻辑保留不动，检索增强在路由层叠加，不侵入已有 service
3. **knowledge_base/ 文件一字未改**：只读检索，不修改
4. **API 契约未自行修改**：新增接口独立于已有契约
5. **未做向量检索**：当前是轻量关键词匹配，向量化留待后续升级

## 八、许奕整合时先看哪里

1. **`app/api/router.py`** — 确认 building_detail 路由注册
2. **`app/api/routes/assistant.py`** — 确认知识检索集成的 `_enrich_citations` 逻辑
3. **`app/services/knowledge_search_service.py`** — 检索服务的接口和缓存机制
4. **`app/api/routes/building_detail.py`** — 建筑详情接口参数和返回格式
5. **本文件** — 了解全部变更概览
