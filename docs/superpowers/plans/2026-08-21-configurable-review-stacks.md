# Configurable Review Stacks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将代码走读收敛为通用入口 + 项目级技术栈注册表，并把 Qt C++/QML 的专项编排、检查项和经验沉淀放回各自 skill。

**Architecture:** `edanspec-code-review` 只负责确定范围、读取 `.edan-dev/review-stack.yaml`、执行通用走读和按配置调用专项 skill。配置只描述匹配规则、skill 名称和项目级补充说明；Qt 规则与流程留在 `skills/qt-cpp-review/`、`skills/qt-qml-review/`，不进入通用入口。缺少配置时只执行通用走读，配置错误或已启用专项无法执行时结论为 `INCOMPLETE`。

**Tech Stack:** Markdown skills, YAML configuration, Python/pytest contract tests, existing offline bundle builder.

---

## 文件边界

- `skills/edanspec-code-review/SKILL.md`：通用走读入口、配置加载、专项调用协议和通用状态模型。
- `skills/edanspec-code-review/reviewer-agent.md`：通用 reviewer 的四维职责；不得包含任何技术栈专属规则。
- `skills/edanspec-code-review/reviews/review-report-template.md`：通用阶段表和可扩展 `specialists` 结果表。
- `.edan-dev/review-stack.yaml`：当前项目启用的技术栈注册表，包含 Qt C++ 与 Qt QML 两项。
- `skills/qt-cpp-review/SKILL.md`、`skills/qt-qml-review/SKILL.md`：各自专项走读的入口和执行阶段。
- `skills/qt-cpp-review/references/review-workflow.md`、`skills/qt-qml-review/references/review-workflow.md`：专项走读编排顺序、输入边界和报告要求。
- `skills/qt-cpp-review/references/lessons-learned.md`、`skills/qt-qml-review/references/lessons-learned.md`：后续沉淀的专项注意事项；通用规则成熟后再晋升到 checklist。
- `.edan-dev/review-notes/qt-cpp.md`、`.edan-dev/review-notes/qt-qml.md`：项目/团队特有补充，通过配置的 `guidance` 字段传递，不修改官方 skill 规则。
- `tests/test_review_stack_contract.py`：配置、通用调度协议、专项 skill 资源和失败语义的契约测试。
- `scripts/build_offline_bundles.py`、`tests/test_offline_bundle_builder.py`：保持平台无关的资源复制与 manifest 校验，删除 Qt 专属分支。
- `.edan-dev/feature/20260813134142-qt-review-skill-integration/{proposal.md,design.md,specs/qt-review-integration-spec.md}`：把已有 Qt 方案文档改为注册表架构，避免设计文档与实现漂移。

## Task 1: 锁定项目级注册表契约

**Files:**
- Create: `.edan-dev/review-stack.yaml`
- Create: `tests/test_review_stack_contract.py`

- [ ] **Step 1: Write the failing contract tests**

  测试读取 `.edan-dev/review-stack.yaml` 和 skill 文档，验证：两个启用项的 `id` 分别为 `qt-cpp`、`qt-qml`；`skill` 分别指向 `qt-cpp-review`、`qt-qml-review`；每项有 `match`；通用 skill 明确读取 `review-stack.yaml`、始终执行 generic reviewer，并使用 `specialists` 状态；缺失配置时只走通用审查，配置/专项失败时使用 `INCOMPLETE`。

- [ ] **Step 2: Run the contract tests to verify RED**

  Run: `python -m pytest -q tests/test_review_stack_contract.py`

  Expected: FAIL because the project registry, generic protocol text, and specialist workflow references do not yet exist.

- [ ] **Step 3: Add the minimal registry**

  `.edan-dev/review-stack.yaml` 使用以下稳定字段，不把检查清单正文写进配置：

  ```yaml
  version: 1
  stacks:
    - id: qt-cpp
      enabled: true
      skill: qt-cpp-review
      match:
        extensions: [.cpp, .cc, .cxx, .h, .hh, .hpp]
        content_any:
          - '#include\\s*[<"](?:Qt[^>"]+|Q[A-Z]\\w*)'
          - '\\bQ_OBJECT\\b'
          - '\\bQ_PROPERTY\\b'
          - '\\bQAbstractItemModel\\b'
        build_any:
          - 'find_package\\s*\\(\\s*Qt6'
          - '\\bqt_add_executable\\b'
          - '\\bqt_add_qml_module\\b'
      guidance:
        - .edan-dev/review-notes/qt-cpp.md
    - id: qt-qml
      enabled: true
      skill: qt-qml-review
      match:
        extensions: [.qml, .qmltypes]
      guidance:
        - .edan-dev/review-notes/qt-qml.md
  ```

- [ ] **Step 4: Run the contract tests to verify GREEN**

  Run: `python -m pytest -q tests/test_review_stack_contract.py`

  Expected: PASS for registry shape and the completed routing contract.

- [ ] **Step 5: Commit the registry contract**

  ```bash
  git add .edan-dev/review-stack.yaml tests/test_review_stack_contract.py
  git commit -m "feat(review): add configurable review stack registry"
  ```

## Task 2: Replace Qt-specific code-review routing with generic dispatch

**Files:**
- Modify: `skills/edanspec-code-review/SKILL.md`
- Modify: `skills/edanspec-code-review/reviewer-agent.md`
- Modify: `skills/edanspec-code-review/reviews/review-report-template.md`
- Modify: `skills/edanspec-task-implement/SKILL.md`
- Modify: `README.md`
- Delete: `skills/edanspec-code-review/scripts/classify_qt_scope.py`
- Delete: `skills/edanspec-code-review/scripts/aggregate_reports.py`
- Test: `tests/test_review_stack_contract.py`

- [ ] **Step 1: Extend the failing contract tests for generic dispatch**

  Add assertions that the generic skill describes this sequence: freeze `allFiles`, read `.edan-dev/review-stack.yaml`, always run generic review, match enabled stacks by `extensions`/`content_any`/`build_any`, pass only matched files and `guidance` files to the configured `skill`, and record `specialists.<id>` status. Assert the generic docs contain no hardcoded `qtCppFiles`, `qmlFiles`, `qtCppReview`, or `qmlReview` protocol fields.

- [ ] **Step 2: Run the focused tests to verify RED**

  Run: `python -m pytest -q tests/test_review_stack_contract.py`

  Expected: FAIL because the current `code-review` skill still contains Qt-specific routing and reports.

- [ ] **Step 3: Rewrite the generic protocol**

  Replace the Qt section with a platform-neutral protocol. The route instructions must state:

  ```text
  1. 固化 allFiles。
  2. 读取 .edan-dev/review-stack.yaml；不存在时 specialist 阶段为 not-applicable。
  3. generic reviewer 始终审查 allFiles。
  4. 对每个 enabled stack，按 match 规则计算 matchedFiles；只把 matchedFiles 和 guidance 传给 stack.skill。
  5. 专项 skill 自己决定 lint、深度分析、报告格式；通用入口不复制专项规则。
  6. 统一报告使用 genericReview、specialists、conclusion；专项失败或配置错误为 INCOMPLETE。
  ```

  将报告模板的 Qt 固定列改成 `specialists.<stack-id>` 可重复表；将 task-implement 的门禁说明泛化为“任一启用专项阶段”；README 只描述“可配置技术栈专项走读”。

- [ ] **Step 4: Remove obsolete Qt-specific helpers**

  删除两个 Qt 命名的 Python helper。由于当前 skill 是 Agent 编排而非应用运行时，不引入新的通用解析器；YAML 由执行 skill 按契约读取，保持最小实现和清晰边界。

- [ ] **Step 5: Run focused tests to verify GREEN**

  Run: `python -m pytest -q tests/test_review_stack_contract.py`

  Expected: PASS with generic routing contract and no Qt-specific protocol fields in the generic docs.

- [ ] **Step 6: Commit the generic dispatch change**

  ```bash
  git add skills/edanspec-code-review skills/edanspec-task-implement README.md tests/test_review_stack_contract.py
  git rm skills/edanspec-code-review/scripts/classify_qt_scope.py skills/edanspec-code-review/scripts/aggregate_reports.py
  git commit -m "refactor(code-review): dispatch configurable specialist stacks"
  ```

## Task 3: Move Qt C++ and QML orchestration into specialist skills

**Files:**
- Modify: `skills/qt-cpp-review/SKILL.md`
- Modify: `skills/qt-qml-review/SKILL.md`
- Create: `skills/qt-cpp-review/references/review-workflow.md`
- Create: `skills/qt-qml-review/references/review-workflow.md`
- Create: `skills/qt-cpp-review/references/lessons-learned.md`
- Create: `skills/qt-qml-review/references/lessons-learned.md`
- Create: `.edan-dev/review-notes/qt-cpp.md`
- Create: `.edan-dev/review-notes/qt-qml.md`
- Test: `tests/test_review_stack_contract.py`

- [ ] **Step 1: Add failing specialist asset tests**

  Assert each specialist `SKILL.md` links to its own `references/review-workflow.md`, `references/lessons-learned.md`, and existing checklist/lint resources; assert Qt C++ workflow contains scope, phase order, framework-mode confirmation, and read-only rules; assert QML workflow contains Python lint, optional `qmllint`, six analysis domains, and read-only rules.

- [ ] **Step 2: Run tests to verify RED**

  Run: `python -m pytest -q tests/test_review_stack_contract.py`

  Expected: FAIL because the new workflow and notes files do not exist.

- [ ] **Step 3: Add specialist workflow documents**

  Keep `SKILL.md` as the discoverable entrypoint with a short phase list and move detailed orchestration to `references/review-workflow.md`. Add an empty-but-explicit notes template with sections `新增注意事项`, `证据`, `适用范围`, `状态`; do not copy project notes into the official Qt checklist.

- [ ] **Step 4: Add project guidance files**

  Create `.edan-dev/review-notes/qt-cpp.md` and `.edan-dev/review-notes/qt-qml.md` with a short purpose statement and no speculative rules. Future confirmed project findings are appended there and passed through `guidance`.

- [ ] **Step 5: Run tests to verify GREEN**

  Run: `python -m pytest -q tests/test_review_stack_contract.py`

  Expected: PASS for both specialist skill contracts and guidance paths.

- [ ] **Step 6: Commit specialist boundaries**

  ```bash
  git add skills/qt-cpp-review skills/qt-qml-review .edan-dev/review-notes tests/test_review_stack_contract.py
  git commit -m "docs(review): isolate Qt specialist workflows and notes"
  ```

## Task 4: Remove platform-builder Qt special cases and update feature design

**Files:**
- Modify: `scripts/build_offline_bundles.py`
- Modify: `tests/test_offline_bundle_builder.py`
- Modify: `.edan-dev/feature/20260813134142-qt-review-skill-integration/proposal.md`
- Modify: `.edan-dev/feature/20260813134142-qt-review-skill-integration/design.md`
- Modify: `.edan-dev/feature/20260813134142-qt-review-skill-integration/specs/qt-review-integration-spec.md`

- [ ] **Step 1: Add a failing builder contract assertion**

  Assert the offline builder has no `QT_SKILL_FILES`, `qtCppFiles`, or `qmlFiles` special-case identifiers and still copies arbitrary `skills/` subdirectories unchanged into all platform stages.

- [ ] **Step 2: Run the builder tests to verify RED**

  Run: `python -m pytest -q tests/test_offline_bundle_builder.py`

  Expected: FAIL because the builder currently validates Qt-specific resources and install text.

- [ ] **Step 3: Remove only Qt-specific builder logic**

  Delete `QT_SKILL_FILES`, Qt-specific install instructions, and Qt-specific validation assertions. Retain generic skill frontmatter/path checks, manifest generation, archive extraction, and Claude-path leak checks; the existing root `skills/` copy automatically packages both Qt skills.

- [ ] **Step 4: Rewrite the feature documents**

  Replace direct Qt routing and three fixed statuses with the registry contract: `genericReview`, `specialists` keyed by stack id, and `INCOMPLETE` for invalid/failed enabled stages. Record that Qt C++ and QML are the initial config entries and Java/C# require only new skill + registry entries.

- [ ] **Step 5: Run builder and feature tests to verify GREEN**

  Run: `python -m pytest -q tests/test_offline_bundle_builder.py tests/test_review_stack_contract.py`

  Expected: PASS, with all three archives still manifest-valid and both Qt skill directories present through generic copying.

- [ ] **Step 6: Commit the packaging and design cleanup**

  ```bash
  git add scripts/build_offline_bundles.py tests/test_offline_bundle_builder.py .edan-dev/feature/20260813134142-qt-review-skill-integration
  git commit -m "refactor(packaging): keep specialist skills platform-neutral"
  ```

## Task 5: Full verification and PR update

**Files:**
- Test: `tests/test_review_stack_contract.py`
- Test: all existing `tests/` and `tests/context_browser_app.test.mjs`

- [ ] **Step 1: Run focused routing and builder tests**

  Run: `python -m pytest -q tests/test_review_stack_contract.py tests/test_offline_bundle_builder.py`

  Expected: PASS.

- [ ] **Step 2: Run the complete verification suite**

  Run: `python -m pytest -q`

  Expected: 0 failures.

  Run: `node --test tests/context_browser_app.test.mjs`

  Expected: 7 passing subtests.

- [ ] **Step 3: Build all offline bundles**

  Run: `python scripts/build_offline_bundles.py --repo-root . --output-dir <temporary-output-dir> --date-tag 20260821`

  Expected: Claude Code, OpenCode, and Kilo Code archives build, extract, and pass `MANIFEST.sha256` verification.

- [ ] **Step 4: Review the net diff**

  Run: `git diff upstream/main..HEAD --stat` and `git diff --check`.

  Confirm the net change has exactly two product concerns: CodeGraph project-context and configurable specialist review stacks; `.superpowers/`, `dist/`, and `deliverables/` remain unstaged.

- [ ] **Step 5: Push the cleanup commits and update the existing Draft PR**

  ```bash
  git push origin sync/upstream-20260723
  gh pr edit 1 --repo YuanLiChu/edan-spec --title "refactor: configurable project context and review stacks"
  ```

  Update the PR body with the registry design, Qt C++/QML initial entries, test counts, and the fact that no platform-specific Qt builder code remains.

## Self-review checklist

- Every requirement maps to a task: CodeGraph remains untouched by this refactor; generic review reads a project registry; both Qt skills retain independent orchestration; future notes have a project-local and reusable location; packaging remains generic; invalid enabled stacks cannot produce `APPROVE`.
- No step depends on `classify_qt_scope.py` or `aggregate_reports.py`; both are explicitly removed.
- `specialists.<stack-id>` is the only extensible report key; no later task reintroduces fixed `qtCppReview`/`qmlReview` fields.
- The default behavior is explicit: absent registry means generic-only review; present enabled stacks are mandatory stages.
