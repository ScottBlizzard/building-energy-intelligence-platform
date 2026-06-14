@startuml
!include <C4/C4_Deployment>
skinparam componentStyle rectangle

node "浏览器" as Browser <<设备>> {
  component "http://127.0.0.1:5173" as BrowserComp
}

node "Vite Dev Server\n[5173]" as Vite <<进程>> {
  component "Vite Dev Server" as ViteComp
}

node "FastAPI/Uvicorn\n[127.0.0.1:8000]" as API <<进程>> {
  component "FastAPI/Uvicorn" as APIComp
}

node "MCP Server\n[stdio 或 8765/mcp]" as MCP <<进程>> {
  component "MCP Server" as MCPComp
}

node "MCP Client" as Client <<设备>> {
  component "MCP Client" as ClientComp
}

database "CSV/JSON/Markdown\n(data + knowledge_base)" as Files <<文件系统>>

database "MySQL 8.x\n(可选)" as MySQL <<数据库>>

node "外部 LLM API\n(可选)" as LLM <<外部系统>> {
  component "外部 LLM API" as LLMComp
}

BrowserComp --> ViteComp : http
ViteComp --> APIComp : /api/v1 代理
APIComp <--> Files : 读写
APIComp <--> MySQL : JDBC/ODBC
APIComp ..> LLMComp : HTTP (可选)
ClientComp --> MCPComp : 调用
MCPComp <--> Files : 读写
MCPComp <--> MySQL : JDBC
MCPComp ..> LLMComp : HTTP (可选)

@enduml