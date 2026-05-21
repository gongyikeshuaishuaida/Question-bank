---
title: Dataview 查询示例
type: reference
---

# Dataview 查询示例

> [!note] 前提条件
> 需要安装 Dataview 插件，并在设置中启用 JavaScript 查询。

以下查询以 frontmatter 中的 `id` 字段识别题目，不依赖题目所在文件夹。

---

## 1. 显示所有题目

```dataview
TABLE
  id AS "ID",
  题型 AS "题型",
  难度 AS "难度",
  状态 AS "状态",
  知识点 AS "知识点",
  完成次数 AS "完成",
  正确率 AS "正确率",
  图片核验 AS "图片核验"
FROM ""
WHERE id
SORT id ASC
```

---

## 2. 按题型筛选

```dataview
TABLE
  id AS "ID",
  难度 AS "难度",
  状态 AS "状态",
  来源 AS "来源"
FROM ""
WHERE id AND 题型 = "选择题"
SORT id ASC
```

```dataview
TABLE
  id AS "ID",
  难度 AS "难度",
  状态 AS "状态",
  来源 AS "来源"
FROM ""
WHERE id AND 题型 = "填空题"
SORT id ASC
```

---

## 3. 按知识点筛选

```dataview
TABLE
  id AS "ID",
  题型 AS "题型",
  难度 AS "难度",
  状态 AS "状态"
FROM ""
WHERE id AND contains(知识点, "03python基础")
SORT id ASC
```

---

## 4. 未练习题目

```dataview
TABLE
  id AS "ID",
  题型 AS "题型",
  难度 AS "难度",
  知识点 AS "知识点"
FROM ""
WHERE id AND 状态 = "未练习"
SORT id ASC
```

---

## 5. 图片待核验

```dataview
TABLE
  id AS "ID",
  题型 AS "题型",
  知识点 AS "知识点",
  来源 AS "来源"
FROM ""
WHERE id AND 图片核验 = "待核验"
SORT id ASC
```

---

## 6. 需复习或错题

```dataview
TABLE
  id AS "ID",
  题型 AS "题型",
  知识点 AS "知识点",
  完成次数 AS "完成",
  正确率 AS "正确率",
  错题原因 AS "错题原因"
FROM ""
WHERE id AND (状态 = "需复习" OR 状态 = "错题")
SORT id ASC
```

---

## 7. 各题型数量

```dataview
TABLE
  length(rows) AS "题目数量"
FROM ""
WHERE id
GROUP BY 题型
```

---

## 8. 各知识点题目数

```dataview
TABLE
  length(rows) AS "题目数量"
FROM ""
FLATTEN 知识点 AS k
WHERE id
GROUP BY k
SORT k ASC
```

---

## 9. 练习进度统计

```dataviewjs
const pages = dv.pages()
  .where(p => p.id && p.题型);

const total = pages.length;
const completed = pages.where(p => p.完成次数 > 0).length;
const accuracies = pages.where(p => p.完成次数 > 0)
  .map(p => Number(p.正确率))
  .where(v => !Number.isNaN(v));
const avgAccuracy = accuracies.length
  ? accuracies.reduce((a, b) => a + b, 0) / accuracies.length * 100
  : 0;

dv.paragraph(`**题库统计**
- 总题目数：${total}
- 已练习：${completed} (${total ? (completed / total * 100).toFixed(1) : 0}%)
- 平均正确率：${avgAccuracy.toFixed(1)}%`);
```
