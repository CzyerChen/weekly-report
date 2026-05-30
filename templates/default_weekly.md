# {{name}} 周报

**日期范围**：{{date_range}}
**姓名**：{{name}}
**角色**：{{role}}

---

## 一、本周工作总结

### 1. 完成事项

{{#each completedItems}}
- **{{title}}** {{#if issueKey}}({{issueKey}}){{/if}}
  {{description}}
{{/each}}

### 2. 进行中事项

{{#each inProgressItems}}
- **{{title}}** {{#if issueKey}}({{issueKey}}){{/if}} - {{progress}}
  {{description}}
{{/each}}

### 3. 其他工作

{{otherWork}}

---

## 二、工作量统计

| 分类 | 数量 |
|------|------|
| 已完成 | {{stats.completed}} |
| 进行中 | {{stats.inProgress}} |
| 待处理 | {{stats.pending}} |

---

## 三、下周工作规划

{{#each nextWeekPlans}}
{{add @index 1}}. **{{title}}**
   - 目标：{{goal}}
   - 优先级：{{priority}}
{{/each}}

---

## 四、风险与挑战

{{risks}}

---

## 五、学习与成长

{{learning}}

---

## 六、其他

{{others}}
