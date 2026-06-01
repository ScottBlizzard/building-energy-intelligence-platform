# 文档目录说明

本目录中的正式提交文档以 `pdf-latex/` 为准，全部由 `latex/` 中的 LaTeX 源文件通过 XeLaTeX 编译生成。

- `pdf-latex/`：正式提交版 PDF，包含 SRS、SDD/SDS、SEE、SEM、测试与验收、用户手册与部署、数据接口/MCP、最终提交说明。
- `latex/`：正式提交版 LaTeX 源文件，可用于重新编译 PDF。
- `markdown/`：项目过程资料和早期 Markdown 文档，保留用于快速查阅，不作为最终正式版优先入口。
- `pdf/`：早期 Markdown 转换 PDF，保留用于过程备查；最终评审请优先查看 `pdf-latex/`。

重新生成正式 PDF 的命令：

```powershell
python .\scripts\build_final_latex_documents.py --compile
```
