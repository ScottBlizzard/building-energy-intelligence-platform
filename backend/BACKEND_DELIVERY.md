# 后端独立包交付说明

负责人：王天一
交付日期：2026-05-03

---

## 一、后端现在能跑什么

后端当前可稳定运行以下接口，全部通过 29 个自动化测试：

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/health` | GET | 健康检查 |
| `/api/v1/overview` | GET | 首页总览指标 |
| `/api/v1/dataset-meta` | GET | 字段列表、建筑选项、时间范围 |
| `/api/v1/buildings` | GET | 建筑列表 |
| `/api/v1/records` | GET | 原始记录查询（支持 building_id/start_time/end_time/limit 筛选） |
| `/api/v1/analytics/time-summary` | GET | 时段汇总（支持 H/D/W/M 频率） |
| `/api/v1/analytics/building-comparison` | GET | 建筑间对比 |
| `/api/v1/analytics/cop-ranking` | GET | COP 排名 |
| `/api/v1/analytics/anomalies` | GET | 异常明细 |
| `/api/v1/analytics/anomaly-reasons` | GET | 异常原因计数 |
| `/api/v1/assistant/query` | POST | 智能问答（规则化占位） |
| `/api/v1/export/csv` | GET | **新增** CSV 导出 |

## 二、我改了哪些文件

| 文件 | 改动内容 |
|------|----------|
| `app/services/data_loader.py` | 新增 `load_dataset_or_raise()` 共享函数，统一数据加载错误处理 |
| `app/services/analysis_service.py` | 新增 `_FREQ_MAP` 映射，修复 pandas 废弃频率别名警告（H→h, M→ME） |
| `app/services/assistant_service.py` | 修复第 141 行运算符优先级 bug（`or`/`and` 未加括号） |
| `app/api/routes/data.py` | 改用共享的 `load_dataset_or_raise()`，移除重复的 `_load_dataset` |
| `app/api/routes/analytics.py` | 改用共享的 `load_dataset_or_raise()`，移除重复的 `_load_dataset` |
| `app/api/router.py` | 注册新增的 export 路由 |
| `tests/test_health.py` | 增加返回字段验证测试 |
| `tests/test_data_endpoints.py` | 增加 overview、time_range、buildings 字段、records limit 等测试 |
| `tests/test_analytics_endpoints.py` | 增加 freq 参数、building-comparison、cop-ranking 排序、anomalies 筛选等测试 |
| `tests/test_assistant_endpoint.py` | 增加异常/COP/能耗/默认回复等多场景测试 |

## 三、我新增了哪些文件

| 文件 | 用途 |
|------|------|
| `app/services/export_service.py` | CSV 导出逻辑（数据筛选、格式转换、文件名生成） |
| `app/api/routes/export.py` | CSV 导出路由 `GET /api/v1/export/csv` |
| `tests/test_export_endpoint.py` | 导出接口测试（5 个用例） |

## 四、我新增或加强了哪些接口

### 新增接口

**`GET /api/v1/export/csv`**
- 支持查询参数：`building_id`、`start_time`、`end_time`
- 返回 CSV 文件下载（StreamingResponse）
- 无数据时返回 404
- 文件名根据筛选条件自动命名

### 加强的接口稳定性

所有现有接口已确认：
- 返回结构稳定（与 `docs/06-api-contract.md` 一致）
- 空数据时不崩溃（返回空列表或零值）
- 参数错误时有明确报错（422 验证错误）
- 建筑筛选、时间筛选功能正常

## 五、我没有完成什么

1. **问答接口未接入真实大模型**：当前仍是规则化占位实现，接入 LLM/RAG 需要后续完成
2. **未新增认证/鉴权机制**：当前所有接口开放访问
3. **未做性能压测**：当前数据量较小，未测试大数据量下的性能表现
4. **`build_anomaly_summary` 硬编码 `.head(20)`**：异常明细最多返回 20 条，如需完整列表需修改此限制

## 六、许奕整合时先看哪里

1. **`app/api/router.py`** — 确认新增的 export 路由注册
2. **`app/services/data_loader.py`** — 新增的 `load_dataset_or_raise()` 共享函数，data.py 和 analytics.py 都依赖它
3. **`app/api/routes/export.py`** — 新的导出接口，前端可接入"导出 CSV"按钮
4. **`BACKEND_DELIVERY.md`**（本文件）— 交付说明

## 七、测试运行方式

```powershell
cd backend
python -m pytest tests/ -v
```

当前 29 个测试全部通过。
