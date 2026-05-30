# API 契约文档

这个文档用于在第一次任务分发前冻结前后端接口契约，减少集成阶段返工。

## 基础约定

- API 前缀：`/api/v1`
- 返回格式：优先使用对象包裹，列表类接口统一放在 `items`
- 时间格式：`YYYY-MM-DD HH:mm:ss`
- 数值单位：电耗 `kWh`，水耗 `m3`，温度 `℃`

## 已冻结接口

### `GET /api/v1/health`

用途：检查后端是否正常运行

### `GET /api/v1/overview`

用途：获取首页总览指标

返回核心字段：

- `total_records`
- `building_count`
- `average_cop`
- `abnormal_record_count`
- `time_range`
- `totals`

### `GET /api/v1/dataset-meta`

用途：获取字段列表、建筑选项和数据时间范围

### `GET /api/v1/buildings`

用途：返回可筛选的建筑列表

返回字段：

- `building_id`
- `building_name`
- `building_type`

### `GET /api/v1/records`

用途：查询原始记录

查询参数：

- `building_id`
- `floor_label`
- `start_time`
- `end_time`
- `limit`

返回核心字段：

- `count`
- `total_filtered_count`
- `items`

`items` 中除原始能耗字段外，会额外返回用于前端展示和演示下钻的派生字段：

- `floor_label`
- `zone_name`
- `equipment_type`
- `source_equipment_id`

### `GET /api/v1/analytics/time-summary`

用途：返回时段汇总统计

查询参数：

- `building_id`
- `floor_label`
- `start_time`
- `end_time`
- `freq`

### `GET /api/v1/analytics/building-comparison`

用途：返回建筑间对比结果

查询参数：

- `start_time`
- `end_time`

### `GET /api/v1/analytics/cop-ranking`

用途：返回建筑 COP 排名

查询参数：

- `start_time`
- `end_time`

### `GET /api/v1/analytics/anomalies`

用途：返回异常明细

查询参数：

- `building_id`
- `floor_label`
- `start_time`
- `end_time`

### `GET /api/v1/analytics/anomaly-explanations/{record_id}`

用途：返回单条异常的解释信息，包括触发规则、同建筑基线、同楼层均值、动态阈值、可能原因和处置建议。

返回核心字段：

- `record_id`
- `building_name`
- `floor_label`
- `equipment_id`
- `severity`
- `anomaly_reason`
- `conclusion`
- `metrics`
- `triggered_rules`
- `possible_cause`
- `recommended_action`

### `GET /api/v1/analytics/anomaly-reasons`

用途：返回异常原因计数

查询参数：

- `building_id`
- `floor_label`
- `start_time`
- `end_time`

### `GET /api/v1/analytics/floor-summary`

用途：返回建筑楼层与区域维度的能耗、COP、异常数量和运维判断。

查询参数：

- `building_id`
- `floor_label`
- `start_time`
- `end_time`

返回核心字段：

- `building_id`
- `building_name`
- `floor_label`
- `zone_name`
- `record_count`
- `equipment_count`
- `electricity_kwh`
- `water_m3`
- `average_cop`
- `anomaly_count`
- `anomaly_rate`
- `operation_focus`

说明：当前样例数据没有真实 BIM 楼层字段，楼层、区域和设备类型由设备编号、建筑类型和运行规则派生，适合作为课程演示级的逐层分析。

### `GET /api/v1/analytics/floor-registry`

用途：返回楼层 / 设备台账，用于展示楼层用途、面积、负责人、设备构成、健康评分和风险等级。

查询参数：

- `building_id`
- `floor_label`
- `start_time`
- `end_time`

返回核心字段：

- `building_id`
- `building_name`
- `floor_label`
- `floor_area_m2`
- `usage`
- `owner`
- `main_equipment_types`
- `health_score`
- `risk_level`
- `operation_policy`

### `GET /api/v1/analytics/equipment-summary`

用途：返回设备级运行监测结果，用于判断维护优先级。

查询参数：

- `building_id`
- `floor_label`
- `start_time`
- `end_time`

返回核心字段：

- `building_name`
- `equipment_id`
- `equipment_type`
- `floor_label`
- `zone_name`
- `latest_status`
- `latest_seen_at`
- `average_cop`
- `anomaly_count`
- `priority`
- `maintenance_hint`

### `GET /api/v1/analytics/work-orders`

用途：把异常记录转换为可执行的巡检工单和处置建议。

查询参数：

- `building_id`
- `floor_label`
- `start_time`
- `end_time`

返回核心字段：

- `work_order_id`
- `priority`
- `status`
- `building_name`
- `floor_label`
- `zone_name`
- `equipment_id`
- `equipment_type`
- `timestamp`
- `anomaly_reason`
- `possible_cause`
- `recommended_action`
- `owner_role`

### `GET /api/v1/analytics/optimization-recommendations`

用途：根据 COP、夜间负荷、异常数量和空调电耗占比生成运营优化建议。

查询参数：

- `building_id`
- `floor_label`
- `start_time`
- `end_time`

返回核心字段：

- `recommendation_id`
- `building_id`
- `building_name`
- `category`
- `priority`
- `finding`
- `action`
- `expected_impact`

### `GET /api/v1/analytics/operation-report`

用途：生成运营日报，汇总总览、重点风险、最近异常、工单状态、未来 7 天电耗估算和建议动作。

查询参数：

- `building_id`
- `floor_label`
- `start_time`
- `end_time`

返回核心字段：

- `title`
- `generated_at`
- `overview`
- `risk`
- `latest_anomaly`
- `work_order`
- `forecast`
- `recommendation`
- `action_items`

### `GET /api/v1/work-orders`

用途：读取后端持久化保存的人工工单列表。

### `POST /api/v1/work-orders`

用途：把前端选择的异常记录创建为“处理中”工单，并写入 `data/runtime/work_orders.json`。

### `PATCH /api/v1/work-orders/{work_order_id}`

用途：更新工单状态、负责人或处理备注。

### `GET /api/v1/export/csv`

用途：导出当前筛选范围内的原始记录 CSV

查询参数：

- `building_id`
- `floor_label`
- `start_time`
- `end_time`

返回形式：

- `text/csv` 文件流
- 文件名会根据建筑和时间筛选条件自动生成

### `POST /api/v1/assistant/query`

用途：智能问答入口

说明：

- 默认使用本地规则问答和知识库引用
- 若本地 `.env` 中开启 `LLM_ENABLED=true`，后端会尝试调用外部大模型增强回答
- 外部模型调用失败时自动回退本地问答，响应结构不变

请求体：

```json
{
  "question": "当前有哪些异常记录？",
  "provider": "nvidia",
  "model": "meta/llama-3.3-70b-instruct"
}
```

其中 `provider` 和 `model` 为可选字段。若不传，则使用 `.env` 中的默认模型；若外部模型未启用或调用失败，则回退本地规则问答。

响应体：

```json
{
  "answer": "字符串回答",
  "citations": [
    {
      "title": "来源标题",
      "path": "来源路径"
    }
  ],
  "follow_up": ["后续建议问题"],
  "llm_used": true,
  "llm_provider": "nvidia",
  "llm_model": "meta/llama-3.3-70b-instruct"
}
```

### `GET /api/v1/assistant/providers`

用途：返回前端可展示的外部模型选项

安全说明：

- 只返回供应商、模型名、展示标签和是否已配置
- 不返回任何 API Key 或敏感配置

响应体：

```json
{
  "enabled": true,
  "default_provider": "nvidia",
  "default_model": "meta/llama-3.3-70b-instruct",
  "options": [
    {
      "provider": "nvidia",
      "model": "meta/llama-3.3-70b-instruct",
      "label": "NVIDIA · meta/llama-3.3-70b-instruct",
      "configured": true
    }
  ]
}
```

## 协作规则

- 前端同学不要自行改返回字段名。
- 后端同学不要在未同步的情况下改接口路径。
- 若必须改契约，先改此文档，再统一通知组内。
