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
- `start_time`
- `end_time`
- `limit`

返回核心字段：

- `count`
- `total_filtered_count`
- `items`

### `GET /api/v1/analytics/time-summary`

用途：返回时段汇总统计

查询参数：

- `building_id`
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
- `start_time`
- `end_time`

### `GET /api/v1/analytics/anomaly-reasons`

用途：返回异常原因计数

查询参数：

- `building_id`
- `start_time`
- `end_time`

### `GET /api/v1/export/csv`

用途：导出当前筛选范围内的原始记录 CSV

查询参数：

- `building_id`
- `start_time`
- `end_time`

返回形式：

- `text/csv` 文件流
- 文件名会根据建筑和时间筛选条件自动生成

### `POST /api/v1/assistant/query`

用途：智能问答入口

请求体：

```json
{
  "question": "当前有哪些异常记录？"
}
```

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
  "follow_up": ["后续建议问题"]
}
```

## 协作规则

- 前端同学不要自行改返回字段名。
- 后端同学不要在未同步的情况下改接口路径。
- 若必须改契约，先改此文档，再统一通知组内。
