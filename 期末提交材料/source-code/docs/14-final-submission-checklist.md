# 期末项目最终提交清单

本清单根据课程期末项目要求整理，用于最后一轮打磨、验收、打包和 Canvas 提交。时间安排以 Canvas 通知为准，本文只记录项目组必须交付的内容。

## 1. 课程明确要求

- [ ] 完成课程项目的财务分析。
- [ ] 注意项目的设计、实现与部署，不只停留在文档或原型。
- [ ] 覆盖项目范围、项目计划、软件过程监控与控制、风险管理。
- [ ] 覆盖软件开发与维护成本、定价策略、资金与融资。
- [ ] 覆盖项目财务分析与评价。
- [ ] 最终文档应包含 SRS、SDS、SEE、SEM。
- [ ] 最终材料应包含团队开发并部署的源代码。
- [ ] 将上述所有文件打包成一个 `.zip` 文件并提交到 Canvas。

## 2. 对应到本项目需要补齐的内容

### 2.1 SRS：软件需求规格说明

- [x] 最终 SRS 已形成：`docs/17-SRS-software-requirements-specification.md`。
- [x] 项目背景与目标：见 `docs/01-requirements.md`。
- [x] 用户角色与业务场景：见 `docs/01-requirements.md` 和 `docs/03-user-manual.md`。
- [x] 功能需求：能耗数据浏览、统计分析、三维楼层风险、异常工单、AI 助手、运营日报。
- [x] MCP 需求：基于 MCP 协议的数据接入、查询统计、异常诊断和智能问答工具。
- [x] 非功能需求：可运行、可测试、可演示、REST/MCP 接口清晰、密钥不入库。
- [x] 最终交付确认阶段检查需求文档是否和当前系统功能完全一致。

### 2.2 SDS：软件设计说明

- [x] 最终 SDS 已形成：`docs/18-SDS-software-design-description.md`。
- [x] 技术方案：见 `docs/02-technical-solution.md`。
- [x] API 契约：见 `docs/06-api-contract.md`。
- [x] MCP 集成说明：见 `docs/16-mcp-integration.md`。
- [x] 数据字典与数据源说明：见 `docs/04-data-dictionary-template.md` 和 `docs/10-data-source-research.md`。
- [x] 外部大模型接入说明：见 `docs/13-llm-provider-integration.md`。
- [x] 最终交付确认阶段补充部署架构图或运行流程图，已在 SDS 中用文本架构图说明。

### 2.3 SEE：软件经济分析与评价

最终经济分析文档已形成：`docs/19-SEE-software-economic-evaluation.md`。

- [x] 开发成本估算：人员投入、开发周期、工具与环境成本。
- [x] 部署与运行成本估算：服务器、存储、网络、外部大模型 API。
- [x] 维护成本估算：数据维护、模型配置、故障处理、功能迭代。
- [x] 收益分析：节能收益、人工巡检成本节约、异常响应效率提升。
- [x] 财务评价：ROI、回收期、成本收益比和敏感性分析。
- [x] 定价策略：说明项目制、订阅制和咨询加平台混合模式。
- [x] 资金与融资：说明课程阶段、试点阶段和商业化阶段资金来源。

### 2.4 SEM：软件工程管理

最终工程管理文档已形成：`docs/20-SEM-software-engineering-management.md`。

- [x] 两轮分工与整合记录：见 `第一次任务/`、`第二次任务/`、`docs/11-first-integration-summary.md`、`docs/12-second-integration-summary.md`。
- [x] 协作规则：见 `docs/07-collaboration-rules.md`。
- [x] 集成清单：见 `docs/08-integration-checklist.md`。
- [x] 测试计划：见 `docs/09-testing-plan.md`。
- [x] MCP 补充集成记录：见 `docs/16-mcp-integration.md` 和 `docs/15-project-acceptance-report.md`。
- [x] 项目范围管理：说明哪些功能属于本期范围，哪些作为后续扩展。
- [x] 项目计划：说明两轮任务、整合、测试、演示准备的安排。
- [x] 软件过程监控与控制：说明 Git、任务文件、测试脚本、集成检查如何控制质量。
- [x] 风险管理：说明数据真实性、API 密钥、模型不可用、演示环境、成员提交质量等风险及应对。

## 3. 源代码与部署验收

- [ ] 后端 FastAPI 能正常启动。
- [ ] 前端 Vue 页面能正常启动。
- [ ] MCP Server 能通过 `.\scripts\start-mcp.ps1` 启动。
- [x] `.\scripts\check-project.ps1` 能通过。
- [x] 后端测试全部通过，当前为 `75 passed`。
- [x] MCP 专项测试已纳入后端测试。
- [x] 前端构建成功。
- [ ] `.env` 不进入 Git，真实 API Key 不出现在提交记录和压缩包公开说明中。
- [ ] `.env.example` 只保留变量名和占位符。
- [ ] 页面演示路径完整：总览、数据浏览、统计分析、三维楼层、异常工单、决策报告、AI 助手。
- [ ] 刷新页面后，关键状态仍能保持或从后端恢复，尤其是工单数据。

## 4. 最终压缩包建议结构

最终提交建议打包为一个 `.zip`，结构如下：

```text
building-energy-intelligence-platform-final.zip
|-- source-code/
|   |-- backend/
|   |-- frontend/
|   |-- data/
|   |-- knowledge_base/
|   |-- scripts/
|   |-- README.md
|   |-- .env.example
|-- documents/
|   |-- SRS-软件需求规格说明书.md
|   |-- SDS-软件设计说明书.md
|   |-- SEE-软件经济分析与评价.md
|   |-- SEM-软件工程管理说明.md
|   |-- 用户手册.md
|   |-- 测试报告.md
|   |-- 演示脚本.md
|   |-- MCP集成说明.md
|-- demo/
|   |-- 演示视频或视频链接说明.txt
|   |-- 演示PPT.pptx
|-- submission-readme.md
```

说明：如果 Canvas 只允许上传一个文件，应将全部材料放进同一个压缩包；如果允许分项提交，也建议保留该统一目录结构，避免遗漏。

## 5. 最后交付确认阶段一小时检查

- [ ] 重新拉取最新代码，确认没有未合并内容。
- [ ] 运行完整检查脚本并保存结果。
- [ ] 打开前端页面，从头到尾走一遍演示流程。
- [ ] 检查所有文档标题、项目名称、成员姓名、分工描述一致。
- [ ] 检查 MCP 说明文档和验收报告中的工具数量、测试结果与当前代码一致。
- [ ] 检查压缩包内没有 `.env`、真实 API Key、缓存目录、临时文件。
- [ ] 检查压缩包能正常解压，README 能指导评审人员运行项目。
- [ ] 确认 Canvas 上传成功，并保留上传截图或提交记录。
