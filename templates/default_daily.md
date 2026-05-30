# {{name}} 日报

**日期**：{{date}}
**姓名**：{{name}}
**角色**：{{role}}

---

## 今日工作

{{#each todayTasks}}
### {{category}}
{{#each items}}
- {{title}} {{#if issueKey}}({{issueKey}}){{/if}}
  {{description}}
{{/each}}
{{/each}}

---

## 明日计划

{{#each tomorrowTasks}}
- {{title}} {{#if issueKey}}({{issueKey}}){{/if}}
  {{description}}
{{/each}}

---

## 问题与思考

{{issues}}

---

## 备注

{{notes}}
