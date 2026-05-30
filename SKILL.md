---
name: "weekly-report"
description: "Generates weekly/daily reports from JIRA/TAPD issues and Git commits. Invoke when user uploads issues.csv and commits.json and asks for report generation."
---

# 自动化周报/日报生成工具

为不同角色的团队成员提供自动化的周报/日报生成能力，支持从项目管理工具（JIRA/TAPD/禅道等）和 Git Commit 代码提交信息融合生成完整报告。

---

## 一、概述

### 1.1 目标

- **项目/产品人员**：基于项目管理工具的任务数据（JIRA/TAPD/禅道等）生成报告
- **技术人员/开发人员**：融合项目管理工具任务 + Git Commit 代码提交信息生成完整报告

### 1.2 角色识别与报告适配

| 角色类型 | 识别方式 | 报告特点 |
|---|---|---|
| **产品/项目人员** | 未提供 commits.json 或 Commit 与 Issue 无关联| 侧重任务进度、需求管理、项目推进 |
| **技术/开发人员** | 提供 commits.json 或 Commit 与 Issue 有关联， 在任务基础上增加代码功能描述、技术方案，若与 Issue 无关联，则直接当一个开发项描述，描述功能 | 增加代码功能描述、技术方案 |

**角色声明方式**：

```
请根据我上传的 issues.csv 生成周报。
姓名：蛋仔
角色：产品经理
```

**Assignee 的多重含义**：

| 角色 | Assignee = 本人的含义 | 报告展示 |
|---|---|---|
| 开发人员 | 负责代码开发 | 「开发项」+ 代码详情 |
| 产品经理 | 负责需求管理 | 「负责任务」+ 进度状态 |
| 测试人员 | 负责测试执行 | 「测试任务」+ 测试结果 |
| 项目经理 | 负责项目推进 | 「负责任务」+ 整体进度 |

```
IF 用户声明角色为 "产品经理" OR "项目经理" OR "测试人员"
   OR (未提供 commits.json)
THEN 归类为「产品/项目角色」
     使用「负责任务」而非「开发项」

IF 用户声明角色为 "开发人员" OR "技术负责人"
   OR (提供了 commits.json 且 Commit 与 Issue 有关联)
THEN 归类为「技术/开发角色」
     区分「开发项」和「负责任务」
```

**技术角色的细分**：

| 子分类 | 识别条件 | 说明 |
|---|---|---|
| **开发项** | Assignee = 本人 AND 有关联的 Commit | 实际编写代码的开发任务 |
| **负责任务** | Assignee = 本人 AND 无关联 Commit | 技术评审、方案设计、非编码任务 |

### 1.3 智能筛选逻辑

**双轨筛选机制**：

| 筛选条件 | 含义 | 报告分类 |
|---|---|---|
| **Assignee 是本人** | 自己是该任务的负责人/开发者 | **开发项** |
| **Comment 中有本人** | 本人在该任务下回复或跟进过 | **跟进内容** |
| **Watcher 是本人** | 本人关注该任务的进展 | **跟进内容** |
| **Reporter 是本人** | 本人创建的任务 | **跟进内容** |

**为什么需要双轨筛选？**

| 角色 | Assignee = 本人 | Comment/Watcher/Reporter = 本人 |
|---|---|---|
| 开发人员 | 开发负责人，主要编写代码 | 在他人任务中提供技术支持、关注进展、创建任务 |
| 测试人员 | 负责测试的任务 | 验证他人开发的 Bug、关注待测任务 |
| 产品经理 | 负责的需求 | 跟进其他人实现的功能、监控需求进展 |

#### 1.3.1 内容区分规则

##### 1.3.1.1  产品/项目角色 - 负责任务（Assignee = 本人）

**识别规则**：
```
IF Assignee 匹配本人姓名（任意格式）
THEN 该 Issue 归类为「负责任务」
```

**报告展示**：
- 作为主要负责的工作内容展示
- 展示任务进度、状态、关键节点
- 不关联代码信息

**示例标题**：
- 产品经理：「负责任务」「需求管理」「项目推进」
- 测试人员：「测试任务」「用例执行」「Bug验证」
- 项目经理：「负责任务」「项目协调」「进度管理」

##### 1.3.1.2  技术/开发角色 - 开发项（Assignee = 本人 + 有关联Commit）

**识别规则**：
```
IF Assignee 匹配本人姓名（任意格式）
AND 存在与该Issue关联的Git Commit
THEN 该 Issue 归类为「开发项」
```

**报告展示**：
- 作为主要开发工作展示
- 关联 Git Commit，展示代码实现细节
- 显示代码变更统计（新增/删除行数）

##### 1.3.1.3  技术/开发角色 - 负责任务（Assignee = 本人 + 无关联Commit）

**识别规则**：
```
IF Assignee 匹配本人姓名（任意格式）
AND 不存在与该Issue关联的Git Commit
THEN 该 Issue 归类为「负责任务」
```

**典型场景**：
- 技术方案评审
- 代码审查（Code Review）
- 技术调研
- 架构设计
- 文档编写

##### 1.3.1.4  跟进内容（Comment/Watcher/Reporter 包含本人）

**识别规则**：
```
IF (Comment 中包含本人姓名（任意格式）
    OR Watcher 包含本人
    OR Reporter = 本人)
AND Assignee != 本人
THEN 该 Issue 归类为「跟进内容」
```

**跟进类型细分**：

| 类型 | 识别条件 | 典型场景 |
|---|---|---|
| **Comment参与** | Comment 包含本人姓名 | 在他人任务中回复、提供技术支持、验收确认 |
| **Watcher关注** | Watcher 列表包含本人 | 监控任务进展、等待任务完成进行下一步工作 |
| **Reporter创建** | Reporter = 本人 | 创建的任务分配给其他人、需求/缺陷上报 |

**报告展示**：
- 作为协助/跟进内容展示
- 标注跟进类型（Comment/Watcher/Reporter）
- 提取本人评论的关键信息（如为Comment类型）
- 标注原负责人

### 1.4 姓名识别与匹配

| 姓名格式 | 示例 | 匹配方式 |
|---|---|---|
| **中文全名** | 张三、蛋仔 | 精确匹配 |
| **英文名** | San Zhang、Tom | 精确匹配 |
| **拼音（全拼）** | zhangsan、chenziyan | 精确匹配（不区分大小写） |
| **拼音（简写）** | zs、czy、chenzy | 精确匹配（不区分大小写） |

**匹配优先级**：
1. 精确匹配（中文全名）
2. 忽略大小写的拼音匹配
3. 部分匹配（如 "陈" 可以匹配 "蛋仔"）

**配置方式**：

```
姓名：蛋仔
姓名变体：chenziyan, czy, chenzy, Claire
```

---

## 二、数据格式规范

### 2.1 项目管理工具导出格式

#### JIRA CSV 格式

**必需字段**：

| 字段名 | 说明 | 示例 |
|---|---|---|
| `Issue key` | Issue 编号 | `PROJ-123` |
| `Summary` | 标题 | `修复用户登录异常` |
| `Issue Type` | 类型 | `Bug` / `Story` / `Task` |
| `Status` | 状态 | `In Progress` / `Done` / `To Do` |
| `Assignee` | 负责人 | `张三` |
| `Reporter` | 创建人 | `张三` |
| `Watchers` | 关注人 | `李四, 王五` |
| `Comment` | 评论内容 | `张三: 已完成代码开发，等待测试验收` |
| `Created` | 创建时间 | `2026-05-25` |
| `Updated` | 更新时间 | `2026-05-26` |

**可选但推荐字段**：

| 字段名 | 说明 | 示例 |
|---|---|---|
| `Description` | 问题描述 | `用户反馈登录时报错...` |
| `Priority` | 优先级 | `High` / `Medium` / `Low` |
| `Labels` | 标签 | `backend`, `urgent` |

#### TAPD Excel 格式

**必需字段**：

| 字段名 | 说明 |
|---|---|
| `ID` | 编号 |
| `标题` | 标题 |
| `类型` | 缺陷/需求/任务 |
| `状态` | 已解决/实现中/新建 |
| `处理人` | 负责人 |
| `创建人` | 创建人 |
| `创建时间` | 创建时间 |
| `最后修改时间` | 更新时间 |

#### 禅道 CSV 格式

**必需字段**：

| 字段名 | 说明 |
|---|---|
| `编号` | Bug/任务 ID |
| `需求名称` | 需求名称 |
| `类别` | Bug/任务 |
| `当前状态` | 已关闭/已解决/进行中 |
| `指派给` | 负责人 |
| `由谁创建` | 创建人 |
| `抄送给` | 关注人 |
| `创建日期` | 创建时间 |

### 2.2 Git Commit JSON 格式

```json
{
  "repo": "/path/to/repo",
  "since": "2026-05-25 00:00:00",
  "until": "2026-05-29 23:59:59",
  "authors": ["张三", "Claire"],
  "report_type": "weekly",
  "generated_at": "2026-05-29 15:30:00",
  "enriched": true,
  "merged": true,
  "commits": [
    {
      "hash": "abc123...",
      "date": "2026-05-26",
      "author": "张三",
      "message": "feat(user): 添加用户登录功能",
      "added_lines": 45,
      "removed_lines": 3,
      "files_changed": 2,
      "changed_files": [
        "src/main/java/com/xxx/UserService.java",
        "src/main/resources/mapper/UserMapper.xml"
      ],
      "branch": "feature/user-login",
      "module": "user"
    }
  ]
}
```

---

## 三、数据融合策略（技术人员专用）

### 3.1 融合逻辑

当同时提供 Issue 列表和 Git Commit 时，SOLO 按以下策略融合：

1. **Issue 为主** → 描述"做了什么任务"
2. **Commit 为辅** → 如果 Commit 从关键字或内容上能匹配到 Issue，则利用 commit message 补充"代码实现"情况，无需体现行数；如果 Commit 从关键字或内容上能匹配到 Issue，则直接当一个开发项描述，描述功能无需体现行数
3. **模块归类** → 按功能模块组织展示

### 3.2 融合示例

| Issue | Commit | 融合后描述 |
|---|---|---|
| `PROJ-123 修复用户登录异常` | `fix(user): 修复登录时的空指针` | **用户模块** - 🐛 Bug修复：修复用户登录异常（空指针问题） |
| `PROJ-124 新增订单导出` | `feat(order): 实现导出接口` | **订单模块** - ✨ 新功能：新增订单导出功能（接口实现） |
|  | `task: 调整调价函模板` | **费用模块** - ⚡ 优化/任务：优化调价函模板（语句优化） |

### 3.3 状态映射

| Issue 状态 | 报告分类 | 说明 |
|---|---|---|
| `Done` / `Closed` / `Resolved` / `已解决` / `已关闭` | ✅ 已完成 | 本周已完成的工作 |
| `In Progress` / `进行中` / `实现中` | 🔄 进行中 | 尚未完成的工作 |
| `To Do` / `Open` / `新建` / `待处理` | 📋 待处理 | 下周待处理的工作 |

### 3.4 类型标签

| Issue 类型 | 标签 | 说明 |
|---|---|---|
| `Bug` / `缺陷` | 🐛 Bug修复 | 问题修复类工作 |
| `Story` / `需求` / `Feature` | ✨ 新功能 | 功能开发类工作 |
| `Task` / `任务` / `Improvement` | ⚡ 优化/任务 | 优化改进类工作 |

---

## 四、模板支持

### 4.1 内置模板（精确映射表）

**CRITICAL：必须严格按以下映射表选择模板，不得自由发挥。**

| 用户声明的平台 | 用户声明的周期 | 对应模板文件 |
|---|---|---|
| 企业微信 / 企微 / wechat | 周报 / 周 / weekly / 周工作总结 | `templates/wechat_work_weekly.md` |
| 企业微信 / 企微 / wechat | 日报 / 日 / daily / 日工作总结 | `templates/wechat_work_daily.md` |
| 钉钉 / dingtalk | 周报 / 周 / weekly / 周工作总结 | `templates/dingtalk_weekly.md` |
| 钉钉 / dingtalk | 日报 / 日 / daily / 日工作总结 | `templates/dingtalk_daily.md` |
| 通用 / 普通 / 默认 | 周报 / 周 / weekly | `templates/default_weekly.md` |
| 通用 / 普通 / 默认 | 日报 / 日 / daily | `templates/default_daily.md` |

**模板选择决策树**：

```
用户声明了模板参数吗？
├── 是 → 从上表精确匹配「平台 + 周期」
│        示例："企业微信" + "周报" → wechat_work_weekly.md
│        示例："钉钉" + "日报" → dingtalk_daily.md
│        示例："企业微信" → 默认周期为周报 → wechat_work_weekly.md
│        示例："周报" → 默认平台为通用 → default_weekly.md
└── 否 → 默认使用：通用周报 → default_weekly.md
```

### 4.2 模板文件对应关系

```
templates/wechat_work_weekly.md    ← 用户说：企业微信 + 周报
templates/wechat_work_daily.md      ← 用户说：企业微信 + 日报
templates/dingtalk_weekly.md       ← 用户说：钉钉 + 周报
templates/dingtalk_daily.md        ← 用户说：钉钉 + 日报
templates/default_weekly.md         ← 用户说：通用 + 周报（或只说"周报"）
templates/default_daily.md          ← 用户说：通用 + 日报（或只说"日报"）
```

**CRITICAL**：
- 模板文件路径必须在 `templates/` 目录下，不得自行创建或修改模板文件名
- 用户说"用企业微信模板"但未说日报还是周报时，**默认按周报处理**
- 用户说"生成周报"但未说平台时，**默认使用通用模板**

### 4.3 模板变量说明

生成报告时，AI 必须读取 `templates/` 目录下的真实模板文件，找到文件中所有的 `{{变量名}}` 占位符，并用实际值逐一替换。不得跳过读取模板文件直接输出报告。

#### 4.3.1 变量来源与提取规则

| 变量 | 必填 | 来源 | 提取方式 | 默认值 |
|---|---|---|---|---|
| `{{name}}` | ✅ 是 | 用户请求 | 从 `姓名：XXX` 提取 | 无默认值，必须用户提供 |
| `{{date_range}}` | ✅ 是 | 用户请求或数据推断 | 从用户声明的周期提取，格式为 `YYYY-MM-DD ~ YYYY-MM-DD` | 无默认值，推断为上周一至周日 |
| `{{role}}` | ❌ 否 | 用户声明或推断 | 从 `角色：XXX` 提取，未声明则按第一节规则推断 | 按 1.2 规则自动推断 |
| `{{summary_responsible}}` | ✅ 是 | issues.csv | Assignee = 本人的 Issue 列表，格式见下方 | 空列表（无负责任务时输出空） |
| `{{summary_followup}}` | ✅ 是 | issues.csv | Comment/Watcher/Reporter 含本人的 Issue 列表，格式见下方 | 空列表（无跟进内容时输出空） |
| `{{summary_development}}` | ✅ 是 | issues.csv + commits.json | Assignee = 本人且有关联 Commit 的 Issue 列表（仅技术角色） | 技术角色必须填写，产品角色输出空 |
| `{{plan_next}}` | ❌ 否 | issues.csv | Status = 进行中/待处理 的本人 Issue | 可为空 |
| `{{notes}}` | ❌ 否 | 用户补充 | 用户明确补充的其他事项 | 可为空 |

#### 4.3.2 各分类区块的输出格式

每个分类区块内的条目必须严格按以下格式输出：

**负责任务 / 开发项 / 跟进内容 条目格式**：
```
- {Issue编号}: {标题}（{状态标签}）
```
- `Issue编号`：直接使用 CSV 中 `Issue key` 字段，如 `PROJ-123`
- `标题`：直接使用 CSV 中 `Summary` 字段，不做任何改写
- `状态标签`：根据 3.3 状态映射表转换，如 `✅ 已完成` / `🔄 进行中` / `📋 待处理`

**开发项额外格式**（在技术/开发角色报告的「开发项」中）：
```
- {Issue编号}: {标题}（{状态标签}）
  代码：{commit message 摘要}
```
- `commit message 摘要`：取 commits.json 中匹配 commit 的 `message` 字段，截取前 50 个字符

**跟进内容额外格式**（所有角色报告的「跟进内容」中）：
```
- {Issue编号}: {跟进说明}（{跟进类型}，负责人：{原Assignee}）
```
- `跟进说明`：提取本人评论中与本人相关的关键句；若为 Watcher/Reporter 类型，可用 Issue 的 Summary
- `跟进类型`：直接使用 `Comment` / `Watcher` / `Reporter` 文本
- `原Assignee`：填写该 Issue 的实际 Assignee 姓名

#### 4.3.3 完整变量替换示例

**输入**：
```
姓名：蛋仔
角色：开发人员
模板：企业微信
```
**issues.csv 中匹配到的数据**：

| Issue key | Summary | Assignee | Status | Type |
|---|---|---|---|---|
| PROJ-123 | 修复用户登录异常 | 蛋仔 | Done | Bug |
| PROJ-456 | 优化订单查询性能 | 蛋仔 | In Progress | Task |
| PROJ-789 | 添加数据导出功能 | 张三 | Done | Story |

**commits.json 中匹配到的数据**：

| Commit message | Issue |
|---|---|
| `fix(user): 修复登录空指针问题` | PROJ-123 |

**生成的变量替换**：
```
{{name}}          → 蛋仔
{{date_range}}    → 2026-05-19 ~ 2026-05-25（推断）
{{summary_development}}  → - PROJ-123: 修复用户登录异常（✅ 已完成）
                           代码：fix(user): 修复登录空指针问题
{{summary_responsible}} → - PROJ-456: 优化订单查询性能（🔄 进行中）
{{summary_followup}}    → - PROJ-789: 添加数据导出功能（✅ 已完成，负责人：张三）
```

#### 4.3.4 常见错误警告

| 错误行为 | 正确做法 |
|---|---|
| ❌ 直接输出 `{{name}}` 占位符 | ✅ 替换为用户声明的姓名 |
| ❌ 跳过读取模板文件，自行编写格式 | ✅ 必须读取 `templates/wechat_work_weekly.md` 并按其结构输出 |
| ❌ 用 Issue 编号生成标题 | ✅ 直接使用 CSV 中的 `Summary` 字段 |
| ❌ 状态直接写英文/中文原文 | ✅ 必须按 3.3 映射表转换为带 emoji 的标签 |
| ❌ 开发项未关联 Commit 就填入 | ✅ 仅当 Issue 有关联 Commit 时才填入「开发项」，否则填入「负责任务」 |
| ❌ 跟进内容不标注原负责人 | ✅ 格式必须包含 `（负责人：XXX）` |

---

## 五、边界情况处理

| 场景 | 处理方式 |
|---|---|
| 无 commits.json | 使用产品/项目角色模板 |
| 姓名匹配失败 | 提示用户确认姓名或提供姓名变体 |
| Comment 字段缺失 | 仅使用 Assignee 筛选 |
| Issue 无关联 Commit | 归类为「负责任务」而非「开发项」 |
| Commit 无关联 Issue | 作为独立开发项，从 message 描述功能 |
| 用户未声明模板 | 使用 `templates/default_weekly.md`（通用周报） |
| 用户只说平台不说周期 | 默认按**周报**处理 |
| 用户只说周期不说平台 | 默认使用**通用**模板 |
| 用户声明的模板不存在 | 提示用户选择内置模板之一 |
| 模板文件读取失败 | 回退到 markdown 代码块输出报告内容 |

---

## 六、执行流程

```
1. 接收用户请求，提取参数：姓名、角色、模板、时间范围
2. 读取 issues.csv，识别用户姓名匹配的 Issue
3. 若提供 commits.json，读取并尝试与 Issue 匹配
4. 按角色分类：开发项/负责任务/跟进内容
5. 按模板格式生成报告
6. 输出报告，等待用户确认或调整
```