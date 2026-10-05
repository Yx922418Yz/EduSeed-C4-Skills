# C4C 教学说明：作业自动求解与排版流水线（LiYaxuan_C4C_homework-solver）

## 这个技能能做什么

把一份作业文件（Markdown / PDF / Word / 图片）变成一份**带完整解题步骤的 PDF 解答**，
全程一条命令，不需要人工解题。

支持的科目（四类）：
- **微积分**：极限、切线、ε-δ 证明
- **线性代数**（本次新增）：行列式、逆矩阵、特征值特征向量、矩阵秩、线性方程组
- **微分方程**（本次新增）：一阶可分离、一阶线性、二阶常系数
- **大学物理·力学**（本次新增）：匀变速直线运动、自由落体、牛顿第二定律、圆周运动

## 怎么用

```bash
# 1. 安装依赖
python -m pip install sympy pyyaml pdfplumber python-docx

# 2. 一条命令跑通全流程（--compile 会编译 PDF）
python scripts/pipeline.py 作业文件.md 输出目录 --compile --course "线性代数" --student "LiYaxuan" --title "作业解答"
```

跑完会在输出目录生成 5 个文件：
| 文件 | 内容 |
|------|------|
| `1_ingested.json` | 摄入后的结构化文本 |
| `2_parsed.json` | 拆好的题目 + 类型分类 |
| `3_solutions.json` | 每题的步骤与答案 |
| `homework.tex` | LaTeX 源码 |
| `homework.pdf` | 最终可提交的解答 PDF |

## 想要更聪明的解答（可选）

配置任一国产大模型 Key，规则解不出的证明/概念题会自动交给大模型深解：

```powershell
$env:DASHSCOPE_API_KEY = "sk-通义千问Key"   # 或 MOONSHOT_API_KEY（Kimi）
```

不配置也能用——自动降级为纯 SymPy 求解，完全离线。

## 解题原理（写给使用者）

1. **摄入**：按文件类型读取文本（PDF 用 pdfplumber，Word 用 python-docx）；
2. **解析**：识别题号、提取公式，用关键词判断题目类型（矩阵/方程/物理/极限…）；
3. **求解**：按类型调用 SymPy 符号计算（行列式、解方程组、dsolve 微分方程、公式模板算物理），失败再降级 LLM；
4. **排版**：把步骤和答案写成 LaTeX；
5. **编译**：调用本机 LaTeX 编译成 PDF。

## 与其他技能/工具的配合

- 作业 PDF 由 C4A 技能评审（本包也带 C4A 的评审逻辑可复测）；
- 生成的 `homework.tex` 可在 Overleaf 在线编译（无 LaTeX 环境时）；
- 与 C4B 公众号技能配合：把解答写成公众号推文排版。

## 常见问题

| 问题 | 怎么办 |
|------|--------|
| 提示 pdfplumber 未安装 | `python -m pip install pdfplumber` |
| 没有 LaTeX | 去掉 `--compile`，把 homework.tex 丢到 overleaf.com |
| 某题显示 unsolved | 配置 LLM Key 后重跑；或人工补解（reason 字段会说明原因） |
| 扫描版 PDF 读不出字 | 需 OCR（技能已留 pytesseract 扩展点） |
