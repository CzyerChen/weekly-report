# 日报
**姓名**：{{name}}
**日期**：{{date}}
**角色**：{{role}}

---

## 今日功能总结

{{#if hasDevelopmentItems}}
### 一、开发项（Assignee + 代码提交）

{{#each developmentItems}}
**{{issueKey}} {{title}}** - {{typeEmoji}} {{status}}
{{#if commitInfo}}
- 代码：{{commitInfo}}
{{/if}}
{{description}}
---
{{/each}}
{{/if}}

{{#if hasResponsibleTasks}}
### 二、负责任务（Assignee = 本人）

{{#each responsibleTasks}}
**{{issueKey}} {{title}}** - {{typeEmoji}} {{status}}
{{description}}
---
{{/each}}
{{/if}}

{{#if hasFollowUpItems}}
### 三、跟进内容（Comment/Watcher/Reporter）

{{#each followUpItems}}
**{{issueKey}} {{title}}** - {{typeEmoji}} {{status}}
- 类型：{{followUpType}}
{{#if originalAssignee}}
- 负责人：{{originalAssignee}}
{{/if}}
{{description}}
---
{{/each}}
{{/if}}

{{#if hasCommits}}

---

## 明日工作计划

{{#each nextWeekPlans}}
{{add @index 1}}. **{{title}}**：{{description}}
{{/each}}

---

## 其他事项

{{otherNotes}}
