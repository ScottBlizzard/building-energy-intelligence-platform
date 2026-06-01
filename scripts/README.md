# 脚本目录说明

本目录存放本地开发和演示用脚本。当前提供前端、后端、MCP Server、验证和样例数据生成脚本。

## 当前脚本

- `start-backend.ps1`：启动 FastAPI 后端，默认 `http://127.0.0.1:8000`
- `start-frontend.ps1`：启动 Vue/Vite 前端，默认 `http://127.0.0.1:5173`
- `start-mcp.ps1`：启动 MCP Server，默认 stdio transport，也支持 `streamable-http`
- `check-project.ps1`：执行项目验证
- `generate_sample_dataset.py`：生成样例能耗数据

## MCP 启动示例

默认 stdio transport：

```powershell
.\scripts\start-mcp.ps1
```

HTTP transport：

```powershell
.\scripts\start-mcp.ps1 -Transport streamable-http -HostAddress 127.0.0.1 -Port 8765
```

stdio 模式下终端安静等待是正常现象，它在等待 MCP 客户端通过标准输入输出发送协议消息。

## 可扩展脚本

- 数据清洗脚本
- 数据扩充脚本
- 测试脚本
- 一键演示脚本

