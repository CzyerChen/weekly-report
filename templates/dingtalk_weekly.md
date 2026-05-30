# {{name}} 周报

**汇报人**：{{name}}
**日期**：{{date_range}}
**角色**：{{role}}

==========

**一、本周工作完成情况**

{{#each completedTasks}}
✅ {{issueKey}} {{title}}
{{description}}
{{/each}}

**二、本周进行中工作**

{{#each inProgressTasks}}
🔄 {{issueKey}} {{title}} - {{progress}}
{{description}}
{{/each}}

**三、下周工作计划**

{{#each nextWeekTasks}}
📋 {{issueKey}} {{title}}
{{description}}
{{/each}}

**四、风险与问题**

{{riskIssues}}

**五、需要的支持**

{{supportNeeded}}

==========

日报链接：{{dailyReportLink}}
周报系统：{{reportSystemUrl}}
