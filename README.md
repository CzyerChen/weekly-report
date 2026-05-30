# Weekly Report Skill

## 一、Skill 简介
这是一款**面向全角色、多维度、全自动的周报/日报生成 Skill**，支持**项目/产品、技术/开发、测试、项目经理**等不同岗位，自动整合**项目管理工具数据 + 源代码管理工具数据**，双轨筛选负责事项与跟进内容，**只需要上传留痕数据，AI 直接输出完整规范报告**，周报更精准、日报更快捷。

## 文件结构

```
weekly-report/
├── SKILL.md                           # Skill 核心配置文件
├── README.md                          # 使用说明
├── templates/                         # 报告模板
│   ├── wechat_work_weekly.md         # 企业微信周报模板
│   ├── wechat_work_daily.md          # 企业微信日报模板
│   ├── dingtalk_weekly.md            # 钉钉周报模板
│   ├── dingtalk_daily.md             # 钉钉日报模板
│   ├── default_weekly.md              # 通用周报模板
│   └── default_daily.md               # 通用日报模板
├── docs/                              # 详细文档
│   └── design.md                      # 设计文档
├── tools/                             # 辅助工具
│   ├── extract_commits.py             # Git Commit 提取工具
│   ├── generate_from_json.py          # JSON 数据生成报告
│   └── report_generator.py            # 报告生成核心逻辑
├── demo/                              # 示例数据
│   ├── commits.json                   # 示例 Commit 数据
│   ├── issues-jira.csv                # 示例 JIRA 数据
│   └── issues-tapd.xlsx               # 示例 TAPD 数据
├── img/                               # 截图资源
│   ├── 企业微信-周报内容-产品经理.png    # 产品经理周报内容示例
│   ├── 企业微信-周报内容-开发人员.png    # 开发人员周报内容示例
│   ├── 企业微信-周报生成-产品经理.png    # 产品经理生成流程示例
│   └── 企业微信-周报生成-开发人员.png    # 开发人员生成流程示例
└── blog/                              # 相关文章
    ├── dev-1.png                      # 文章截图1
    ├── dev-2.png                      # 文章截图2
    ├── dev-3.png                      # 文章截图3
    └── 【Skill 创作】告别手写周报！项目+开发双维度自动生成，全程不用动脑.md
```

## 二、使用场景
### 为什么做它
每周写总结都在**回忆—查漏—补全—排版**上浪费大量时间：
- 产品/项目：只记得核心需求，**漏跟进、漏评审、漏协作**，每次写周报，除了总览JIRA任务进展，还要观察备注的进度，结合成员写的周报，花了挺多时间，再写项目周报，明确进展、问题、解决方法等，又耗时，人为描述可能遗漏
- 开发/技术：只记得写代码，**说不清任务关联、讲不清进度价值**，每次写周报都要先纵览一下JIRA和GIT，看看自己做了什么，写周报就是寥寥几字，程序员确实不爱长篇大论写作文，写的太简略，自己知道什么回事，领导又要过来问三问四
- 所有人：靠回忆写不全，**工作留痕≠总结呈现**
- 传统自动化：只抓任务、不抓协作；只抓表面、不抓细节

### 解决了什么
- **全程不用动脑**：不用回忆、不用梳理、不用排版，**把已有的留痕丢给 AI 即可**
- **覆盖双进度**：同时呈现**项目管理进展 + 代码开发进展**，数据完整有依据
- **角色自动适配**：产品看需求、开发看代码、测试看验证，一份报告贴合岗位
- **更适合周报**：周报周期数据充足、颗粒度完整；日报快速生成、简洁高效

### 省掉哪些动作
- 不用翻平台查本周任务
- 不用核对评论找协作事项
- 不用翻 Git/代码库统计工作量
- 不用分类、不用润色、不用排版
- 不用怕漏项、不用怕写得干巴

**做了的，能写的都写了，觉得冗余，只需要你删一删**
**感觉模板不好，自己添加个模板，强化下指定岗位的周报模板**

## 三、创作过程

由于较长，[完整创作文档参看](docs/design.md)
由于较长，[完整创作历程](blog/【Skill 创作】告别手写周报！项目+开发双维度自动生成，全程不用动脑.md)

## 四、快速开始

### 项目/产品/测试同学（仅项目数据）
1. 从项目管理工具导出本周数据，例如：JIRA、TAPD、禅道等
2. 上传文件到 SOLO，例如：issues.csv
3. 告诉 AI 姓名与角色，例如：
>请根据我上传的 issues.csv 生成周报。
姓名：蛋仔
姓名变体：chenziyan, czy, chenzy, Claire
角色：产品经理
模板：企业微信
4. 直接生成完整报告

![alt text](image-5.png)

### 技术/开发同学（项目+源码）
1. 导出项目管理数据，例如：JIRA、TAPD、禅道等
2. 本地提取代码提交记录，例如：git commit log
3. 上传两份数据文件，例如：issues.csv,commits.json
4. AI 自动融合任务进展 + 开发细节，生成专业周报
> 请根据我上传的 issues.csv,commits.json 生成周报。
姓名：蛋仔
姓名变体：chenziyan, czy, chenzy, Claire
角色：开发
模板：企业微信

![alt text](image-4.png)

### issues.csv 哪里来？

以 JIRA 为例：

1. 登录 JIRA → 进入问题筛选器

2. 设置**双轨筛选条件**（确保不遗漏跟进内容）：

   **方式一：导出 Assignee 是自己的任务（开发项）**
   ```
   assignee = currentUser()
   ```

   **方式二：导出自己参与评论的任务（跟进内容 - Comment）**
   ```
   issueFunction in commented("by chenziyan") 
   ```

   **方式三：导出自己关注的任务（跟进内容 - Watcher）**
   ```
   watcher = currentUser()
   ```

   **方式四：导出自己创建的任务（跟进内容 - Reporter）**
   ```
   reporter = currentUser() AND assignee != currentUser()
   ```

   **方式五：合并导出（推荐）**
   ```
   assignee = currentUser() 
   OR issueFunction in commented("by chenziyan") 
   OR watcher = currentUser()
   OR (reporter = currentUser() AND assignee != currentUser())
   ```

3. 设置时间条件：
   ```
   updated >= -7d（本周）
   或
   updated >= startOfWeek() AND updated <= endOfWeek()
   ```

4. 点击「导出」→ 选择「CSV（所有字段）」

5. 保存为 `issues.csv`

**重要**：确保导出的 CSV 包含以下字段：
- `Issue key`（Issue 编号）
- `Summary`（标题）
- `Issue Type`（类型）
- `Status`（状态）
- `Assignee`（负责人）
- `Reporter`（创建人）
- `Watchers`（关注人）
- `Comment`（评论内容）
- `Updated`（更新时间）

其他工具：
- **TAPD**：需求/缺陷 → 高级筛选 → 导出 Excel（确保包含「评论」字段）
- **禅道**：Bug/任务 → 筛选 → 导出 CSV（确保包含「评论」字段）

### commits.json 哪里来？

```bash
# 下载 extract_commits.py 到本地

# 进入你的 Git 仓库目录
cd /path/to/your/repo

# 运行提取脚本
python3 extract_commits.py --repo . --authors "你的名字"
```

## 支持的平台

| 平台 | 模板文件 |
|------|---------|
| 企业微信 | wechat_work_weekly.md |
| 钉钉 | dingtalk_weekly.md |
| 通用 | default_weekly.md |

## 角色支持

| 角色 | 报告特点 |
|------|---------|
| 开发人员 | 开发项 + 代码提交信息 |
| 产品经理 | 负责任务 + 需求管理 |
| 测试人员 | 测试任务 + 执行结果 |
| 项目经理 | 项目进度 + 整体协调 |

## 姓名匹配

支持多种姓名格式：
- 中文全名：蛋仔
- 拼音全拼：chenziyan
- 拼音简写：czy, chenzy
- 英文名：Claire

## 双轨筛选

1. **Assignee = 本人**：负责任务/开发项
2. **Comment/Watcher/Reporter = 本人**：跟进内容

## 提取 Git Commits

```bash
# 安装依赖
pip install GitPython

# 提取本周提交
python extract_commits.py --repo /path/to/repo --authors "蛋仔,Claire"

# 提取指定时间范围
python extract_commits.py --repo /path/to/repo --authors "蛋仔" --since 2026-05-01 --until 2026-05-29
```

## 模板变量

| 变量 | 说明 | 示例 |
|------|------|------|
| `{{name}}` | 姓名 | 蛋仔 |
| `{{date_range}}` | 日期范围 | 2026-05-25 ~ 2026-05-29 |
| `{{role}}` | 角色 | 开发人员 |
| `{{hasDevelopmentItems}}` | 是否有开发项 | true/false |
| `{{hasResponsibleTasks}}` | 是否有负责任务 | true/false |
| `{{hasFollowUpItems}}` | 是否有跟进内容 | true/false |
| `{{hasCommits}}` | 是否有代码提交 | true/false |

## 示例输出

### 企业微信周报

```
蛋仔 周报
日期范围：2026年5月25日 - 2026年5月29日

本周工作总结

一、开发项（Assignee + 代码提交）

1. Doris慢查询告警（CP-2022） - 🐛 进行中
   - 接口监控已上线
   - 代码：fix(monitor): 修复接口超时问题

二、负责任务（Assignee = 本人）

1. MySQL优化（CP-1972） - ⚡ 待处理
   - 推进参数优化落地

三、跟进内容

1. 告警模式（CP-1986） - ✨ 已完成
   - 类型：Reporter
   - 功能已上线

下周工作规划

1. 标签上线
2. 持续优化接口监控
```

## 常见问题

**Q: CSV 文件太大怎么办？**
A: 在项目管理工具中设置更精确的筛选条件，如仅导出本周更新的 Issue。

**Q: 如何导出更多字段？**
A: 点击「列」→「自定义列」，添加需要的字段后重新导出。

**Q: 支持其他工具吗？**
A: 只要支持导出 CSV/Excel 格式，且包含基本字段（标题、状态、负责人、时间），即可使用。

## 版本历史

| 版本 | 日期 | 更新内容 |
|---|---|---|
| v1.0 | 2026-05-29 | 初始版本，支持 Git Commit 提取和周报生成 |
| v2.0 | 2026-05-29 | 新增项目管理工具集成（JIRA/TAPD/禅道） |
| v2.1 | 2026-05-29 | 重构文档结构，以用户角色为主线，离线方式优先 |
| v2.2 | 2026-05-29 | 新增双轨筛选机制（开发项+跟进内容），支持姓名变体匹配 |
| v2.3 | 2026-05-29 | 扩展为多轨筛选，新增 Watcher 和 Reporter 识别 |
| v2.4 | 2026-05-29 | 强化角色区分逻辑，支持无角色声明时的自动推断 |
