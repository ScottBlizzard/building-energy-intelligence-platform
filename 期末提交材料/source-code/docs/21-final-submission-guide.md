# 最终提交与打包说明

本文档用于最后提交前检查和打包，目标是保证评审人员收到的 zip 包可以清楚看到源码、文档、测试结果和演示材料。

正式提交文档以 `docs/final-latex/pdf/` 中的 LaTeX 编译版 PDF 为准，并已同步到 `期末提交材料/documents/pdf-latex/`。Markdown 文档保留为过程资料和快速查阅入口。

## 1. 提交前必须确认

- [ ] 本地已拉取最新 `main` 分支。
- [ ] 运行 `.\scripts\check-project.ps1` 通过。
- [ ] 前端可以访问 `http://127.0.0.1:5173`。
- [ ] 后端文档可以访问 `http://127.0.0.1:8000/docs`。
- [ ] README 中的运行步骤准确。
- [ ] `documents/pdf-latex/` 中 8 份正式 LaTeX PDF 已生成。
- [ ] `documents/latex/` 中 8 份 LaTeX 源文件已保留。
- [ ] SRS、SDD/SDS、SEE、SEM 已采用正式模板重写。
- [ ] 测试与验收、用户部署、数据接口/MCP、最终提交说明已生成 PDF。
- [ ] PPT 和演示视频已由对应负责人补齐。
- [ ] zip 包中没有 `.env` 和真实 API Key。

## 2. 推荐压缩包结构

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
|   |-- .gitignore
|-- documents/
|   |-- pdf-latex/
|   |   |-- 01-SRS-软件需求规格说明书.pdf
|   |   |-- 02-SDD-SDS-软件设计说明书.pdf
|   |   |-- 03-SEE-软件经济分析与评价.pdf
|   |   |-- 04-SEM-软件工程管理说明.pdf
|   |   |-- 05-测试与验收报告.pdf
|   |   |-- 06-用户手册与部署说明.pdf
|   |   |-- 07-数据接口与MCP说明.pdf
|   |   `-- 08-最终提交说明.pdf
|   |-- latex/
|   `-- markdown/
|-- demo/
|   |-- 演示PPT.pptx
|   |-- 演示视频.mp4 或 视频链接说明.txt
|-- submission-readme.md
```

## 3. 源码包应包含

- `backend/`
- `frontend/`
- `data/`
- `knowledge_base/`
- `scripts/`
- `docs/`
- `README.md`
- `.env.example`
- `.gitignore`

## 4. 源码包不应包含

- `.env`
- `frontend/node_modules/`
- `frontend/dist/`
- `.pytest_cache/`
- `__pycache__/`
- `data/runtime/`
- 个人无关 PDF 或其他课程实验文件
- 内部任务分配过程材料：`第一次任务/`
- 内部任务分配过程材料：`第二次任务/`
- 非期末项目材料：`实验二/`
- 真实 API Key、Token、密码

## 5. 面向评审人员的运行说明

可以在 `submission-readme.md` 中写入以下内容：

```text
本项目为“基于大模型的建筑能源智能管理与运维优化系统”。

运行方式：
1. 安装 Python 3.11 和 Node.js。
2. 在项目根目录复制 .env.example 为 .env。
3. 安装后端依赖：pip install -r backend/requirements.txt。
4. 启动后端：.\scripts\start-backend.ps1。
5. 安装前端依赖：cd frontend 后执行 npm install。
6. 启动前端：.\scripts\start-frontend.ps1。
7. 浏览器访问：http://127.0.0.1:5173。
8. 可选：运行 .\scripts\check-project.ps1 进行完整自检。

说明：
- .env.example 不包含真实 API Key。
- 如果没有真实外部模型 Key，系统仍可使用本地知识库问答。
- MCP Server 可通过 .\scripts\start-mcp.ps1 启动。
```

## 6. 最终演示建议顺序

1. 打开 README，说明项目结构和运行方式。
2. 打开总览页，展示 KPI 和三维楼宇风险态势。
3. 点击异常楼层，跳转统计分析。
4. 展示异常明细、异常解释、楼层台账和设备分析。
5. 在工单中心创建并完成一个工单。
6. 在决策报告页生成运营日报。
7. 在 AI 助手中提问当前异常风险。
8. 展示 API 文档和 MCP 集成说明。
9. 展示测试结果和最终文档。
10. 总结经济分析和项目管理过程。

## 7. 最终提交口径

答辩或报告中可以采用以下表述：

本项目已完成建筑能源智能管理系统的核心建设目标，形成了前端 Web 工作台、FastAPI 后端、MCP Server、样例数据集、知识库、外部大模型可选接入、异常分析、工单闭环、运营报告和完整交付文档。当前系统通过后端自动化测试和前端构建测试，具备课程期末项目演示和提交条件。

## 8. 提交前安全检查

提交 zip 前建议执行：

```powershell
git status --short
.\scripts\check-project.ps1
python .\scripts\build_final_latex_documents.py --compile
```

人工检查：

- 搜索 zip 包中是否存在 `.env`。
- 搜索是否存在 `nvapi-`、`AIza`、`sk-`、`gsk_`、`sk-or-v1-` 等 Key 前缀。
- 解压 zip 到临时目录，确认 README 和文档能正常打开。
- 打开 `documents/pdf-latex/`，确认 8 份正式 PDF 均可正常阅读。
- 确认 PPT 和视频文件能正常播放。

## 9. 当前剩余事项

系统侧已经完成最终打磨。提交侧仍需由 PPT 和视频负责人补齐：

- 最终答辩 PPT。
- 演示视频或视频链接。
- Canvas 上传截图或提交记录。
