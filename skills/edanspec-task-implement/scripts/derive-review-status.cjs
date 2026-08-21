#!/usr/bin/env node
// derive-review-status.cjs — 从审查报告文件推导审查状态
// 跨平台：macOS / Windows / Linux（Node.js 标准库，零依赖）
// 用法:
//   node derive-review-status.cjs                                    # 扫描 EdanSpec/feature/ 下所有活跃 feature
//   node derive-review-status.cjs EdanSpec/feature/20260518-login    # 指定具体 feature 目录
// 输出: JSON 格式的审查状态到 stdout

const fs = require('fs');
const path = require('path');

const REVIEW_FILES = {
  codeReview: 'code-review-report.md',
  securityReview: 'security-review-report.md',
  verify: 'verify-report.md',
};

function parseReport(filePath) {
  // 解析审查报告文件，提取状态和 findings。
  // 返回: { status, lastRun, hasCritical, findings: { critical, important, suggestion } }
  // 文件不存在或无法解析时返回 null。
  if (!fs.existsSync(filePath) || !fs.statSync(filePath).isFile()) return null;

  const content = fs.readFileSync(filePath, 'utf-8');

  // 提取各严重度数量：匹配表格中的 CRITICAL/IMPORTANT/SUGGESTION 行
  // 格式: | CRITICAL | N | ...
  const criticalMatch = content.match(/\|\s*CRITICAL\s*\|\s*(\d+)\s*\|/);
  const importantMatch = content.match(/\|\s*IMPORTANT\s*\|\s*(\d+)\s*\|/);
  const suggestionMatch = content.match(/\|\s*SUGGESTION\s*\|\s*(\d+)\s*\|/);

  const critical = criticalMatch ? parseInt(criticalMatch[1], 10) : 0;
  const important = importantMatch ? parseInt(importantMatch[1], 10) : 0;
  const suggestion = suggestionMatch ? parseInt(suggestionMatch[1], 10) : 0;

  // 也尝试从报告表格中提取状态
  // 匹配结论行: | **结论** | APPROVE / REQUEST_CHANGES |
  const conclusionMatch = content.match(/\|\s*\*\*结论\*\*\s*\|\s*(\S+)/);
  let status;
  if (conclusionMatch) {
    const conclusion = conclusionMatch[1].trim();
    status = conclusion === 'APPROVE' ? 'passed' : 'failed';
  } else {
    status = critical === 0 ? 'passed' : 'failed';
  }

  // 提取最后运行时间（如果有）
  const lastRunMatch = content.match(/(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})/);
  const lastRun = lastRunMatch ? lastRunMatch[1] : null;

  return {
    status,
    lastRun,
    hasCritical: critical > 0,
    findings: { critical, important, suggestion },
  };
}

function derive(featureDir) {
  // 从 feature 目录下的审查报告文件推导审查状态
  const reviewStatus = {};
  for (const [gateName, filename] of Object.entries(REVIEW_FILES)) {
    const result = parseReport(path.join(featureDir, filename));
    reviewStatus[gateName] = result !== null
      ? result
      : {
          status: 'pending',
          lastRun: null,
          hasCritical: false,
          findings: { critical: 0, important: 0, suggestion: 0 },
        };
  }
  return reviewStatus;
}

function allCompleted(reviewStatus) {
  // 判断是否全部关卡通过
  for (const gate of Object.values(reviewStatus)) {
    if (gate.status !== 'passed' || gate.hasCritical) return false;
  }
  return true;
}

// 定位项目根目录：从脚本位置 (skills/edanspec-task-implement/scripts/) 向上 4 级
const SCRIPTS_DIR = __dirname;                          // .../skills/edanspec-task-implement/scripts
const SKILLS_DIR = path.resolve(SCRIPTS_DIR, '../..');  // .../skills
const PROJECT_ROOT = path.resolve(SKILLS_DIR, '../..'); // 项目根

function main() {
  const argv = process.argv.slice(2);

  if (argv.length > 0) {
    let arg = argv[0];
    if (!path.isAbsolute(arg)) arg = path.resolve(PROJECT_ROOT, arg);
    const featureDir = arg;
    if (!fs.existsSync(featureDir) || !fs.statSync(featureDir).isDirectory()) {
      console.log(JSON.stringify({ error: `目录不存在: ${featureDir}` }));
      process.exit(1);
    }
    const result = derive(featureDir);
    console.log(JSON.stringify({
      feature: path.basename(featureDir),
      reviewStatus: result,
      allPassed: allCompleted(result),
    }, null, 2));
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
      const reviewStatus = derive(featureDir);
      output[featureName] = { reviewStatus, allPassed: allCompleted(reviewStatus) };
    }
    console.log(JSON.stringify(output, null, 2));
  }
}

main();
