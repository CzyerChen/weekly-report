# {{name}} 日报

**汇报人**：{{name}}
**日期**：{{date}}
**角色**：{{role}}

==========

**一、今日完成工作**

{{#each completedTasks}}
✅ {{issueKey}} {{title}}
{{description}}
{{/each}}

**二、今日未完成工作**

{{#each inProgressTasks}}
🔄 {{issueKey}} {{title}} - {{progress}}
{{description}}
{{/each}}

**三、需协调工作**

{{supportNeeded}}

