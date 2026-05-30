#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 JSON 文件生成周报
读取 extract_commits.py 导出的 JSON 文件，生成周报
"""

import os
import sys
import json
import argparse
from datetime import datetime


def load_commits_from_json(json_path: str) -> dict:
    """从 JSON 文件加载 Commit 数据"""
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def classify_commits(commits: list) -> dict:
    """对 Commit 进行分类"""
    
    CATEGORY_KEYWORDS = {
        "plan": ["plan", "计划", "安排", "规划", "下一步", "下周", "待办", "todo"],
        "risk": ["bug", "error", "异常", "问题", "阻塞", "风险", "issue", "故障", "超时"],
        "in_progress": ["wip", "进行中", "开发中", "处理中", "in progress", "ongoing"],
        "completed": ["feat", "feature", "add", "fix", "修复", "解决", "新增", "添加", "实现", "完成", "优化", "refactor", "改进", "提升", "部署", "上线", "release", "merge"],
    }
    
    TYPE_LABELS = {
        "feat": "✨ 新功能", "feature": "✨ 新功能", "add": "✨ 新功能",
        "新增": "✨ 新功能", "添加": "✨ 新功能", "实现": "✨ 新功能",
        "fix": "🐛 Bug修复", "bug": "🐛 Bug修复", "修复": "🐛 Bug修复", "解决": "🐛 Bug修复",
        "refactor": "♻️ 重构", "重构": "♻️ 重构",
        "优化": "⚡ 优化", "optimize": "⚡ 优化", "改进": "⚡ 优化", "提升": "⚡ 优化",
        "docs": "📝 文档", "文档": "📝 文档",
        "test": "🧪 测试", "测试": "🧪 测试",
        "config": "⚙️ 配置", "配置": "⚙️ 配置",
        "deploy": "🚀 部署", "部署": "🚀 部署", "上线": "📦 发布",
        "merge": "🔀 合并",
    }
    
    classified = {
        "completed": [],
        "plan": [],
        "risk": [],
        "in_progress": [],
        "other": [],
    }
    
    for commit in commits:
        msg = commit["message"].lower()
        categorized = False
        
        # 精确匹配
        exact_patterns = {
            "plan": [r"^plan[\s:]", r"^计划[\s:]", r"^下周[\s:]"],
            "in_progress": [r"^wip[\s:]", r"^进行中[\s:]"],
        }
        import re
        for category, patterns in exact_patterns.items():
            for pattern in patterns:
                if re.match(pattern, msg.strip()):
                    classified[category].append(commit)
                    categorized = True
                    break
            if categorized:
                break
        
        if not categorized:
            for category, keywords in CATEGORY_KEYWORDS.items():
                for keyword in keywords:
                    if keyword.lower() in msg:
                        classified[category].append(commit)
                        categorized = True
                        break
                if categorized:
                    break
        
        if not categorized:
            classified["other"].append(commit)
    
    return classified


def format_commit(commit: dict) -> str:
    """格式化 Commit 为可读描述"""
    msg = commit["message"].strip()
    
    import re
    TYPE_LABELS = {
        "feat": "✨ 新功能", "feature": "✨ 新功能", "add": "✨ 新功能",
        "新增": "✨ 新功能", "添加": "✨ 新功能", "实现": "✨ 新功能",
        "fix": "🐛 Bug修复", "bug": "🐛 Bug修复", "修复": "🐛 Bug修复", "解决": "🐛 Bug修复",
        "refactor": "♻️ 重构", "重构": "♻️ 重构",
        "优化": "⚡ 优化", "optimize": "⚡ 优化", "改进": "⚡ 优化", "提升": "⚡ 优化",
    }
    
    # 尝试提取 Conventional Commits 格式
    match = re.match(r'^(\w+)(\([^)]+\))?\s*:\s*(.+)$', msg)
    if match:
        commit_type = match.group(1).lower()
        subject = match.group(3).strip()
        label = TYPE_LABELS.get(commit_type, "")
        if label:
            return f"{label}：{subject}"
        return subject
    
    # 尝试提取 Jira 任务编号
    match = re.match(r'^\[([A-Z]+-\d+)\]\s*(.+)$', msg)
    if match:
        ticket = match.group(1)
        subject = match.group(2).strip()
        return f"[{ticket}] {subject}"
    
    return msg


def generate_report(data: dict, name: str, template: str = "wechat_work") -> str:
    """生成周报"""
    
    commits = data["commits"]
    since = data.get("since", "")[:10]
    until = data.get("until", "")[:10]
    report_type = data.get("report_type", "周报")
    type_names = {"daily": "日报", "weekly": "周报", "monthly": "月报"}
    type_name = type_names.get(report_type, "周报")
    
    classified = classify_commits(commits)
    
    # 统计
    stats = {
        "commit_count": len(commits),
        "added_lines": sum(c["added_lines"] for c in commits),
        "removed_lines": sum(c["removed_lines"] for c in commits),
        "changed_files": sum(c["files_changed"] for c in commits),
        "active_days": len(set(c["date"] for c in commits)),
    }
    
    lines = []
    
    if template == "wechat_work":
        # 企业微信模板
        lines.append(f"# {type_name}")
        lines.append("")
        lines.append(f"**姓名**：{name}")
        lines.append(f"**日期范围**：{since} ~ {until}")
        lines.append("")
        
        # 本周工作总结
        lines.append("## 本周工作总结")
        lines.append("")
        items = [format_commit(c) for c in classified["completed"]] or [format_commit(c) for c in classified["other"]]
        if items:
            for item in items:
                lines.append(f"- {item}")
        else:
            lines.append("暂无")
        lines.append("")
        
        # 下周工作规划
        lines.append("## 下周工作规划")
        lines.append("")
        if classified["plan"]:
            for item in [format_commit(c) for c in classified["plan"]]:
                lines.append(f"- {item}")
        else:
            lines.append("待补充")
        lines.append("")
        
        # 其他事项
        lines.append("## 其他事项")
        lines.append("")
        other_items = [format_commit(c) for c in classified["risk"]] + [format_commit(c) for c in classified["in_progress"]]
        if other_items:
            for item in other_items:
                lines.append(f"- {item}")
        else:
            lines.append("暂无")
        lines.append("")
        
    elif template == "dingtalk":
        # 钉钉模板
        lines.append(f"# {type_name}")
        lines.append("")
        lines.append(f"**姓名**：{name}")
        lines.append(f"**日期范围**：{since} ~ {until}")
        lines.append("")
        
        # 本周完成工作
        lines.append("## 本周完成工作")
        lines.append("")
        items = [format_commit(c) for c in classified["completed"]] or [format_commit(c) for c in classified["other"]]
        if items:
            for item in items:
                lines.append(f"- {item}")
        else:
            lines.append("暂无")
        lines.append("")
        
        # 下周工作计划
        lines.append("## 下周工作计划")
        lines.append("")
        if classified["plan"]:
            for item in [format_commit(c) for c in classified["plan"]]:
                lines.append(f"- {item}")
        else:
            lines.append("待补充")
        lines.append("")
        
        # 本周工作总结
        lines.append("## 本周工作总结")
        lines.append("")
        lines.append(f"本周共完成 {len(classified['completed'])} 项工作。")
        lines.append("")
        
    else:
        # 通用模板
        lines.append(f"# 工作{type_name}")
        lines.append("")
        lines.append(f"**姓名**：{name}")
        lines.append(f"**日期范围**：{since} ~ {until}")
        lines.append("")
        
        lines.append("## 一、完成事项")
        lines.append("")
        items = [format_commit(c) for c in classified["completed"]] or [format_commit(c) for c in classified["other"]]
        if items:
            for item in items:
                lines.append(f"- {item}")
        else:
            lines.append("暂无")
        lines.append("")
        
        lines.append("## 二、数据统计")
        lines.append("")
        lines.append("| 指标 | 数值 |")
        lines.append("|---|---|")
        lines.append(f"| 提交次数 | {stats['commit_count']} |")
        lines.append(f"| 新增行数 | +{stats['added_lines']} |")
        lines.append(f"| 删除行数 | -{stats['removed_lines']} |")
        lines.append(f"| 修改文件数 | {stats['changed_files']} |")
        if report_type == "weekly":
            lines.append(f"| 活跃天数 | {stats['active_days']} |")
        lines.append("")
        
        lines.append("## 三、工作计划")
        lines.append("")
        if classified["plan"]:
            for item in [format_commit(c) for c in classified["plan"]]:
                lines.append(f"- {item}")
        else:
            lines.append("待补充")
        lines.append("")
        
        lines.append("## 四、风险与问题")
        lines.append("")
        if classified["risk"]:
            for item in [format_commit(c) for c in classified["risk"]]:
                lines.append(f"- {item}")
        else:
            lines.append("暂无")
        lines.append("")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="从 JSON 文件生成周报")
    parser.add_argument("input", help="输入的 JSON 文件路径")
    parser.add_argument("--name", "-n", default="", help="报告人姓名")
    parser.add_argument("--template", "-t", choices=["wechat_work", "dingtalk", "default"], 
                        default="wechat_work", help="模板类型（默认: wechat_work）")
    parser.add_argument("--output", "-o", default="", help="输出文件路径")

    args = parser.parse_args()

    # 加载数据
    data = load_commits_from_json(args.input)
    
    # 确定姓名
    name = args.name
    if not name and data.get("authors"):
        name = "/".join(data["authors"])
    if not name:
        name = "未知"
    
    # 生成报告
    report = generate_report(data, name, args.template)
    
    # 输出
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"报告已保存到: {args.output}")
    else:
        print("=" * 50)
        print("  周报预览")
        print("=" * 50)
        print(report)
        print("=" * 50)


if __name__ == "__main__":
    main()
