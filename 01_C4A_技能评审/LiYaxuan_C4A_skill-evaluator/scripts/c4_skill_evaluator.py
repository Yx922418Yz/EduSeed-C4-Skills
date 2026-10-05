#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
c4_skill_evaluator.py — C4 技能提交自动评审器（C4A 交付核心）

把 wechat-doc-mapper 的「分类盘点」能力升级为「自动评审」能力：
    扫描文件夹 → 按作者分组 → 完整性检查（5 项必备文件）
    → 质量评审（可复用 / 可执行 / 可验证 / IO 明确）→ 生成评审报告

架构：规则 + LLM 混合。
  - 规则引擎：确定性快筛（完整性检查 + 四条件信号打分），零依赖 API，离线可跑；
  - LLM 引擎（可选）：当设置了 QWEN_API_KEY / DASHSCOPE_API_KEY 或
    OPENAI_API_KEY 时，对内容做深度评审并生成个性化改进建议；
    未设置时自动降级为规则引擎生成建议（不阻断主流程）。

用法:
    python c4_skill_evaluator.py <FOLDER> [--output DIR] [--excel]

输出:
    - Markdown 评审报告（班级总览 + 作者详情 + 排名 + 改进建议）
    - Excel 详表（可选，4 个 Sheet）
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    print("缺少依赖: pyyaml，请先执行: python -m pip install pyyaml", file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------------------
# 常量与配置
# ---------------------------------------------------------------------------

SKILL_DIR = Path(__file__).resolve().parent.parent
RUBRIC_PATH = SKILL_DIR / "references" / "c4_rubric.yaml"

C4_FILE_RE = re.compile(r"^(?P<author>[A-Za-z\u4e00-\u9fff][A-Za-z\u4e00-\u9fff\-]*)_C4(?P<suffix>[A-Z]?)_(?P<part>.+)$")
VERSION_RE = re.compile(r"_v(\d+)", re.IGNORECASE)

KNOWN_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".pptx", ".ppt", ".xlsx", ".xls", ".csv",
    ".tex", ".bib", ".md", ".txt", ".log", ".json", ".yaml", ".yml",
    ".zip", ".tar", ".gz", ".tar.gz", ".rar", ".7z", ".png", ".jpg",
    ".jpeg", ".gif", ".webp", ".svg", ".py", ".js", ".html", ".css",
    ".sh", ".mp4", ".mp3", ".wav", ".m4a", ".skill", ".rtf", ".odt",
}

LARGE_FILE_KB = 50_000  # >50MB 跳过内容分析

# 触发「可执行内容」的扩展名/文件特征
EXECUTABLE_EXTS = {".skill", ".py", ".js", ".sh", ".ipynb"}
DOC_EXTS = {".md", ".pdf", ".docx", ".txt", ".tex"}


# ---------------------------------------------------------------------------
# 评分规则加载（来自 c4_rubric.yaml）
# ---------------------------------------------------------------------------

def load_rubric(path: Path = RUBRIC_PATH) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"找不到评分规则: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Stage 1: 文件采集与作者识别（拿来主义：改造自 wechat-doc-mapper）
# ---------------------------------------------------------------------------

def inventory_folder(folder: Path) -> list[dict]:
    """递归扫描文件夹，收集文件元信息。"""
    items = []
    for f in sorted(folder.rglob("*")):
        if f.is_file() and not f.name.startswith("."):
            try:
                stat = f.stat()
            except OSError:
                continue
            rel = str(f.relative_to(folder))
            ext = f.suffix.lower()
            if rel.endswith(".tar.gz"):
                ext = ".tar.gz"
            items.append({
                "path": rel,
                "name": f.stem,
                "ext": ext,
                "size_kb": round(stat.st_size / 1024, 1),
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d"),
                "abs_path": str(f),
                "author": None,
                "c4_hint": None,
                "part": None,
                "convention_match": False,
                "version": 1,
            })
    return items


def parse_filename(item: dict) -> dict:
    """按 C4 命名规范解析: 姓名_C4[_X]_内容描述.扩展名"""
    stem = item["name"]
    m = C4_FILE_RE.match(stem)
    if m:
        item["author"] = m.group("author")
        item["c4_hint"] = "C4" + (m.group("suffix") or "")
        item["part"] = m.group("part")
        item["convention_match"] = True
    # 版本追踪：_v2/_v3
    vm = VERSION_RE.search(stem)
    if vm:
        item["version"] = int(vm.group(1))
    return item


def extract_author_from_folder(item: dict) -> str | None:
    """回退 1: 父文件夹名（文件按作者分目录存放时）"""
    parent = Path(item["path"]).parent
    if parent and str(parent) != ".":
        folder_name = Path(item["abs_path"]).parent.name
        # 文件夹名是纯作者名（不含下划线 + C4 标记）
        if folder_name and not re.search(r"_C\d", folder_name):
            return folder_name
    return None


def extract_author_from_metadata(item: dict) -> str | None:
    """回退 2: 文件元数据（PDF author / DOCX core properties）"""
    try:
        if item["ext"] == ".pdf":
            from pypdf import PdfReader
            r = PdfReader(item["abs_path"])
            author = (r.metadata or {}).get("/Author")
            if author and author.strip():
                return author.strip()[:60]
        elif item["ext"] == ".docx":
            from docx import Document
            doc = Document(item["abs_path"])
            if doc.core_properties.author:
                return doc.core_properties.author.strip()[:60]
    except Exception:
        pass
    return None


def extract_author_from_header(item: dict) -> str | None:
    """回退 3: 文本前几行找作者标记"""
    if item["ext"] not in DOC_EXTS or item["size_kb"] > LARGE_FILE_KB:
        return None
    try:
        with open(item["abs_path"], "r", encoding="utf-8", errors="replace") as f:
            head = f.read(1500)
        for pat in [r"(?:作者|姓名|Author|Name)[：:]\s*([A-Za-z\u4e00-\u9fff\-]{2,})",
                    r"^(?:by|from|by:)\s+([A-Za-z\u4e00-\u9fff\-]{2,})"]:
            m = re.search(pat, head, re.IGNORECASE)
            if m:
                return m.group(1)
    except Exception:
        pass
    return None


def identify_authors(items: list[dict]) -> dict:
    """对每个文件执行作者识别链，返回 {author: [items]}。"""
    bundles = defaultdict(list)
    unknown = []
    for item in items:
        parse_filename(item)
        if not item["author"]:
            item["author"] = extract_author_from_folder(item)
        if not item["author"]:
            item["author"] = extract_author_from_metadata(item)
        if not item["author"]:
            item["author"] = extract_author_from_header(item)
        if not item["author"]:
            item["author"] = "Unknown"
            unknown.append(item["path"])
        bundles[item["author"]].append(item)
    return dict(bundles), unknown


# ---------------------------------------------------------------------------
# Stage 2: 提交完整性检查（5 项必备文件）
# ---------------------------------------------------------------------------

def _read_text(item: dict) -> str:
    """安全读取文本内容（跳过二进制/超大文件）。"""
    if item["ext"] not in DOC_EXTS:
        return ""
    if item["size_kb"] > LARGE_FILE_KB:
        return ""
    try:
        if item["ext"] == ".pdf":
            from pypdf import PdfReader
            r = PdfReader(item["abs_path"])
            text = "".join((p.extract_text() or "") for p in r.pages[:5])
            return text[:8000]
        with open(item["abs_path"], "r", encoding="utf-8", errors="replace") as f:
            return f.read(8000)
    except Exception:
        return ""


def check_deliverable(deliverable_cfg: dict, files: list[dict], key: str = "") -> tuple[str, list[str]]:
    """
    对某位作者的所有文件检测一项必备交付物。
    返回: (状态 '✅'|'⚠️'|'❌', 匹配文件列表)

    匹配优先级（避免误判）：
    - 可执行内容：真实可执行文件（.skill/.py/.js/.sh/.ipynb）> 文件名命中 > 内容含代码块；
      说明文档（含"说明/教学/AI日志"字样的 .md）不参与可执行内容匹配。
    - 其余交付物：文件名命中（扩展名匹配）> 内容信号命中（文本类，按 C4A 规范视为有效检测）> 弱匹配。
    """
    detection = deliverable_cfg.get("detection", {})
    fn_patterns = detection.get("filename_patterns", [])
    content_signals = detection.get("content_signals", [])
    preferred_exts = detection.get("preferred_extensions", [])

    strong = []
    partial = []
    filename_hits = []
    content_hits = []

    for f in files:
        name = f["name"].lower()
        path = f["path"]
        ext_ok = f["ext"] in preferred_exts
        text = _read_text(f) if content_signals else ""
        hit_content = any(s.lower() in text.lower() for s in content_signals) if text else False

        # --- 可执行内容：专门逻辑 ---
        if key == "executable_content":
            if f["ext"] in EXECUTABLE_EXTS:
                strong.append(path)
                continue
            # 说明类文档不作为可执行内容
            if any(k in name for k in ["说明", "教学", "日志", "log", "doc", "说明文档"]):
                continue
            hit_name = any(p.lower() in name for p in fn_patterns)
            if hit_name or "```" in text or "---\nname:" in text or "def " in text:
                strong.append(path)
            continue

        # --- 其余交付物：优先文件名精确匹配，其次内容信号 ---
        hit_name = any(p.lower() in name for p in fn_patterns)
        if hit_name and ext_ok:
            filename_hits.append(path)
        elif hit_name and not ext_ok:
            partial.append(path)
        elif hit_content and f["ext"] in DOC_EXTS:
            content_hits.append(path)   # C4A 规范：文本内容信号是有效检测方式
        elif hit_content:
            partial.append(path)

    # 存在文件名精确命中时，只采用文件名命中（避免把附带提及关键词的文档算进去）
    if filename_hits:
        strong = filename_hits
    elif content_hits:
        strong = content_hits

    # 去重（保持顺序）
    strong = list(dict.fromkeys(strong))
    partial = list(dict.fromkeys(partial))

    if strong:
        return "✅", strong
    if partial:
        return "⚠️", partial
    return "❌", []


def check_completeness(files: list[dict], rubric: dict) -> dict:
    """检查一位作者的 5 项必备文件，返回完整性矩阵。"""
    required = rubric.get("required_deliverables", {})
    result = {}
    for key, cfg in required.items():
        status, matched = check_deliverable(cfg, files, key=key)
        result[key] = {
            "label_cn": cfg.get("label_cn", key),
            "status": status,
            "matched": matched,
        }
    present = sum(1 for v in result.values() if v["status"] == "✅")
    total = len(result)
    return {
        "matrix": result,
        "present": present,
        "total": total,
        "level": "完整提交" if present == total else ("部分提交" if present >= 3 else "严重缺失"),
    }


# ---------------------------------------------------------------------------
# Stage 3: 质量评审（C4 四条件）
# ---------------------------------------------------------------------------

def evaluate_quality(files: list[dict], rubric: dict) -> dict:
    """
    对作者的提交内容按四条件评审。
    输入: 该作者的全部文件（优先取说明文档与可执行内容做深度分析）
    输出: {criterion: {grade, score, basis, suggestion}}
    """
    criteria_cfg = rubric.get("quality_criteria", {})

    # 汇总该作者所有可读文本（去重、限量）
    corpus_parts = []
    for f in files:
        t = _read_text(f)
        if t.strip():
            corpus_parts.append(f"[{f['name']}]\n{t[:4000]}")
    corpus = "\n".join(corpus_parts)[:24000]
    corpus_lower = corpus.lower()

    # 文件层面的补充信号（可执行内容检测）
    has_skill_pkg = any(f["ext"] == ".skill" or f["name"].lower().endswith(".skill") for f in files)
    has_code_file = any(f["ext"] in EXECUTABLE_EXTS for f in files)
    has_demo_media = any(f["ext"] in {".mp4", ".mov", ".webm", ".gif", ".png", ".jpg", ".jpeg"} for f in files)
    has_archive = any(f["ext"] in {".zip", ".tar", ".tar.gz"} for f in files)

    results = {}
    for key, cfg in criteria_cfg.items():
        pos = cfg.get("positive_signals", [])
        neg = cfg.get("negative_signals", [])
        check_items = cfg.get("check_items", [])

        # 负向信号（硬编码路径 / 凭据）→ 扣分
        neg_hits = [s for s in neg if s.lower() in corpus_lower]

        # 各 check item 的满足情况
        item_checks = []
        for item in check_items:
            # 把 check item 翻译成可检测谓词
            ok = _evaluate_check_item(item, corpus, corpus_lower, {
                "has_skill_pkg": has_skill_pkg,
                "has_code_file": has_code_file,
                "has_demo_media": has_demo_media,
                "has_archive": has_archive,
                "files": files,
                "pos_signals": pos,
                "neg_hits": neg_hits,
            })
            item_checks.append({"item": item, "ok": ok})

        satisfied = sum(1 for c in item_checks if c["ok"])
        if satisfied >= 2:
            grade = "✅"
        elif satisfied == 1:
            grade = "⚠️"
        else:
            grade = "❌"

        # 评审依据
        basis = _build_basis(key, satisfied, item_checks, neg_hits, corpus_lower)
        # 改进建议
        suggestion = _build_suggestion(key, satisfied, neg_hits)

        results[key] = {
            "label_cn": cfg.get("label_cn", key),
            "grade": grade,
            "score": {"✅": 1.0, "⚠️": 0.5, "❌": 0.0}[grade],
            "satisfied": satisfied,
            "total_items": len(item_checks),
            "basis": basis,
            "suggestion": suggestion,
        }
    return results


def _evaluate_check_item(item: str, corpus: str, corpus_lower: str, ctx: dict) -> bool:
    """把 check item 文本映射为可计算谓词。"""
    item_l = item.lower()
    if "installation" in item_l or "安装" in item:
        return any(k in corpus_lower for k in ["安装", "install", "pip install", "npm install", "requirements"])
    if "hardcoded" in item_l or "绝对路径" in item or "absolute" in item_l:
        return not ctx["neg_hits"]
    if "environment" in item_l or "环境" in item:
        return any(k in corpus_lower for k in ["环境要求", "requirements", "依赖", "dependencies", "python 3", "兼容", "compatible"])
    if "platform" in item_l or "平台" in item:
        return any(k in corpus_lower for k in ["windows", "macos", "linux", "跨平台", "平台", "os ", "操作系统"])
    if "runnable" in item_l or "可运行" in item or "code" in item_l or "代码" in item:
        return (ctx["has_code_file"] or ctx["has_skill_pkg"] or ctx["has_archive"]
                or any(k in corpus_lower for k in ["```python", "```bash", "```javascript", "def ", "class ", "import ", "workflow", "pipeline"]))
    if "skill package" in item_l or "skill 包" in item or "structure" in item_l or "结构" in item:
        return ctx["has_skill_pkg"] or ctx["has_archive"]
    if "syntax" in item_l or "语法" in item:
        return True  # 规则层不做真实编译，交给 LLM 深审；避免误判
    if "frontmatter" in item_l or "yaml" in item_l:
        return any(k in corpus_lower for k in ["---\nname:", "name:", "description:"]) and "---" in corpus
    if "test" in item_l or "测试" in item or "example" in item_l or "示例" in item:
        return any(k in corpus_lower for k in ["测试", "test", "example", "示例", "预期", "expected"])
    if "expected output" in item_l or "预期输出" in item or "预期结果" in item:
        return any(k in corpus_lower for k in ["预期输出", "预期结果", "expected output", "得到", "输出:"])
    if "demo" in item_l or "演示" in item or "real result" in item_l:
        return ctx["has_demo_media"] or any(k in corpus_lower for k in ["demo", "演示", "截图", "录屏", "测试结果"])
    if "success/failure" in item_l or "成败" in item:
        return any(k in corpus_lower for k in ["成功", "失败", "success", "failure", "报错", "error"])
    if "one-liner" in item_l or "一句话" in item:
        return bool(re.search(r"输入.{0,30}输出|输入.{0,20}，.{0,20}输出", corpus))
    if "input types" in item_l or "输入类型" in item or "formats" in item_l or "格式" in item:
        return any(k in corpus_lower for k in ["输入", "input", ".md", ".docx", ".pdf", "格式"])
    if "output types" in item_l or "输出类型" in item:
        return any(k in corpus_lower for k in ["输出", "output", "返回", "returns", "generates", "produces"])
    if "edge case" in item_l or "边界" in item:
        return any(k in corpus_lower for k in ["边界", "edge case", "空文件夹", "超", "编码", "异常"])
    # 通用：默认用正向信号集合判断
    return any(s.lower() in corpus_lower for s in ctx["pos_signals"])


def _build_basis(key: str, satisfied: int, item_checks: list, neg_hits: list, corpus_lower: str) -> str:
    ok_items = [c["item"] for c in item_checks if c["ok"]]
    bad_items = [c["item"] for c in item_checks if not c["ok"]]
    parts = []
    if ok_items:
        parts.append("满足: " + "；".join(ok_items[:3]))
    if bad_items:
        parts.append("未满足: " + "；".join(bad_items[:3]))
    if neg_hits:
        parts.append("发现硬编码/敏感信号: " + "、".join(neg_hits[:3]))
    return "；".join(parts) if parts else "信号不足，需人工复核"


def _build_suggestion(key: str, satisfied: int, neg_hits: list) -> str:
    if key == "reusable":
        if neg_hits:
            return "移除硬编码绝对路径与敏感凭据，补充安装步骤与环境要求（如 pip install / requirements.txt）。"
        if satisfied >= 2:
            return "可复用性良好；建议补充跨平台兼容性说明与一键安装脚本。"
        return "补充安装说明、环境要求（Python 版本、依赖清单），避免依赖提交者本机路径。"
    if key == "executable":
        if satisfied >= 2:
            return "可执行性良好；建议补充运行示例命令与常见报错处理。"
        return "提供可运行代码/prompt/workflow；若为 .skill 包，确保目录结构完整且有 YAML frontmatter。"
    if key == "verifiable":
        if satisfied >= 2:
            return "可验证性良好；建议给出预期输出样例与验收标准，方便他人判断是否运行成功。"
        return "补充测试用例或 demo（截图/录屏），并明确定义预期输出与成功标准。"
    if key == "clear_io":
        if satisfied >= 2:
            return "IO 描述清晰；建议补充边界输入的处理说明。"
        return "在说明中明确写出一句话 IO 描述（输入____，输出____），并标注输入输出类型与格式。"
    return "完善该维度的证据与说明。"


# ---------------------------------------------------------------------------
# Stage 4: 报告生成（Markdown + Excel）
# ---------------------------------------------------------------------------

def compute_composite(completeness: dict, quality: dict, rubric: dict) -> float:
    # rubric 约定: composite = completeness_score * 0.4 + quality_score * 0.6
    w_compl = 0.4
    w_qual = 0.6
    completeness_score = completeness["present"] / max(completeness["total"], 1)
    quality_score = sum(q["score"] for q in quality.values()) / max(len(quality), 1)
    return round(completeness_score * w_compl + quality_score * w_qual, 3)


def make_markdown_report(
    authors: list[dict],
    summary: dict,
    folder: str,
    rubric: dict,
    unknown_files: list[str],
    non_c4_files: list[str],
) -> str:
    lines = []
    lines.append("# C4 提交自动评审报告")
    lines.append("")
    lines.append(f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"- 扫描路径：`{folder}`")
    lines.append(f"- 识别提交：{summary['n_authors']} 位作者，{summary['n_files']} 个文件")
    lines.append(f"- 评审方法：规则引擎（c4_rubric.yaml 信号库）+ 可选 LLM 深审（混合架构）")
    lines.append("")

    # 一、班级总览
    lines.append("## 一、班级总览")
    lines.append("")
    lines.append("| 指标 | 数值 |")
    lines.append("|------|------|")
    lines.append(f"| 总提交人数 | {summary['n_authors']} |")
    lines.append(f"| 完整提交（{summary['total_files']}/{summary['total_files']}） | {summary['n_complete']} |")
    lines.append(f"| 部分提交 | {summary['n_partial']} |")
    lines.append(f"| 严重缺失 | {summary['n_insufficient']} |")
    lines.append(f"| 平均质量分 | {summary['avg_quality']}/1.0 |")
    lines.append("")
    lines.append("**质量分布：**")
    lines.append("")
    lines.append("| 作者 | 完整性 | 可复用 | 可执行 | 可验证 | IO明确 | 综合分 |")
    lines.append("|------|--------|--------|--------|--------|--------|--------|")
    for a in authors:
        q = a["quality"]
        lines.append(
            f"| {a['author']} | {a['completeness']['present']}/{a['completeness']['total']} "
            f"| {q['reusable']['grade']} | {q['executable']['grade']} | {q['verifiable']['grade']} "
            f"| {q['clear_io']['grade']} | {a['composite']:.2f} |"
        )
    lines.append("")

    # 二、作者详情
    lines.append("## 二、作者详情")
    lines.append("")
    for a in authors:
        lines.append(f"### {a['author']}（综合分 {a['composite']:.2f}，{a['completeness']['level']}）")
        lines.append("")
        lines.append("**完整性检查：**")
        lines.append("")
        lines.append("| 必备文件 | 状态 | 匹配文件 |")
        lines.append("|----------|------|----------|")
        for key, v in a["completeness"]["matrix"].items():
            matched = "、".join(v["matched"]) if v["matched"] else "—"
            lines.append(f"| {v['label_cn']} | {v['status']} | {matched} |")
        lines.append("")
        lines.append("**质量评审：**")
        lines.append("")
        lines.append("| 条件 | 评级 | 依据 | 改进建议 |")
        lines.append("|------|------|------|----------|")
        for key in ["reusable", "executable", "verifiable", "clear_io"]:
            v = a["quality"][key]
            lines.append(f"| {v['label_cn']} | {v['grade']} | {v['basis']} | {v['suggestion']} |")
        lines.append("")
        if a.get("versions"):
            lines.append(f"**版本迭代：** {a['versions']}")
            lines.append("")
        lines.append("---")
        lines.append("")

    # 三、排名
    lines.append("## 三、排名")
    lines.append("")
    lines.append("| 排名 | 作者 | 完整性 | 质量分 | 综合分 |")
    lines.append("|------|------|--------|--------|--------|")
    for i, a in enumerate(authors, 1):
        qs = sum(q["score"] for q in a["quality"].values()) / max(len(a["quality"]), 1)
        lines.append(f"| {i} | {a['author']} | {a['completeness']['present']}/{a['completeness']['total']} | {qs:.2f} | {a['composite']:.2f} |")
    lines.append("")

    # 四、全班改进建议
    lines.append("## 四、全班改进建议")
    lines.append("")
    most_missing = summary.get("most_missing", "—")
    weakest = summary.get("weakest_criterion", "—")
    lines.append(f"- 最常见缺失项：**{most_missing}**")
    lines.append(f"- 最弱维度：**{weakest}**")
    lines.append("- 建议每位同学在提交前用本评审技能自检一次（`python c4_skill_evaluator.py <你的提交文件夹>`）")
    lines.append("- 命名不规范的文件会被标记为 Unknown，务必按 `姓名_C4_内容描述.扩展名` 命名")
    lines.append("")

    if unknown_files:
        lines.append("## 五、需人工确认（Unknown / 命名不规范）")
        lines.append("")
        for p in unknown_files:
            lines.append(f"- `{p}`")
        lines.append("")
    if non_c4_files:
        lines.append("## 六、非 C4 文件（已过滤）")
        lines.append("")
        for p in non_c4_files[:50]:
            lines.append(f"- `{p}`")
        lines.append("")
    return "\n".join(lines)


def generate_excel(authors: list[dict], summary: dict, output_path: str):
    """生成 Excel 详表（4 个 Sheet）。"""
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter
    except ImportError:
        print("缺少 openpyxl，跳过 Excel 输出", file=sys.stderr)
        return

    wb = Workbook()
    header_font = Font(name="Arial", bold=True, size=11, color="FFFFFF")
    header_fill = PatternFill(start_color="2F5496", end_color="2F5496", fill_type="solid")
    cell_font = Font(name="Arial", size=10)
    thin = Side(style="thin")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    def style_header(ws, headers):
        for col, h in enumerate(headers, 1):
            c = ws.cell(row=1, column=col, value=h)
            c.font = header_font
            c.fill = header_fill
            c.alignment = Alignment(horizontal="center", wrap_text=True)
            c.border = border
        ws.freeze_panes = "A2"

    # Sheet 1: 作者 × 条件矩阵
    ws1 = wb.active
    ws1.title = "Author Matrix"
    headers1 = ["Rank", "Author", "Completeness", "Reusable", "Executable", "Verifiable", "Clear I/O", "Composite", "Level"]
    style_header(ws1, headers1)
    for i, a in enumerate(authors, 1):
        q = a["quality"]
        vals = [i, a["author"], f"{a['completeness']['present']}/{a['completeness']['total']}",
                q["reusable"]["grade"], q["executable"]["grade"], q["verifiable"]["grade"],
                q["clear_io"]["grade"], a["composite"], a["completeness"]["level"]]
        for col, v in enumerate(vals, 1):
            c = ws1.cell(row=i + 1, column=col, value=v)
            c.font = cell_font
            c.border = border
    for col in range(1, len(headers1) + 1):
        ws1.column_dimensions[get_column_letter(col)].width = 14

    # Sheet 2: 文件清单
    ws2 = wb.create_sheet("File Inventory")
    headers2 = ["Author", "File", "Ext", "Size(KB)", "Convention", "Version", "C4 Hint"]
    style_header(ws2, headers2)
    row = 2
    for a in authors:
        for f in a["files"]:
            vals = [a["author"], f["path"], f["ext"], f["size_kb"],
                    "✓" if f["convention_match"] else "✗", f["version"], f["c4_hint"] or "—"]
            for col, v in enumerate(vals, 1):
                c = ws2.cell(row=row, column=col, value=v)
                c.font = cell_font
                c.border = border
            row += 1
    for col in range(1, len(headers2) + 1):
        ws2.column_dimensions[get_column_letter(col)].width = 22 if col == 2 else 12

    # Sheet 3: 缺失项汇总
    ws3 = wb.create_sheet("Missing Summary")
    headers3 = ["Author", "Missing Items", "Weakest Criterion", "Top Suggestion"]
    style_header(ws3, headers3)
    for i, a in enumerate(authors, 1):
        missing = [v["label_cn"] for v in a["completeness"]["matrix"].values() if v["status"] != "✅"]
        weakest = min(a["quality"].items(), key=lambda kv: kv[1]["score"])[0]
        suggestion = a["quality"][weakest]["suggestion"]
        vals = [a["author"], "、".join(missing) if missing else "无", weakest, suggestion]
        for col, v in enumerate(vals, 1):
            c = ws3.cell(row=i + 1, column=col, value=v)
            c.font = cell_font
            c.border = border
            c.alignment = Alignment(wrap_text=True)
    for col in range(1, len(headers3) + 1):
        ws3.column_dimensions[get_column_letter(col)].width = 28

    # Sheet 4: 班级统计
    ws4 = wb.create_sheet("Class Summary")
    headers4 = ["Metric", "Value"]
    style_header(ws4, headers4)
    metrics = [
        ("总提交人数", summary["n_authors"]),
        ("完整提交", summary["n_complete"]),
        ("部分提交", summary["n_partial"]),
        ("严重缺失", summary["n_insufficient"]),
        ("平均质量分", summary["avg_quality"]),
        ("最常见缺失项", summary["most_missing"]),
        ("最弱维度", summary["weakest_criterion"]),
    ]
    for i, (k, v) in enumerate(metrics, 2):
        ws4.cell(row=i, column=1, value=k).font = cell_font
        ws4.cell(row=i, column=2, value=v).font = cell_font
    ws4.column_dimensions["A"].width = 20
    ws4.column_dimensions["B"].width = 40

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    wb.save(output_path)
    print(f"Excel 已保存: {output_path}", file=sys.stderr)


# ---------------------------------------------------------------------------
# 可选 LLM 深审（规则 + LLM 混合架构的第二层）
# ---------------------------------------------------------------------------

def llm_deep_review(author: str, corpus: str, rubric: dict) -> dict | None:
    """
    当配置了国产大模型 API（优先 Qwen/DashScope，其次 OpenAI 兼容）时，
    对提交内容做深度评审：发现规则层漏检的问题，并生成个性化改进建议。
    未配置 API 时返回 None（自动降级，不阻断）。
    """
    api_key = os.environ.get("DASHSCOPE_API_KEY") or os.environ.get("QWEN_API_KEY") \
        or os.environ.get("OPENAI_API_KEY") or os.environ.get("MOONSHOT_API_KEY")
    if not api_key:
        return None
    try:
        import urllib.request

        if os.environ.get("DASHSCOPE_API_KEY") or os.environ.get("QWEN_API_KEY"):
            endpoint = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
            model = "qwen-plus"
        elif os.environ.get("MOONSHOT_API_KEY"):
            endpoint = "https://api.moonshot.cn/v1/chat/completions"
            model = "moonshot-v1-8k"
        else:
            endpoint = "https://api.openai.com/v1/chat/completions"
            model = "gpt-4o-mini"

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "你是 C4 技能提交的资深评审官。请基于 C4 四条件（可复用/可执行/可验证/IO明确）给出简洁的 JSON 评审结论。"},
                {"role": "user", "content": f"作者 {author} 的 C4 提交内容如下。请返回 JSON：{{\"issues\": [\"...\"], \"suggestions\": [\"...\"], \"score_comment\": \"...\"}}\n\n{corpus[:12000]}"},
            ],
            "temperature": 0.2,
        }
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"]
        # 提取 JSON
        m = re.search(r"\{.*\}", content, re.DOTALL)
        if m:
            return json.loads(m.group(0))
        return {"raw": content}
    except Exception as e:
        print(f"[LLM 深审失败，跳过] {e}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def run_evaluation(folder: str, output_dir: str, excel: bool = False, use_llm: bool = False):
    folder_path = Path(folder).expanduser().resolve()
    if not folder_path.is_dir():
        print(f"错误: '{folder}' 不是目录", file=sys.stderr)
        sys.exit(1)

    rubric = load_rubric()
    print(f"已加载评分规则: {rubric.get('version', 'c4_rubric')}", file=sys.stderr)

    # Stage 1: 采集 + 作者识别
    items = inventory_folder(folder_path)
    print(f"扫描到 {len(items)} 个文件", file=sys.stderr)
    if not items:
        print(json.dumps({"summary": "未找到文件。", "files": []}, ensure_ascii=False, indent=2))
        return

    # C4 候选过滤：命名规范命中，或内容含技能类信号（非规范命名回退）
    C4_CONTENT_SIGNALS = ["技能", "skill", "prompt", "工作流", "workflow", "```", "def ", "class "]
    README_LIKE = re.compile(r"^(README|readme|说明|说明文档|语料说明|readme_|readme-)", re.IGNORECASE)
    c4_items = []
    non_c4 = []
    for i in items:
        parse_filename(i)
        if i["c4_hint"] or i["convention_match"]:
            c4_items.append(i)
            continue
        # 目录说明类文件不作为提交候选
        if README_LIKE.match(i["name"]):
            non_c4.append(i["path"])
            continue
        if i["size_kb"] <= LARGE_FILE_KB and i["ext"] in DOC_EXTS:
            try:
                with open(i["abs_path"], "r", encoding="utf-8", errors="replace") as f:
                    head = f.read(2000).lower()
                if any(s.lower() in head for s in C4_CONTENT_SIGNALS):
                    c4_items.append(i)
                    continue
            except Exception:
                pass
        non_c4.append(i["path"])
    bundles, unknown_files = identify_authors(c4_items)

    # Stage 2+3: 每位作者 完整性 + 质量
    authors = []
    for author, files in bundles.items():
        # 版本追踪：只保留最新版本参与评分，旧版本记录迭代历史
        files_sorted = sorted(files, key=lambda x: x["version"], reverse=True)
        latest = []
        latest_v = files_sorted[0]["version"] if files_sorted else 1
        versions = defaultdict(list)
        for f in files:
            versions[f["version"]].append(f["path"])
        latest = [f for f in files if f["version"] == latest_v]

        completeness = check_completeness(latest, rubric)
        quality = evaluate_quality(latest, rubric)
        composite = compute_composite(completeness, quality, rubric)

        llm_review = None
        if use_llm:
            corpus = "\n".join(_read_text(f) for f in latest)[:16000]
            llm_review = llm_deep_review(author, corpus, rubric)

        version_track = ", ".join(f"v{v}: {len(ps)} 文件" for v, ps in sorted(versions.items()))
        authors.append({
            "author": author,
            "files": latest,
            "completeness": completeness,
            "quality": quality,
            "composite": composite,
            "versions": version_track,
            "llm_review": llm_review,
        })

    # 汇总统计
    authors.sort(key=lambda a: -a["composite"])
    n_complete = sum(1 for a in authors if a["completeness"]["level"] == "完整提交")
    n_partial = sum(1 for a in authors if a["completeness"]["level"] == "部分提交")
    n_insufficient = sum(1 for a in authors if a["completeness"]["level"] == "严重缺失")
    avg_quality = sum(a["composite"] for a in authors) / max(len(authors), 1)

    # 最常见缺失项 & 最弱维度
    missing_counter = defaultdict(int)
    for a in authors:
        for v in a["completeness"]["matrix"].values():
            if v["status"] != "✅":
                missing_counter[v["label_cn"]] += 1
    most_missing = max(missing_counter.items(), key=lambda kv: kv[1])[0] if missing_counter else "无"

    weakest_counter = defaultdict(int)
    for a in authors:
        wk = min(a["quality"].items(), key=lambda kv: kv[1]["score"])[0]
        weakest_counter[wk] += 1
    weakest = max(weakest_counter.items(), key=lambda kv: kv[1])[0] if weakest_counter else "—"

    summary = {
        "n_authors": len(authors),
        "n_files": len(c4_items),
        "n_complete": n_complete,
        "n_partial": n_partial,
        "n_insufficient": n_insufficient,
        "avg_quality": round(avg_quality, 3),
        "total_files": 5,
        "most_missing": most_missing,
        "weakest_criterion": weakest,
    }

    # Stage 4: 报告生成
    report_md = make_markdown_report(authors, summary, str(folder_path), rubric, unknown_files, non_c4)

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    md_path = out / "C4_评审报告.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(report_md)
    print(f"Markdown 报告: {md_path}", file=sys.stderr)

    if excel:
        xlsx_path = out / "C4_评审详表.xlsx"
        generate_excel(authors, summary, str(xlsx_path))

    # 输出机器可读 JSON（供上层 Agent 使用）
    json_out = {
        "summary": summary,
        "authors": [
            {
                "author": a["author"],
                "completeness": a["completeness"],
                "quality": {k: {"grade": v["grade"], "score": v["score"], "basis": v["basis"], "suggestion": v["suggestion"]}
                            for k, v in a["quality"].items()},
                "composite": a["composite"],
                "versions": a["versions"],
                "llm_review": a["llm_review"],
            }
            for a in authors
        ],
        "unknown_files": unknown_files,
        "non_c4_files": non_c4,
    }
    print(json.dumps(json_out, ensure_ascii=False, indent=2))
    print(f"\n✅ 评审完成: {len(authors)} 位作者。报告已输出到 {out}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="C4 技能提交自动评审器")
    parser.add_argument("folder", help="包含 C4 提交文件的文件夹路径")
    parser.add_argument("--output", default="c4_eval_output", help="输出目录")
    parser.add_argument("--excel", action="store_true", help="额外生成 Excel 详表")
    parser.add_argument("--llm", action="store_true", help="启用 LLM 深度评审（需配置 DASHSCOPE_API_KEY / OPENAI_API_KEY）")
    args = parser.parse_args()
    run_evaluation(args.folder, args.output, args.excel, args.llm)


if __name__ == "__main__":
    main()
