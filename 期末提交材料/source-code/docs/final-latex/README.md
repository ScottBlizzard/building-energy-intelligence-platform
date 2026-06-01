# LaTeX 正式交付文档

本目录保存课程期末项目正式交付文档的 LaTeX 源文件和编译后的 PDF。文档样式基于实验三 `main.tex` 的 `ctexart` 模板扩展，使用 XeLaTeX 编译。

正式提交时以 `pdf-latex/` 或 `docs/final-latex/pdf/` 中的 PDF 为准。真实 `.env` 和 API Key 不得进入本目录或最终压缩包。

生成命令：

```powershell
python .\scripts\build_final_latex_documents.py --compile
```
