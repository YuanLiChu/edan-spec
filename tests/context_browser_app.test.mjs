import assert from "node:assert/strict";
import fs from "node:fs";
import { test } from "node:test";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const {
  buildDocumentsFromFiles,
  discoverDocumentSources,
  estimateMermaidMinWidth,
  isLargeMermaidDiagram,
  mermaidDiagramKind,
  renderMarkdown,
  stripCommonRoot,
} = require("../context-browser/app.js");

test("discovers project, module, and flow documents from a selected folder", async () => {
  const docs = await buildDocumentsFromFiles([
    { path: "project.md", text: "# Demo Project\n\n[Admission](modules/admission/module.md)" },
    {
      path: "modules/admission/module.md",
      text: "# Module: Admission\n\n| Flow | Link |\n|------|------|\n| Create | [flow](flows/create.md) |",
    },
    { path: "modules/admission/flows/create.md", text: "# Create Admission\n\nFlow body." },
  ]);

  assert.deepEqual(docs.map((doc) => doc.kind), ["project", "module", "flow"]);
  assert.equal(docs[0].children[0], "module:admission");
  assert.equal(docs[1].children[0], "flow:admission:create");
  assert.match(docs[1].html, /href="#flow:admission:create"/);
});

test("supports looser module.md and flow.md names outside canonical modules folder", () => {
  const sources = discoverDocumentSources([
    { path: "project.md", text: "# Project" },
    { path: "billing/module.md", text: "# Billing" },
    { path: "billing/flow.md", text: "# Billing Flow" },
  ]);

  assert.deepEqual(sources.map((source) => source.kind), ["project", "module", "flow"]);
  assert.equal(sources[1].module, "billing");
  assert.equal(sources[2].parent, "module:billing");
});

test("renders headings, tables, and mermaid source without external dependencies", () => {
  const rendered = renderMarkdown(
    "# Title\n\n| A | B |\n|---|---|\n| x | y |\n\n```mermaid\ngraph LR\nA-->B\n```",
  );

  assert.equal(rendered.headings[0].text, "Title");
  assert.match(rendered.html, /<table>/);
  assert.match(rendered.html, /Mermaid flowchart diagram/);
  assert.match(rendered.html, /diagram-body/);
});

test("strips selected folder root from webkitRelativePath style paths", () => {
  const files = stripCommonRoot([
    { path: "selected-context/project.md", text: "# Project" },
    { path: "selected-context/modules/a/module.md", text: "# A" },
  ]);

  assert.deepEqual(files.map((file) => file.path), ["project.md", "modules/a/module.md"]);
});

test("treats the alarm event pipeline sequence diagram as a wide readable diagram", () => {
  const markdown = fs.readFileSync("C:/work/context/modules/alarmmanager/flows/alarm-event-pipeline.md", "utf8");
  const diagram = markdown.match(/```mermaid\n([\s\S]*?)```/)?.[1] || "";
  const rendered = renderMarkdown(markdown);

  assert.equal(mermaidDiagramKind(diagram), "sequence");
  assert.equal(isLargeMermaidDiagram(diagram), true);
  assert.ok(estimateMermaidMinWidth(diagram, 640) >= 1800);
  assert.match(rendered.html, /diagram-sequence diagram-large/);
  assert.match(rendered.html, /Wide view/);
});

test("wide diagram view keeps the inner viewport scrollable in Firefox flex layout", () => {
  const css = fs.readFileSync("context-browser/styles.css", "utf8");

  assert.match(css, /\.diagram-expanded \.diagram-body\s*\{[\s\S]*?flex: 1 1 0;[\s\S]*?min-height: 0;[\s\S]*?overflow: hidden;/);
  assert.match(css, /\.diagram-expanded \.diagram-viewport\s*\{[\s\S]*?height: 100%;[\s\S]*?min-width: 0;[\s\S]*?overflow: auto;/);
});

test("default diagram view fits the reader while wide view can expand", () => {
  const css = fs.readFileSync("context-browser/styles.css", "utf8");

  assert.match(css, /\.diagram-block svg\s*\{[\s\S]*?max-width: 100%;[\s\S]*?min-width: 0;[\s\S]*?width: 100%;/);
  assert.match(css, /\.diagram-expanded svg\s*\{[\s\S]*?max-width: none;/);
  assert.doesNotMatch(css, /\.diagram-large svg\s*\{[\s\S]*?min-width:/);
});
