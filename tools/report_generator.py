#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
周报/日报自动生成工具
根据 Git Commit 记录自动生成结构化的工作汇报
支持用户自定义模板，智能匹配模板标题并填充内容
"""

import os
import re
import sys
import argparse
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


# ============================================================
# 数据模型
# ============================================================

@dataclass
class CommitInfo:
    """Git Commit 信息"""
    hash: str
    date: str
    author: str
    message: str
    added_lines: int = 0
    removed_lines: int = 0
    files_changed: int = 0
    category: str = ""  # 自动分类结果


@dataclass
class ReportData:
    """报告数据 - 支持多种模板格式（通用、企业微信、钉钉、飞书）"""
    commits: list = field(default_factory=list)
    completed_items: list = field(default_factory=list)      # 完成事项 / 工作总结
    plan_items: list = field(default_factory=list)           # 计划 / 规划
    risk_items: list = field(default_factory=list)           # 风险 / 问题 / 需协调
    in_progress_items: list = field(default_factory=list)    # 进行中 / 未完成
    other_items: list = field(default_factory=list)          # 其他事项
    summary_items: list = field(default_factory=list)        # 工作总结（钉钉特有）
    stats: dict = field(default_factory=dict)


# ============================================================
# Git Commit 提取
# ============================================================

class GitExtractor:
    """从 Git 仓库提取 Commit 信息"""

    def __init__(self, repo_path: str, author: str = ""):
        self.repo_path = os.path.abspath(repo_path)
        self.author = author

    def _run_git(self, args: list) -> str:
        """执行 Git 命令"""
        cmd = ["git", "-C", self.repo_path] + args
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"[错误] Git 命令执行失败: {e.stderr}")
            return ""

    def get_commits(self, since: str, until: str = "") -> list:
        """获取指定时间范围内的 Commit 列表"""
        args = [
            "log",
            f"--since={since}",
            "--pretty=format:%H|%ad|%an|%s",
            "--date=short",
            "--numstat",
        ]
        if until:
            args.append(f"--until={until}")
        if self.author:
            args.append(f"--author={self.author}")

        output = self._run_git(args)
        if not output:
            return []

        commits = []
        current_commit = None
        added = 0
        removed = 0
        files = 0

        for line in output.split("\n"):
            if not line.strip():
                continue

            # 检测是否是 Commit 信息行（格式：hash|date|author|message）
            if re.match(r'^[a-f0-9]+\|', line):
                # 保存上一个 Commit
                if current_commit:
                    current_commit.added_lines = added
                    current_commit.removed_lines = removed
                    current_commit.files_changed = files
                    commits.append(current_commit)

                parts = line.split("|", 3)
                current_commit = CommitInfo(
                    hash=parts[0],
                    date=parts[1],
                    author=parts[2],
                    message=parts[3] if len(parts) > 3 else "",
                )
                added = 0
                removed = 0
                files = 0
            else:
                # numstat 行：added\tremoved\tfilename
                parts = line.split("\t")
                if len(parts) >= 3:
                    try:
                        a = int(parts[0]) if parts[0] != "-" else 0
                        r = int(parts[1]) if parts[1] != "-" else 0
                        added += a
                        removed += r
                        files += 1
                    except ValueError:
                        pass

        # 保存最后一个 Commit
        if current_commit:
            current_commit.added_lines = added
            current_commit.removed_lines = removed
            current_commit.files_changed = files
            commits.append(current_commit)

        return commits


# ============================================================
# 内容智能分类
# ============================================================

class CommitClassifier:
    """将 Commit 智能分类到不同模块"""

    # 分类关键词映射（顺序决定优先级，更具体的分类放前面）
    CATEGORY_KEYWORDS = {
        "plan": [
            "plan", "计划", "安排", "规划", "下一步", "下周",
            "待办", "todo", "准备", "预备",
        ],
        "risk": [
            "bug", "error", "异常", "问题", "阻塞", "阻碍",
            "风险", "risk", "issue", "block", "fail", "crash",
            "故障", "宕机", "超时", "timeout",
        ],
        "in_progress": [
            "wip", "进行中", "开发中", "处理中", "in progress",
            "ongoing", "working on", "draft",
        ],
        "completed": [
            "feat", "feature", "add", "fix", "修复", "解决",
            "新增", "添加", "实现", "完成", "优化", "refactor",
            "改进", "提升", "部署", "上线", "release", "merge",
        ],
    }

    # Commit 类型标签（用于美化显示）
    TYPE_LABELS = {
        "feat": "✨ 新功能",
        "feature": "✨ 新功能",
        "add": "✨ 新功能",
        "新增": "✨ 新功能",
        "添加": "✨ 新功能",
        "实现": "✨ 新功能",
        "fix": "🐛 Bug修复",
        "bug": "🐛 Bug修复",
        "修复": "🐛 Bug修复",
        "解决": "🐛 Bug修复",
        "refactor": "♻️ 重构",
        "重构": "♻️ 重构",
        "优化": "⚡ 优化",
        "optimize": "⚡ 优化",
        "改进": "⚡ 优化",
        "提升": "⚡ 优化",
        "docs": "📝 文档",
        "doc": "📝 文档",
        "文档": "📝 文档",
        "test": "🧪 测试",
        "测试": "🧪 测试",
        "config": "⚙️ 配置",
        "配置": "⚙️ 配置",
        "deploy": "🚀 部署",
        "部署": "🚀 部署",
        "release": "📦 发布",
        "上线": "📦 发布",
        "merge": "🔀 合并",
        "revert": "⏪ 回滚",
        "回滚": "⏪ 回滚",
    }

    def classify(self, commit: CommitInfo) -> str:
        """对单个 Commit 进行分类（使用精确匹配优先策略）"""
        msg = commit.message.lower()
        msg_stripped = msg.strip()

        # 精确匹配：Commit 以特定关键词开头
        exact_patterns = {
            "plan": [r"^plan[\s:：]", r"^计划[\s:：]", r"^下周[\s:：]", r"^待办[\s:：]"],
            "in_progress": [r"^wip[\s:：]", r"^进行中[\s:：]", r"^开发中[\s:：]"],
        }
        for category, patterns in exact_patterns.items():
            for pattern in patterns:
                if re.match(pattern, msg_stripped):
                    commit.category = category
                    return category

        # 包含匹配：按优先级顺序检查
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in msg:
                    commit.category = category
                    return category

        commit.category = "other"
        return "other"

    def classify_all(self, commits: list) -> ReportData:
        """对所有 Commit 进行分类并生成报告数据"""
        report = ReportData()

        for commit in commits:
            self.classify(commit)
            report.commits.append(commit)

            # 过滤无意义的 Commit
            if self._is_trivial(commit.message):
                continue

            formatted = self._format_commit(commit)

            if commit.category == "completed":
                report.completed_items.append(formatted)
            elif commit.category == "plan":
                report.plan_items.append(formatted)
            elif commit.category == "risk":
                report.risk_items.append(formatted)
            elif commit.category == "in_progress":
                report.in_progress_items.append(formatted)
            else:
                report.other_items.append(formatted)

        # 计算统计数据
        report.stats = self._calc_stats(commits)

        return report

    def _is_trivial(self, message: str) -> bool:
        """判断是否为无意义的 Commit"""
        trivial_patterns = [
            r'^merge\s',
            r'^merge\s',
            r'^update\s*README',
            r'^initial\s*commit',
            r'^wip$',
            r'^\.$',
            r'^update$',
            r'^fix$',
            r'^\s*$',
        ]
        msg = message.strip().lower()
        return any(re.match(p, msg) for p in trivial_patterns)

    def _format_commit(self, commit: CommitInfo) -> str:
        """格式化 Commit 为可读描述"""
        msg = commit.message.strip()

        # 尝试提取 Conventional Commits 格式
        match = re.match(r'^(\w+)(\([^)]+\))?\s*:\s*(.+)$', msg)
        if match:
            commit_type = match.group(1).lower()
            subject = match.group(3).strip()
            label = self.TYPE_LABELS.get(commit_type, "")
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

    def _calc_stats(self, commits: list) -> dict:
        """计算统计数据"""
        if not commits:
            return {
                "commit_count": 0,
                "added_lines": 0,
                "removed_lines": 0,
                "changed_files": 0,
                "active_days": 0,
            }

        total_added = sum(c.added_lines for c in commits)
        total_removed = sum(c.removed_lines for c in commits)
        total_files = sum(c.files_changed for c in commits)
        active_days = len(set(c.date for c in commits))

        return {
            "commit_count": len(commits),
            "added_lines": total_added,
            "removed_lines": total_removed,
            "changed_files": total_files,
            "active_days": active_days,
        }


# ============================================================
# 模板识别与填充
# ============================================================

class TemplateEngine:
    """模板识别与内容填充引擎"""

    # 标题与内容分类的映射关键词
    # 支持：通用模板、企业微信、钉钉、飞书等主流协作工具
    SECTION_MAPPING = {
        # 完成事项 / 工作总结
        "completed": [
            # 通用（注意：单独"事项"太宽泛，需要配合其他词）
            "完成", "进展", "进度", "成果", "产出",
            "done", "completed", "finish", "achievement",
            "本周工作", "今日工作", "工作内容", "工作总结",
            # 企业微信
            "今日工作总结", "本周工作总结", "工作总结",
            # 钉钉
            "今日完成工作", "本周完成工作", "完成工作",
            # 飞书
            "今日已完成", "本周已完成", "已完成工作",
        ],
        # 数据统计（可选模块）
        "stats": [
            "统计", "数据", "指标", "量化",
            "metrics", "statistics", "numbers", "数据统计",
            "工作量统计", "代码统计", "提交统计",
        ],
        # 计划 / 规划
        "plan": [
            # 通用
            "计划", "安排", "规划", "下一步", "下周", "明日",
            "plan", "next", "upcoming", "工作计划",
            # 企业微信
            "明日工作计划", "下周工作规划", "工作规划",
            # 钉钉
            "下周工作计划", "工作计划",
            # 飞书
            "明日计划", "下周计划",
        ],
        # 风险 / 问题 / 需协调
        "risk": [
            # 通用
            "风险", "问题", "困难", "阻碍", "阻塞",
            "risk", "issue", "block", "problem",
            "风险与问题", "问题与风险",
            # 钉钉
            "需协调工作", "协调工作", "待协调", "需支持",
            # 飞书
            "风险提示", "注意事项",
        ],
        # 其他事项（企业微信特有）
        "other": [
            "其他事项", "备注", "说明", "其他",
        ],
        # 未完成 / 进行中
        "in_progress": [
            "进行中", "开发中", "处理中",
            "wip", "in progress", "ongoing",
            # 钉钉
            "未完成工作", "未完成", "待完成",
            # 飞书
            "进行中工作", "待处理",
        ],
        # 总结（钉钉特有）
        "summary": [
            "本周工作总结", "工作总结", "总结",
            "工作反思", "复盘",
        ],
    }

    def __init__(self):
        self.template_content = ""
        self.sections = []  # [(title, section_type, start_line, end_line)]

    def load_template(self, template_path: str) -> bool:
        """加载模板文件"""
        path = Path(template_path)
        if not path.exists():
            print(f"[错误] 模板文件不存在: {template_path}")
            return False

        with open(path, "r", encoding="utf-8") as f:
            self.template_content = f.read()

        self._parse_sections()
        return True

    def _parse_sections(self):
        """解析模板结构，识别标题和分区"""
        lines = self.template_content.split("\n")
        self.sections = []

        # 标题正则匹配
        # 注意：只识别二级及以上标题（## 或更多#）作为内容分区
        # 一级标题（#）通常作为文档标题，不作为内容分区
        title_patterns = [
            r'^(#{2,6})\s+(.+)$',           # Markdown 标题（2-6级）
            r'^([一二三四五六七八九十]+[、.])\s*(.+)$',  # 中文数字编号
            r'^(\d+[.、])\s*(.+)$',          # 阿拉伯数字编号
        ]

        current_title = None
        current_type = None
        start_line = 0

        for i, line in enumerate(lines):
            matched = False
            for pattern in title_patterns:
                match = re.match(pattern, line)
                if match:
                    # 保存上一个分区
                    if current_title is not None:
                        self.sections.append({
                            "title": current_title,
                            "type": current_type,
                            "start": start_line,
                            "end": i - 1,
                        })

                    title_text = match.group(2).strip() if match.lastindex >= 2 else match.group(1).strip()
                    current_title = title_text
                    current_type = self._match_section_type(title_text)
                    start_line = i
                    matched = True
                    break

        # 保存最后一个分区
        if current_title is not None:
            self.sections.append({
                "title": current_title,
                "type": current_type,
                "start": start_line,
                "end": len(lines) - 1,
            })

    def _match_section_type(self, title: str) -> str:
        """根据标题关键词匹配内容分类（使用最长匹配优先策略）"""
        title_lower = title.lower()
        best_match = None
        best_match_len = 0

        for section_type, keywords in self.SECTION_MAPPING.items():
            for keyword in keywords:
                keyword_lower = keyword.lower()
                if keyword_lower in title_lower:
                    # 优先匹配更长的关键词
                    if len(keyword_lower) > best_match_len:
                        best_match = section_type
                        best_match_len = len(keyword_lower)

        return best_match if best_match else "other"

    def fill_template(self, report: ReportData, **variables) -> str:
        """填充模板内容"""
        if not self.template_content:
            return self._generate_default_report(report, **variables)

        lines = self.template_content.split("\n")
        result = []

        # 构建每个分区的填充内容
        section_contents = {
            "completed": self._build_completed_content(report),
            "stats": self._build_stats_content(report),
            "plan": self._build_plan_content(report),
            "risk": self._build_risk_content(report),
            "in_progress": self._build_in_progress_content(report),
            "summary": self._build_summary_content(report),
            "other": self._build_other_content(report),
        }

        # 替换变量占位符
        for line in lines:
            # 检查是否在某个分区内
            filled_line = line
            for var_name, var_value in variables.items():
                filled_line = filled_line.replace(f"{{{{{var_name}}}}}", str(var_value))

            result.append(filled_line)

        # 按分区填充内容
        filled_lines = self._fill_sections(lines, section_contents, **variables)
        return "\n".join(filled_lines)

    def _fill_sections(self, lines: list, section_contents: dict, **variables) -> list:
        """按分区填充内容"""
        result = []
        filled_sections = set()

        for i, line in enumerate(lines):
            # 替换变量占位符
            filled_line = line
            for var_name, var_value in variables.items():
                filled_line = filled_line.replace(f"{{{{{var_name}}}}}", str(var_value))

            # 检查是否是标题行（2级及以上标题才作为内容分区）
            is_title = bool(
                re.match(r'^#{2,6}\s+', filled_line)
                or re.match(r'^[一二三四五六七八九十]+[、.]', filled_line)
                or re.match(r'^\d+[、.]', filled_line)
            )

            if is_title:
                # 查找对应的分区
                for section in self.sections:
                    if section["start"] == i and section["type"] in section_contents:
                        result.append(filled_line)
                        # 填充分区内容
                        content = section_contents.get(section["type"], "")
                        result.append("")
                        result.append(content if content else "暂无")
                        result.append("")
                        filled_sections.add(section["start"])
                        break
                else:
                    result.append(filled_line)
            else:
                # 非标题行：检查是否在某个分区内
                in_filled_section = False
                for section in self.sections:
                    if section["start"] < i <= section["end"]:
                        if section["start"] in filled_sections:
                            # 这个分区已经被填充过了，跳过原模板内容
                            in_filled_section = True
                            break
                if not in_filled_section:
                    result.append(filled_line)

        return result

    def _build_completed_content(self, report: ReportData) -> str:
        """构建完成事项内容"""
        items = report.completed_items
        if not items:
            items = report.other_items  # 如果没有明确分类的，用其他项填充

        if not items:
            return "暂无"

        return "\n".join(f"- {item}" for item in items)

    def _build_stats_content(self, report: ReportData) -> str:
        """构建数据统计内容"""
        stats = report.stats
        return (
            f"| 指标 | 数值 |\n"
            f"|---|---|\n"
            f"| 提交次数 | {stats.get('commit_count', 0)} |\n"
            f"| 新增行数 | +{stats.get('added_lines', 0)} |\n"
            f"| 删除行数 | -{stats.get('removed_lines', 0)} |\n"
            f"| 修改文件数 | {stats.get('changed_files', 0)} |"
        )

    def _build_plan_content(self, report: ReportData) -> str:
        """构建计划内容"""
        items = report.plan_items
        if not items:
            return "待补充"
        return "\n".join(f"- {item}" for item in items)

    def _build_risk_content(self, report: ReportData) -> str:
        """构建风险与问题内容"""
        items = report.risk_items
        if not items:
            return "暂无"
        return "\n".join(f"- {item}" for item in items)

    def _build_in_progress_content(self, report: ReportData) -> str:
        """构建进行中内容"""
        items = report.in_progress_items
        if not items:
            return "暂无"
        return "\n".join(f"- {item}" for item in items)

    def _build_summary_content(self, report: ReportData) -> str:
        """构建工作总结内容（钉钉特有）"""
        items = report.summary_items
        if not items:
            # 如果没有专门的总结项，从完成事项生成简要总结
            if report.completed_items:
                return f"本周共完成 {len(report.completed_items)} 项工作，包括功能开发、Bug 修复和优化改进。"
            return "待补充"
        return "\n".join(f"- {item}" for item in items)

    def _build_other_content(self, report: ReportData) -> str:
        """构建其他事项内容（企业微信特有）"""
        # 其他事项通常用于填写备注信息，如果没有则显示"暂无"
        # 可以将风险问题、进行中事项等合并到这里
        items = []
        if report.risk_items:
            items.extend(report.risk_items)
        if report.in_progress_items:
            items.extend(report.in_progress_items)
        
        if items:
            return "\n".join(f"- {item}" for item in items)
        return "暂无"

    def _generate_default_report(self, report: ReportData, **variables) -> str:
        """无模板时使用默认格式生成报告"""
        stats = report.stats
        name = variables.get("name", "")
        date = variables.get("date", "")
        date_range = variables.get("date_range", "")
        week_num = variables.get("week_num", "")
        report_type = variables.get("report_type", "周报")

        lines = []
        lines.append(f"# 工作{report_type}")
        lines.append("")

        if name:
            lines.append(f"**姓名**：{name}")
        if date:
            lines.append(f"**日期**：{date}")
        if date_range:
            lines.append(f"**日期范围**：{date_range}")
        if week_num:
            lines.append(f"**周数**：{week_num}")
        lines.append("")

        # 完成事项
        lines.append("## 一、完成事项")
        lines.append("")
        if report.completed_items:
            for item in report.completed_items:
                lines.append(f"- {item}")
        elif report.other_items:
            for item in report.other_items:
                lines.append(f"- {item}")
        else:
            lines.append("暂无")
        lines.append("")

        # 数据统计
        lines.append("## 二、数据统计")
        lines.append("")
        lines.append("| 指标 | 数值 |")
        lines.append("|---|---|")
        lines.append(f"| 提交次数 | {stats.get('commit_count', 0)} |")
        lines.append(f"| 新增行数 | +{stats.get('added_lines', 0)} |")
        lines.append(f"| 删除行数 | -{stats.get('removed_lines', 0)} |")
        lines.append(f"| 修改文件数 | {stats.get('changed_files', 0)} |")
        if report_type == "周报":
            lines.append(f"| 活跃天数 | {stats.get('active_days', 0)} |")
        lines.append("")

        # 工作计划
        lines.append("## 三、工作计划")
        lines.append("")
        if report.plan_items:
            for item in report.plan_items:
                lines.append(f"- {item}")
        else:
            lines.append("待补充")
        lines.append("")

        # 风险与问题
        lines.append("## 四、风险与问题")
        lines.append("")
        if report.risk_items:
            for item in report.risk_items:
                lines.append(f"- {item}")
        else:
            lines.append("暂无")
        lines.append("")

        return "\n".join(lines)


# ============================================================
# Word 文档生成
# ============================================================

class WordGenerator:
    """将 Markdown 报告转换为 Word 文档"""

    def __init__(self):
        self.doc = None

    def generate(self, markdown_content: str, output_path: str) -> bool:
        """将 Markdown 转换为 Word 文档"""
        try:
            from docx import Document
            from docx.shared import Pt, Inches, RGBColor
            from docx.enum.text import WD_ALIGN_PARAGRAPH
            from docx.oxml.ns import qn
        except ImportError:
            print("[错误] 需要安装 python-docx 库: pip install python-docx")
            return False

        doc = Document()

        # 设置默认字体
        style = doc.styles['Normal']
        font = style.font
        font.name = 'Microsoft YaHei'
        font.size = Pt(11)
        style.element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft YaHei')

        lines = markdown_content.split("\n")
        i = 0

        while i < len(lines):
            line = lines[i]

            # 一级标题
            if line.startswith("# ") and not line.startswith("## "):
                title = line[2:].strip()
                p = doc.add_heading(title, level=1)
                for run in p.runs:
                    run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)

            # 二级标题
            elif line.startswith("## "):
                title = line[3:].strip()
                p = doc.add_heading(title, level=2)
                for run in p.runs:
                    run.font.color.rgb = RGBColor(0x44, 0x44, 0x44)

            # 三级标题
            elif line.startswith("### "):
                title = line[4:].strip()
                doc.add_heading(title, level=3)

            # 表格
            elif line.startswith("|"):
                table_lines = []
                while i < len(lines) and lines[i].startswith("|"):
                    table_lines.append(lines[i])
                    i += 1
                i -= 1  # 回退一步，因为循环会 i += 1

                if len(table_lines) >= 2:
                    # 解析表格
                    rows = []
                    for tl in table_lines:
                        if tl.startswith("|---") or tl.startswith("| --"):
                            continue  # 跳过分隔行
                        cells = [c.strip() for c in tl.split("|")[1:-1]]
                        rows.append(cells)

                    if rows:
                        table = doc.add_table(rows=len(rows), cols=len(rows[0]))
                        table.style = 'Light Grid Accent 1'
                        for r_idx, row in enumerate(rows):
                            for c_idx, cell_text in enumerate(row):
                                if c_idx < len(table.columns):
                                    table.cell(r_idx, c_idx).text = cell_text

            # 列表项
            elif line.strip().startswith("- "):
                item_text = line.strip()[2:]
                # 处理加粗标记
                p = doc.add_paragraph(style='List Bullet')
                self._add_formatted_text(p, item_text)

            # 加粗行（如 **姓名**：张三）
            elif line.strip().startswith("**") and ":" in line:
                p = doc.add_paragraph()
                self._add_formatted_text(p, line.strip())

            # 空行
            elif not line.strip():
                pass  # 跳过空行

            # 普通段落
            else:
                p = doc.add_paragraph()
                self._add_formatted_text(p, line.strip())

            i += 1

        doc.save(output_path)
        return True

    def _add_formatted_text(self, paragraph, text: str):
        """添加带格式的文本（处理 **加粗** 标记）"""
        parts = re.split(r'(\*\*[^*]+\*\*)', text)
        for part in parts:
            if part.startswith("**") and part.endswith("**"):
                run = paragraph.add_run(part[2:-2])
                run.bold = True
            else:
                paragraph.add_run(part)


# ============================================================
# 主程序
# ============================================================

def get_date_range(report_type: str) -> tuple:
    """获取报告的时间范围"""
    today = datetime.now()

    if report_type == "daily":
        since = today.strftime("%Y-%m-%d 00:00:00")
        until = today.strftime("%Y-%m-%d 23:59:59")
        return since, until
    elif report_type == "weekly":
        # 本周一到今天
        monday = today - timedelta(days=today.weekday())
        since = monday.strftime("%Y-%m-%d 00:00:00")
        until = today.strftime("%Y-%m-%d 23:59:59")
        return since, until
    elif report_type == "monthly":
        # 本月1号到今天
        first_day = today.replace(day=1)
        since = first_day.strftime("%Y-%m-%d 00:00:00")
        until = today.strftime("%Y-%m-%d 23:59:59")
        return since, until
    else:
        # 默认本周
        monday = today - timedelta(days=today.weekday())
        since = monday.strftime("%Y-%m-%d 00:00:00")
        until = today.strftime("%Y-%m-%d 23:59:59")
        return since, until


def get_week_number() -> str:
    """获取当前周数"""
    today = datetime.now()
    return f"第{today.isocalendar()[1]}周"


def main():
    parser = argparse.ArgumentParser(
        description="周报/日报自动生成工具 - 根据 Git Commit 自动生成工作汇报",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 生成本周周报（使用当前目录的 Git 仓库）
  python report_generator.py

  # 生成日报
  python report_generator.py --type daily

  # 指定仓库路径和作者
  python report_generator.py --repo /path/to/repo --author "张三"

  # 使用自定义模板
  python report_generator.py --template my_template.md

  # 同时生成 Word 文档
  python report_generator.py --type weekly --word

  # 指定输出路径
  python report_generator.py --output /path/to/output
        """,
    )

    parser.add_argument(
        "--repo", "-r",
        default=".",
        help="Git 仓库路径（默认为当前目录）",
    )
    parser.add_argument(
        "--author", "-a",
        default="",
        help="Git 作者名称（默认为所有作者）",
    )
    parser.add_argument(
        "--type", "-t",
        choices=["daily", "weekly", "monthly"],
        default="weekly",
        help="报告类型：daily(日报) / weekly(周报) / monthly(月报)（默认: weekly）",
    )
    parser.add_argument(
        "--template",
        default="",
        help="自定义模板文件路径（支持 .md 和 .txt 格式）",
    )
    parser.add_argument(
        "--name", "-n",
        default="",
        help="报告人姓名",
    )
    parser.add_argument(
        "--output", "-o",
        default=".",
        help="输出目录（默认为当前目录）",
    )
    parser.add_argument(
        "--word", "-w",
        action="store_true",
        help="同时生成 Word 文档",
    )
    parser.add_argument(
        "--since",
        default="",
        help="自定义起始日期（格式: YYYY-MM-DD）",
    )
    parser.add_argument(
        "--until",
        default="",
        help="自定义结束日期（格式: YYYY-MM-DD）",
    )

    args = parser.parse_args()

    # 验证仓库路径
    if not os.path.isdir(os.path.join(args.repo, ".git")):
        print(f"[错误] 不是有效的 Git 仓库: {args.repo}")
        sys.exit(1)

    # 获取时间范围
    if args.since:
        since = f"{args.since} 00:00:00"
    else:
        since, _ = get_date_range(args.type)

    if args.until:
        until = f"{args.until} 23:59:59"
    else:
        _, until = get_date_range(args.type)

    # 打印配置信息
    report_type_names = {"daily": "日报", "weekly": "周报", "monthly": "月报"}
    type_name = report_type_names.get(args.type, "报告")
    print(f"=" * 50)
    print(f"  {type_name}自动生成工具")
    print(f"=" * 50)
    print(f"  仓库路径: {os.path.abspath(args.repo)}")
    print(f"  作者: {args.author or '全部'}")
    print(f"  时间范围: {since} ~ {until}")
    print(f"  报告类型: {type_name}")
    if args.template:
        print(f"  模板: {args.template}")
    print(f"=" * 50)

    # 步骤1：提取 Git Commit
    print("\n[步骤1] 提取 Git Commit...")
    extractor = GitExtractor(args.repo, args.author)
    commits = extractor.get_commits(since, until)
    print(f"  找到 {len(commits)} 条 Commit 记录")

    if not commits:
        print("\n[提示] 指定时间范围内没有 Commit 记录，无法生成报告。")
        sys.exit(0)

    # 步骤2：分类
    print("[步骤2] 智能分类 Commit...")
    classifier = CommitClassifier()
    report = classifier.classify_all(commits)
    print(f"  完成事项: {len(report.completed_items)} 条")
    print(f"  工作计划: {len(report.plan_items)} 条")
    print(f"  风险问题: {len(report.risk_items)} 条")
    print(f"  进行中: {len(report.in_progress_items)} 条")
    print(f"  其他: {len(report.other_items)} 条")

    # 步骤3：模板填充
    print("[步骤3] 生成报告...")
    engine = TemplateEngine()

    # 准备变量
    today = datetime.now()
    variables = {
        "name": args.name,
        "date": today.strftime("%Y-%m-%d"),
        "date_range": f"{since[:10]} ~ {until[:10]}",
        "week_num": get_week_number(),
        "report_type": type_name,
    }

    if args.template:
        if engine.load_template(args.template):
            markdown_content = engine.fill_template(report, **variables)
        else:
            print("  [警告] 模板加载失败，使用默认格式")
            markdown_content = engine._generate_default_report(report, **variables)
    else:
        markdown_content = engine._generate_default_report(report, **variables)

    # 步骤4：保存报告
    output_dir = os.path.abspath(args.output)
    os.makedirs(output_dir, exist_ok=True)

    # 生成文件名
    date_str = today.strftime("%Y%m%d")
    md_filename = f"{type_name}_{date_str}.md"
    md_path = os.path.join(output_dir, md_filename)

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    print(f"  Markdown 报告已保存: {md_path}")

    # 生成 Word 文档
    if args.word:
        print("[步骤4] 生成 Word 文档...")
        word_generator = WordGenerator()
        docx_filename = f"{type_name}_{date_str}.docx"
        docx_path = os.path.join(output_dir, docx_filename)

        if word_generator.generate(markdown_content, docx_path):
            print(f"  Word 文档已保存: {docx_path}")
        else:
            print("  [警告] Word 文档生成失败")

    print(f"\n{'=' * 50}")
    print(f"  报告预览")
    print(f"{'=' * 50}")
    print(markdown_content)
    print(f"\n{'=' * 50}")
    print(f"  生成完成！")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
