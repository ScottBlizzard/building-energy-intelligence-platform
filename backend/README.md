# Backend 说明

后端基于 FastAPI 和 MCP Python SDK，负责样例数据读取、查询、统计分析、问答接口封装，以及面向 AI 客户端的 MCP 数据接入能力。

## 当前目录

- `app/api/routes/`：对外接口
- `app/mcp_server.py`：MCP Server 入口，封装数据查询、分析、异常诊断、运营报告和智能问答工具
- `app/services/`：数据读取、分析、问答逻辑
- `app/core/`：配置
- `tests/`：REST 接口、服务逻辑、MCP Server 和 stdio 集成测试

## 当前已实现能力

- 健康检查
- 数据概览
- 建筑列表与数据元信息
- 原始记录查询
- 时间汇总、建筑对比、COP 排名、异常分析
- 楼层区域分析、设备运行监测、异常工单和运营优化建议
- 原始记录 CSV 导出
- 规则问答与知识文件引用
- 可选外部大模型增强问答，默认关闭，失败时回退本地问答
- MCP Tools：数据元信息、建筑列表、记录查询、统计分析、异常解释、运营报告、知识库检索和智能问答
- MCP Resources：数据集元信息、建筑清单、运营报告和知识库入口

## MCP 启动方式

默认 stdio transport，适合支持 MCP 的本地客户端：

```powershell
.\scripts\start-mcp.ps1
```

HTTP 演示或调试模式：

```powershell
.\scripts\start-mcp.ps1 -Transport streamable-http -HostAddress 127.0.0.1 -Port 8765
```

stdio 模式下 PowerShell 窗口会保持等待，这是正常的协议行为；stdout 会保留给 MCP JSON-RPC 消息，手动停止可按 `Ctrl+C`。

## 当前验证结果

- MCP 专项测试：`6 passed`
- 后端完整测试：`75 passed, 1 warning`

## 后续建议重点

- 接入真实传感器或数据库时，优先保持当前 API 字段兼容
- 将问答和 MCP 工具链升级为更完整的检索增强生成链路
- 增加认证、日志和更细粒度错误处理
- 持续完善测试覆盖
