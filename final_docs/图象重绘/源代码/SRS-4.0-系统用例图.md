@startuml
left to right direction
skinparam actorStyle awesome

actor "系统管理员" as SysAdmin
actor "能源运营管理员" as EnergyAdmin
actor "现场工人" as Worker
actor "数据维护者" as DataMaintainer
actor "AI 客户端" as Agent
actor "所有用户" as AllUsers

package "建筑能源智能管理与运维优化系统" {
  
  package "基础设施与组织管理" {
    usecase "UC-00 用户登录与权限管理" as UC00
    usecase "UC-01 管理样例数据与演示状态" as UC01
  }
  
  package "建筑能源运维生命周期管理" {
    usecase "UC-02 查看能源总览与数据查询" as UC02
    usecase "UC-03 统计分析与异常诊断" as UC03
    usecase "UC-04 派发维修工单" as UC04
    usecase "UC-05 处理现场工单" as UC05
    usecase "UC-06 复核关闭工单" as UC06
    usecase "UC-07 时间沙盘与反事实" as UC07
  }
  
  package "智能决策与接入功能" {
    usecase "UC-08 预算执行与闭环改善" as UC08
    usecase "UC-09 ROI 改造与运营报告" as UC09
    usecase "UC-10 可信智能问答" as UC10
    usecase "UC-11 MCP 工具调用" as UC11
  }
  
  package "支撑功能" {
    usecase "UC-12 项目检查与质量验收" as UC12
  }
  
}

AllUsers --> UC00
SysAdmin --> UC01
SysAdmin --> UC12
DataMaintainer --> UC01
EnergyAdmin --> UC02
EnergyAdmin --> UC03
EnergyAdmin --> UC04
EnergyAdmin --> UC06
EnergyAdmin --> UC07
EnergyAdmin --> UC08
EnergyAdmin --> UC09
EnergyAdmin --> UC10
Worker --> UC05
Worker --> UC10
Agent --> UC11


UC04 ..> UC03 : <<extend>>
UC06 ..> UC07 : <<include>>
UC10 ..> UC02 : <<include>>
UC11 ..> UC02 : <<include>>
UC11 ..> UC03 : <<include>>
@enduml