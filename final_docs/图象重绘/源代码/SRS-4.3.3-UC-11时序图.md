@startuml
title MCP工具调用

actor "AI客户端" as Client
participant "MCP Server" as MCP
participant "工具路由" as Router
participant "后端服务层" as Service

Client -> MCP : 建立 stdio 或 HTTP 连接
activate MCP

MCP --> Client : 返回 Tools 和 Resources 列表
deactivate MCP

Client -> MCP : 调用 Tool 并传入参数
activate MCP

MCP -> Router : 校验工具名和参数
activate Router

Router -> Service : 调用数据/分析/工单/问答服务
activate Service

Service --> Router : 返回结构化业务结果
deactivate Service

Router --> MCP : 封装 MCP 响应
deactivate Router

MCP --> Client : 返回结果或结构化错误
deactivate MCP

@enduml