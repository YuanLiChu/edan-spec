#!/usr/bin/env node
// derive-task-status.cjs — 从文件系统事实推导 taskGraph 状态
// 跨平台：macOS / Windows / Linux（Node.js 标准库，零依赖）
// 用法:
//   node derive-task-status.cjs                                    # 扫描 EdanSpec/feature/ 下所有活跃 feature
//   node derive-task-status.cjs EdanSpec/feature/20260518-login    # 指定具体 feature 目录
// 输出: JSON 格式的 taskGraph 数组到 stdout

const fs = require('fs');
const path = require('path');

function readTasksFile(featureDir) {
  const tasksPath = path.join(featureDir, 'tasks.md');
  if (!fs.existsSync(tasksPath) || !fs.statSync(tasksPath).isFile()) return null;
  return fs.readFileSync(tasksPath, 'utf-8');
}

function parseTasksFromMarkdown(content) {
  // 解析 tasks.md 中的任务节点。提取: id, title, dependsOn, files, increments[]
  const tasks = [];

  // 匹配 Task-XXX 标题: ### Task-001：xxx 或 ### Task-001: xxx
  const taskMatches = [...content.matchAll(/^###\s+(Task-\d+)\s*[:：]\s*(.+)$/gm)];

  for (let t = 0; t < taskMatches.length; t++) {
    const m = taskMatches[t];
    const taskId = m[1];
    const title = m[2].trim();
    const start = m.index + m[0].length;

    // 找到下一个 task 标题或文件结尾作为本任务范围
    const next = t + 1 < taskMatches.length ? taskMatches[t + 1] : null;
    const taskBlock = next ? content.slice(start, next.index) : content.slice(start);

    // 解析依赖（匹配第一个）
    const depMatch = taskBlock.match(/\*\*前置依赖\*\*[:：]\s*(.+)$/m);
    let deps = [];
    if (depMatch) {
      const depText = depMatch[1].trim();
      if (!['无', 'none', ''].includes(depText.toLowerCase())) {
        deps = depText.split(/[，,;；]/).map((d) => d.trim()).filter((d) => d.length > 0);
      }
    }

    // 解析涉及文件（匹配第一个块）
    const filesMatch = taskBlock.match(/\*\*涉及文件\*\*[:：]\s*\n((?:- .+\n?)+)/m);
    let files = [];
    if (filesMatch) {
      files = filesMatch[1]
        .trim()
        .split('\n')
        .filter((line) => line.trim().startsWith('- '))
        .map((line) => line.trim().replace(/^- /, '').split(' ')[0].trim().replace(/^`|`$/g, ''));
    }

    // 解析增量 checkbox
    const increments = [];
    for (const inc of taskBlock.matchAll(/- \[([ x])\]\s+\*\*增量\s+(\d+)\*\*[:：]\s*(.*)/gm)) {
      increments.push({
        number: parseInt(inc[2], 10),
        description: inc[3].trim(),
        done: inc[1] === 'x',
      });
    }

    tasks.push({ id: taskId, title, dependsOn: deps, files, increments });
  }
  return tasks;
}

function computeTaskStatuses(tasks) {
  // 基于 checkbox 事实和依赖关系计算每个任务的状态
  const doneIds = new Set();
  const result = [];

  for (const task of tasks) {
    const total = task.increments.length;
    const completed = task.increments.filter((i) => i.done).length;

    // 依赖是否全部 done
    const depsMet = task.dependsOn.every((d) => doneIds.has(d));

    let status;
    if (total > 0 && completed === total) {
      status = 'done';
      doneIds.add(task.id);
    } else if (completed > 0) {
      status = 'in_progress';
    } else if (depsMet) {
      status = 'ready';
    } else {
      status = 'pending';
    }

    result.push({
      id: task.id,
      title: task.title,
      status,
      dependsOn: task.dependsOn,
      files: task.files,
      currentIncrement: completed,
      totalIncrements: total,
      lastModified: new Date().toISOString().replace(/\.\d{3}Z$/, ''),
    });
  }
  return result;
}

function derive(featureDir) {
  const content = readTasksFile(featureDir);
  if (content === null) return [];
  return computeTaskStatuses(parseTasksFromMarkdown(content));
}

// 定位项目根目录：从脚本位置 (skills/edanspec-task-implement/scripts/) 向上 4 级
const SCRIPTS_DIR = __dirname;                          // .../skills/edanspec-task-implement/scripts
const SKILLS_DIR = path.resolve(SCRIPTS_DIR, '../..');  // .../skills
const PROJECT_ROOT = path.resolve(SKILLS_DIR, '../..'); // 项目根

function main() {
  const argv = process.argv.slice(2);

  if (argv.length > 0) {
    let arg = argv[0];
    // 支持相对路径（相对于项目根）和绝对路径
    if (!path.isAbsolute(arg)) arg = path.resolve(PROJECT_ROOT, arg);
    console.log(JSON.stringify(derive(arg), null, 2));
  } else {
    const root = path.join(PROJECT_ROOT, 'EdanSpec', 'feature');
    if (!fs.existsSync(root) || !fs.statSync(root).isDirectory()) {
      console.log(JSON.stringify({ error: 'EdanSpec/feature/ 目录不存在' }));
      process.exit(1);
    }
    const output = {};
    for (const featureName of fs.readdirSync(root).sort()) {
      const featureDir = path.join(root, featureName);
      if (!fs.statSync(featureDir).isDirectory()) continue;
      output[featureName] = derive(featureDir);
    }
    console.log(JSON.stringify(output, null, 2));
  }
}

main();
