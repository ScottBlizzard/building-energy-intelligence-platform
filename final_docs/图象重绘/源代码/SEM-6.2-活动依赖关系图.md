@startuml
!theme plain
skinparam componentStyle rectangle

[数据集/字典] as A
[后端分析服务] as B
[REST API] as C
[MCP Server] as D
[Vue 工作台] as E
[pytest 接口测试] as F
[角色工单闭环] as G
[时间沙盘干预] as H
[预算/KPI 反馈] as I
[ROI/决策报告] as J
[知识库/LLM] as K
[数据质量 L0-L3] as L

A --> B
B --> C
B --> D
C --> E
C --> F
E --> G
G --> H
H --> I
H --> J
K --> D
K --> E
L --> B
L --> I
L --> J

@enduml