# 数据字典模板

建议最终交付时至少整理出如下字段说明表。

| 字段名 | 类型 | 是否必填 | 含义 | 示例 | 备注 |
| --- | --- | --- | --- | --- | --- |
| record_id | string | 是 | 记录唯一编号 | R0001 | 主键 |
| building_id | string | 是 | 建筑编号 | BLD-A | 可用于筛选 |
| building_name | string | 是 | 建筑名称 | 综合教学楼A | 展示字段 |
| building_type | string | 是 | 建筑类型 | teaching | 教学楼/办公楼等 |
| timestamp | datetime | 是 | 采集时间 | 2026-04-01 08:00:00 | 建议精确到小时 |
| electricity_kwh | float | 是 | 电耗 | 285.0 | 单位 kWh |
| water_m3 | float | 否 | 水耗 | 14.5 | 单位 m3 |
| hvac_kwh | float | 是 | 空调系统电耗 | 96.0 | 可用于 COP |
| cooling_load_kwh | float | 是 | 制冷负荷折算值 | 302.0 | 可用于 COP |
| equipment_status | string | 是 | 设备状态 | normal | normal/abnormal |

最终版应补齐更多字段，并和实际数据文件保持严格一致。

