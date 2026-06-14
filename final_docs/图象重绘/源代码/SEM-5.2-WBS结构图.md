@startuml
!theme plain
skinparam linetype ortho
left to right direction

rectangle "基于大模型的建筑能源智能管理与运维优化系统" as root

folder "1.0 项目管理" as L1
folder "2.0 数据与知识库" as L2
folder "3.0 后端与业务服务" as L3
folder "4.0 前端工作台" as L4
folder "5.0 测试验收与交付" as L5

root --> L1
root --> L2
root --> L3
root --> L4
root --> L5

L1 --> [1.1 项目启动\n范围、目标、团队分工]
L1 --> [1.2 计划与协作\n任务包、接口冻结、阶段门]
L1 --> [1.3 文档统筹\nSRS/SDD/SEE/SEM/实验报告]

L2 --> [2.1 能耗数据集\n4864 条记录、4 栋建筑]
L2 --> [2.2 数据质量\nL0-L3 验收、口径红线]
L2 --> [2.3 知识库与 RAG\n手册、术语、FAQ、检索卡片]

L3 --> [3.1 REST API\n数据、分析、导出、认证]
L3 --> [3.2 分析与决策\n异常、风险、反事实]
L3 --> [3.3 工单闭环\n派单、接单、复核、设备级修复]
L3 --> [3.4 时间沙盘\n时钟、故障、维修干预]
L3 --> [3.5 预算与 ROI\nKPI、NPV、IRR、EAA]
L3 --> [3.6 MCP 与 LLM\n工具、资源、接地问答]
L3 --> [3.7 持久化\nCSV/JSON 默认、MySQL 可切换]

L4 --> [4.1 管理员工作台\n总览、统计、工单、预算、ROI]
L4 --> [4.2 工人工作台\n我的工单、处理提交、现场附件]
L4 --> [4.3 可视化组件\nKPI、趋势、对比、3D 风险]
L4 --> [4.4 API 封装\n错误提示、空态、演示重置]

L5 --> [5.1 自动化测试\n119 个 pytest 用例]
L5 --> [5.2 前端构建\nVite build]
L5 --> [5.3 MCP 验收\nTools/Resources/stdio]
L5 --> [5.4 浏览器验收\n角色闭环、预算、ROI、问答]
L5 --> [5.5 交付打包\nPPT/Demo/最终材料]

@enduml