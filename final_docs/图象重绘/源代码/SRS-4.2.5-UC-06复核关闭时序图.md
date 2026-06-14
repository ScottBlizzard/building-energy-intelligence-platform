@startuml
title 工单复核关闭

actor "管理员" as Admin
participant "工单API" as API
participant "工单状态机" as Engine
participant "沙盘服务" as Sim
participant "决策服务" as Decision

Admin -> API : PATCH /work-orders/{id}/review
activate API

API -> Engine : 校验待复核状态
activate Engine

Engine -> Engine : 关闭工单并写入时间线
activate Engine

Engine -> Sim : 登记维修干预
activate Sim

Sim --> Engine : 干预记录完成
deactivate Sim

Engine -> Decision : 刷新预算和报告上下文
activate Decision

Decision --> Engine : 
deactivate Decision

Engine --> API : 
deactivate Engine

API --> Admin : 返回已关闭工单
deactivate API

@enduml