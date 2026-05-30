#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git Commit 信息提取工具（增强版）
在本地运行，将 Commit 信息导出为 JSON 文件，上传到 SOLO 生成周报

增强功能：
1. 提取变更文件路径列表
2. 提取 Commit 所在分支
3. 根据文件路径推断功能模块
4. 合并关联 Commit（同一文件/模块的多次提交合并为一条描述）
"""

import os
import re
import sys
import json
import argparse
import subprocess
from datetime import datetime, timedelta
from collections import defaultdict


def _run_git(repo_path: str, args: list) -> str:
    """执行 Git 命令"""
    cmd = ["git", "-C", repo_path] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return ""


def get_changed_files(repo_path: str, commit_hash: str) -> list:
    """获取指定 Commit 修改的文件列表"""
    output = _run_git(repo_path, ["diff-tree", "--no-commit-id", "--name-only", "-r", commit_hash])
    if not output:
        return []
    return [f.strip() for f in output.split("\n") if f.strip()]


def get_branch_for_commit(repo_path: str, commit_hash: str) -> str:
    """获取 Commit 所在的分支名"""
    output = _run_git(repo_path, [
        "branch", "--all", "--contains", commit_hash
    ])
    if not output:
        return ""
    branches = [b.strip().replace("* ", "") for b in output.split("\n") if b.strip()]
    # 优先返回非 HEAD 分支
    for b in branches:
        if "HEAD" not in b and "detached" not in b:
            return b
    return branches[0] if branches else ""


def infer_module_from_files(files: list) -> str:
    """根据变更文件路径推断功能模块"""
    if not files:
        return ""

    # 提取文件路径中的关键目录/模块名
    modules = set()
    for f in files:
        parts = f.replace("\\", "/").split("/")
        # 跳过常见的非模块目录
        skip_dirs = {"src", "main", "java", "resources", "test", "webapp",
                      "static", "templates", "public", "config", "utils",
                      "common", "base", "core", "entity", "dto", "vo",
                      "controller", "service", "mapper", "dao", "model"}
        for part in parts:
            if part and part not in skip_dirs and not part.endswith(".java") \
               and not part.endswith(".xml") and not part.endswith(".html") \
               and not part.endswith(".js") and not part.endswith(".css") \
               and not part.endswith(".sql") and not part.endswith(".yml") \
               and not part.endswith(".yaml") and not part.endswith(".properties"):
                modules.add(part)

    if modules:
        return "/".join(sorted(modules))
    return ""


def infer_module_from_message(message: str) -> str:
    """从 Commit Message 中提取模块信息（如 Conventional Commits 的 scope）"""
    match = re.match(r'^\w+\(([^)]+)\)', message)
    if match:
        return match.group(1)
    return ""


def get_commits(repo_path: str, since: str, until: str, authors: list = None, 
                 enrich: bool = True, merge_related: bool = True) -> list:
    """获取 Git Commit 列表（增强版）"""

    cmd = [
        "git", "-C", repo_path,
        "log",
        f"--since={since}",
        "--pretty=format:%H|%ad|%an|%s",
        "--date=short",
        "--numstat",
    ]

    if until:
        cmd.append(f"--until={until}")

    if authors:
        all_commits = []
        seen_hashes = set()
        for author in authors:
            cmd_author = cmd + [f"--author={author}"]
            try:
                result = subprocess.run(cmd_author, capture_output=True, text=True, check=True)
                commits = parse_git_output(result.stdout, repo_path, enrich)
                for commit in commits:
                    if commit["hash"] not in seen_hashes:
                        seen_hashes.add(commit["hash"])
                        all_commits.append(commit)
            except subprocess.CalledProcessError:
                print(f"[警告] 无法获取作者 '{author}' 的 Commit")
        commits = all_commits
    else:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            commits = parse_git_output(result.stdout, repo_path, enrich)
        except subprocess.CalledProcessError as e:
            print(f"[错误] Git 命令执行失败: {e}")
            commits = []

    # 合并关联 Commit
    if merge_related:
        commits = merge_related_commits(commits)

    return commits


def parse_git_output(output: str, repo_path: str, enrich: bool) -> list:
    """解析 Git 输出（增强版）"""
    commits = []
    current_commit = None
    added = 0
    removed = 0
    files = []
    changed_files_list = []

    for line in output.split("\n"):
        if not line.strip():
            continue

        if re.match(r'^[a-f0-9]+\|', line):
            if current_commit:
                current_commit["added_lines"] = added
                current_commit["removed_lines"] = removed
                current_commit["files_changed"] = len(files)
                current_commit["changed_files"] = files
                commits.append(current_commit)

            parts = line.split("|", 3)
            commit_hash = parts[0]
            current_commit = {
                "hash": commit_hash,
                "date": parts[1],
                "author": parts[2],
                "message": parts[3] if len(parts) > 3 else "",
            }

            # 增强信息
            if enrich:
                changed_files_list = get_changed_files(repo_path, commit_hash)
                current_commit["changed_files"] = changed_files_list
                current_commit["branch"] = get_branch_for_commit(repo_path, commit_hash)
                current_commit["module"] = (
                    infer_module_from_message(current_commit["message"]) or
                    infer_module_from_files(changed_files_list)
                )
            else:
                current_commit["changed_files"] = []
                current_commit["branch"] = ""
                current_commit["module"] = ""

            added = 0
            removed = 0
            files = []
        else:
            parts = line.split("\t")
            if len(parts) >= 3:
                try:
                    a = int(parts[0]) if parts[0] != "-" else 0
                    r = int(parts[1]) if parts[1] != "-" else 0
                    added += a
                    removed += r
                    if len(parts) >= 3 and parts[2].strip():
                        files.append(parts[2].strip())
                except ValueError:
                    pass

    if current_commit:
        current_commit["added_lines"] = added
        current_commit["removed_lines"] = removed
        current_commit["files_changed"] = len(files)
        if not current_commit.get("changed_files"):
            current_commit["changed_files"] = files
        commits.append(current_commit)

    return commits


def merge_related_commits(commits: list) -> list:
    """合并关联 Commit：同一模块的多次简短提交合并为一条描述"""
    if not commits:
        return commits

    # 过滤 Merge Commit
    non_merge = []
    merge_commits = []
    for c in commits:
        msg = c["message"].strip().lower()
        if msg.startswith("merge") or msg.startswith("merge branch"):
            merge_commits.append(c)
        else:
            non_merge.append(c)

    # 按模块分组
    module_groups = defaultdict(list)
    for c in non_merge:
        module = c.get("module", "") or "other"
        module_groups[module].append(c)

    merged = []
    for module, group in module_groups.items():
        if len(group) == 1:
            merged.append(group[0])
        else:
            # 合并同一模块的多次提交
            total_added = sum(c["added_lines"] for c in group)
            total_removed = sum(c["removed_lines"] for c in group)
            all_files = []
            all_messages = []
            dates = set()
            for c in group:
                all_files.extend(c.get("changed_files", []))
                all_messages.append(c["message"])
                dates.add(c["date"])

            # 生成合并描述
            messages = [m for m in all_messages if m.strip()]
            if len(messages) <= 3:
                merged_msg = "、".join(messages)
            else:
                merged_msg = f"{messages[0]} 等 {len(messages)} 项提交"

            merged_commit = {
                "hash": group[0]["hash"],
                "date": min(dates),
                "author": group[0]["author"],
                "message": merged_msg,
                "added_lines": total_added,
                "removed_lines": total_removed,
                "files_changed": len(set(all_files)),
                "changed_files": list(set(all_files)),
                "branch": group[0].get("branch", ""),
                "module": module,
                "merged_count": len(group),
                "original_commits": all_messages,
            }
            merged.append(merged_commit)

    # 按日期排序
    merged.sort(key=lambda x: x["date"])
    # 合并 Merge Commit 保留（可选）
    merged.extend(merge_commits)

    return merged


def get_date_range(report_type: str) -> tuple:
    """获取时间范围"""
    today = datetime.now()
    if report_type == "daily":
        since = today.strftime("%Y-%m-%d 00:00:00")
        until = today.strftime("%Y-%m-%d 23:59:59")
    elif report_type == "weekly":
        monday = today - timedelta(days=today.weekday())
        since = monday.strftime("%Y-%m-%d 00:00:00")
        until = today.strftime("%Y-%m-%d 23:59:59")
    elif report_type == "monthly":
        first_day = today.replace(day=1)
        since = first_day.strftime("%Y-%m-%d 00:00:00")
        until = today.strftime("%Y-%m-%d 23:59:59")
    else:
        monday = today - timedelta(days=today.weekday())
        since = monday.strftime("%Y-%m-%d 00:00:00")
        until = today.strftime("%Y-%m-%d 23:59:59")
    return since, until


def main():
    parser = argparse.ArgumentParser(
        description="Git Commit 信息提取工具（增强版）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 提取本周所有 Commit（增强模式）
  python extract_commits.py --repo /path/to/repo

  # 提取本周指定作者的 Commit（多作者用逗号分隔）
  python extract_commits.py --repo /path/to/repo --authors "Claire,陈子妍"

  # 不合并关联 Commit（保留每一条原始提交）
  python extract_commits.py --repo /path/to/repo --no-merge

  # 不提取增强信息（仅基础信息，速度更快）
  python extract_commits.py --repo /path/to/repo --no-enrich

  # 提取本月 Commit
  python extract_commits.py --repo /path/to/repo --type monthly

  # 指定时间范围
  python extract_commits.py --repo /path/to/repo --since 2026-05-01 --until 2026-05-28
        """,
    )

    parser.add_argument("--repo", "-r", default=".", help="Git 仓库路径（默认为当前目录）")
    parser.add_argument("--authors", "-a", default="", help="作者列表，多个用逗号分隔")
    parser.add_argument("--type", "-t", choices=["daily", "weekly", "monthly"],
                        default="weekly", help="报告类型（默认: weekly）")
    parser.add_argument("--since", default="", help="起始日期（格式: YYYY-MM-DD）")
    parser.add_argument("--until", default="", help="结束日期（格式: YYYY-MM-DD）")
    parser.add_argument("--output", "-o", default="commits.json", help="输出文件（默认: commits.json）")
    parser.add_argument("--no-enrich", action="store_true",
                        help="不提取增强信息（变更文件、分支、模块），速度更快")
    parser.add_argument("--no-merge", action="store_true",
                        help="不合并关联 Commit，保留每一条原始提交")

    args = parser.parse_args()

    # 验证仓库
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

    # 解析作者列表
    authors = None
    if args.authors:
        authors = [a.strip() for a in args.authors.split(",") if a.strip()]

    enrich = not args.no_enrich
    merge_related = not args.no_merge

    # 提取 Commit
    print("=" * 50)
    print("  Git Commit 信息提取（增强版）")
    print("=" * 50)
    print(f"  仓库路径: {os.path.abspath(args.repo)}")
    print(f"  时间范围: {since[:10]} ~ {until[:10]}")
    if authors:
        print(f"  作者列表: {', '.join(authors)}")
    else:
        print(f"  作者: 全部")
    print(f"  增强信息: {'开启' if enrich else '关闭'}")
    print(f"  关联合并: {'开启' if merge_related else '关闭'}")
    print("=" * 50)

    commits = get_commits(args.repo, since, until, authors, enrich=enrich, merge_related=merge_related)
    print(f"\n共提取 {len(commits)} 条 Commit 记录")

    if not commits:
        print("[提示] 没有找到 Commit 记录")
        sys.exit(0)

    # 打印合并信息
    merged_count = sum(1 for c in commits if c.get("merged_count", 0) > 1)
    if merged_count:
        print(f"  其中 {merged_count} 条为合并后的记录（原始提交已合并）")

    # 打印模块信息
    if enrich:
        modules = set(c.get("module", "") for c in commits if c.get("module"))
        if modules:
            print(f"  涉及模块: {', '.join(sorted(modules))}")

    # 导出到 JSON
    output_data = {
        "repo": os.path.abspath(args.repo),
        "since": since,
        "until": until,
        "authors": authors,
        "report_type": args.type,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "enriched": enrich,
        "merged": merge_related,
        "commits": commits,
    }

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\n已保存到: {args.output}")
    print(f"\n请将 {args.output} 文件上传到 SOLO 生成周报。")

    # 打印统计
    total_added = sum(c["added_lines"] for c in commits)
    total_removed = sum(c["removed_lines"] for c in commits)
    unique_authors = set(c["author"] for c in commits)
    unique_dates = set(c["date"] for c in commits)

    print(f"\n统计信息:")
    print(f"  - 提交次数: {len(commits)}")
    print(f"  - 新增行数: +{total_added}")
    print(f"  - 删除行数: -{total_removed}")
    print(f"  - 涉及作者: {len(unique_authors)} ({', '.join(unique_authors)})")
    print(f"  - 活跃天数: {len(unique_dates)}")

    # 打印每条 Commit 的摘要
    print(f"\n{'─' * 50}")
    print("  Commit 摘要")
    print(f"{'─' * 50}")
    for c in commits:
        merged_info = f" (合并{c.get('merged_count', 1)}条)" if c.get("merged_count", 1) > 1 else ""
        module_info = f" [{c.get('module', '')}]" if c.get('module', '') else ""
        print(f"  {c['date']}  {c['message'][:50]}{module_info}{merged_info}")


if __name__ == "__main__":
    main()
