#!/usr/bin/env python3
"""数据整理技能：清洗 Excel 数据，输出汇总表"""

import csv
from collections import Counter


def clean_and_summarize(input_csv: str, output_csv: str):
    """去除空行与重复行，统计分类计数"""
    rows = list(csv.reader(open(input_csv, encoding="utf-8")))
    seen = set()
    out = []
    for r in rows:
        key = tuple(r)
        if key and key not in seen:
            seen.add(key)
            out.append(r)
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(out)
    return len(out)
