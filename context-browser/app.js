let state = {
  documents: [],
  activeId: "",
};

const dom = typeof document === "undefined" ? null : {
  title: document.getElementById("project-title"),
  pickFolder: document.getElementById("pick-folder"),
  folderInput: document.getElementById("folder-input"),
  search: document.getElementById("search"),
  tree: document.getElementById("tree"),
  breadcrumbs: document.getElementById("breadcrumbs"),
  reader: document.getElementById("reader"),
  details: document.getElementById("details"),
};

async function buildDocumentsFromFiles(files) {
  const normalizedFiles = stripCommonRoot(files.map((file) => ({
    path: normalizePath(file.path || file.webkitRelativePath || file.name),
    text: file.text,
  })));
  const sources = normalizedFiles
    .filter((file) => file.path.toLowerCase().endsWith(".md"));
  const sourceMap = new Map(sources.map((file) => [file.path, file]));
  const documentSources = discoverDocumentSources(sources);
  const linkMap = new Map(documentSources.map((source) => [source.path, source.id]));
  const documents = documentSources.map((source) => loadDocument(source, sourceMap, linkMap));
  return attachChildren(documents);
}

function discoverDocumentSources(files) {
  const sources = [];
  const project = findProject(files);
  if (project) {
    sources.push({ path: project.path, kind: "project", id: "project", module: null, parent: null });
  }

  const modules = files
    .filter((file) => basename(file.path).toLowerCase() === "module.md")
    .sort((a, b) => a.path.localeCompare(b.path));
  for (const file of modules) {
    const moduleName = moduleNameFromPath(file.path);
    sources.push({
      path: file.path,
      kind: "module",
      id: `module:${slugId(moduleName)}`,
      module: moduleName,
      parent: project ? "project" : null,
    });
  }

  const moduleByPath = new Map(sources.filter((source) => source.kind === "module").map((source) => [source.module, source.id]));
  const flows = files
    .filter((file) => isFlowMarkdown(file.path))
    .sort((a, b) => a.path.localeCompare(b.path));
  for (const file of flows) {
    const moduleName = moduleNameFromFlowPath(file.path);
    const flowName = basename(file.path).replace(/\.md$/i, "");
    sources.push({
      path: file.path,
      kind: "flow",
      id: uniqueId(`flow:${slugId(moduleName)}:${slugId(flowName)}`, sources),
      module: moduleName,
      parent: moduleByPath.get(moduleName) || (project ? "project" : null),
    });
  }
  return sources;
}

function renderMarkdown(markdown, currentPath = "", linkMap = new Map()) {
  const lines = markdown.replace(/^\uFEFF/, "").split(/\r?\n/);
  const parts = [];
  const headings = [];
  let index = 0;
  let inList = false;
  while (index < lines.length) {
    const line = lines[index];
    if (line.startsWith("```")) {
      const result = readCodeBlock(lines, index);
      parts.push(renderCodeBlock(result.block, result.language));
      index = result.nextIndex;
      continue;
    }
    if (isTableStart(lines, index)) {
      const result = readTable(lines, index);
      parts.push(renderTable(result.rows, currentPath, linkMap));
      index = result.nextIndex;
      continue;
    }
    const heading = /^(#{1,6})\s+(.+)$/.exec(line);
    if (heading) {
      if (inList) {
        parts.push("</ul>");
        inList = false;
      }
      const level = heading[1].length;
      const text = heading[2].trim();
      const anchor = slugId(text);
      headings.push({ level, text, anchor });
      parts.push(`<h${level} id="${anchor}">${escapeInline(text, currentPath, linkMap)}</h${level}>`);
    } else if (/^\s*[-*]\s+/.test(line)) {
      if (!inList) {
        parts.push("<ul>");
        inList = true;
      }
      parts.push(`<li>${escapeInline(line.replace(/^\s*[-*]\s+/, "").trim(), currentPath, linkMap)}</li>`);
    } else if (!line.trim()) {
      if (inList) {
        parts.push("</ul>");
        inList = false;
      }
    } else {
      if (inList) {
        parts.push("</ul>");
        inList = false;
      }
      parts.push(`<p>${escapeInline(line.trim(), currentPath, linkMap)}</p>`);
    }
    index += 1;
  }
  if (inList) {
    parts.push("</ul>");
  }
  return { html: parts.join("\n"), headings };
}

function normalizePath(path) {
  return String(path || "").replace(/\\/g, "/").replace(/^\/+/, "");
}

function stripCommonRoot(files) {
  if (!files.length || files.some((file) => file.path.split("/").length < 2)) {
    return files;
  }
  const [root] = files[0].path.split("/");
  if (!root || files.some((file) => file.path.split("/")[0] !== root)) {
    return files;
  }
  return files.map((file) => ({ ...file, path: file.path.split("/").slice(1).join("/") }));
}

function findProject(files) {
  return files.find((file) => file.path.toLowerCase() === "project.md")
    || files.find((file) => basename(file.path).toLowerCase() === "project.md");
}

function loadDocument(source, sourceMap, linkMap) {
  const file = sourceMap.get(source.path);
  const text = typeof file?.text === "string" ? file.text.replace(/^\uFEFF/, "") : "";
  const rendered = renderMarkdown(text, source.path, linkMap);
  const title = extractTitle(text, basename(source.path).replace(/\.md$/i, ""));
  return {
    id: source.id,
    kind: source.kind,
    title,
    path: source.path,
    module: source.module,
    parent: source.parent,
    children: [],
    html: rendered.html || `<p class="empty">空文档。</p>`,
    headings: rendered.headings,
    searchText: `${title} ${source.path} ${plainText(text)}`.toLowerCase(),
  };
}

function attachChildren(documents) {
  const byId = new Map(documents.map((doc) => [doc.id, { ...doc, children: [] }]));
  for (const doc of byId.values()) {
    if (doc.parent && byId.has(doc.parent)) {
      byId.get(doc.parent).children.push(doc.id);
    }
  }
  return [...byId.values()];
}

function moduleNameFromPath(path) {
  const parts = path.split("/");
  const modulesIndex = parts.findIndex((part) => part.toLowerCase() === "modules");
  if (modulesIndex >= 0 && parts[modulesIndex + 1]) {
    return parts[modulesIndex + 1];
  }
  return parts.length > 1 ? parts[parts.length - 2] : "module";
}

function moduleNameFromFlowPath(path) {
  const parts = path.split("/");
  const modulesIndex = parts.findIndex((part) => part.toLowerCase() === "modules");
  if (modulesIndex >= 0 && parts[modulesIndex + 1]) {
    return parts[modulesIndex + 1];
  }
  const flowsIndex = parts.findIndex((part) => part.toLowerCase() === "flows");
  if (flowsIndex > 0) {
    return parts[flowsIndex - 1];
  }
  return parts.length > 1 ? parts[parts.length - 2] : "flows";
}

function isFlowMarkdown(path) {
  const name = basename(path).toLowerCase();
  if (name === "project.md" || name === "module.md") {
    return false;
  }
  const parts = path.toLowerCase().split("/");
  return parts.includes("flows") || name === "flow.md" || name.startsWith("flow-");
}

function uniqueId(id, sources) {
  let next = id;
  let index = 2;
  while (sources.some((source) => source.id === next)) {
    next = `${id}-${index}`;
    index += 1;
  }
  return next;
}

function basename(path) {
  return path.split("/").filter(Boolean).pop() || "";
}

function extractTitle(markdown, fallback) {
  const line = markdown.split(/\r?\n/).find((item) => /^#\s+/.test(item));
  return line ? line.replace(/^#\s+/, "").trim() : titleCase(fallback);
}

function readCodeBlock(lines, start) {
  const language = lines[start].replace(/`/g, "").trim().toLowerCase();
  const block = [];
  let index = start + 1;
  while (index < lines.length && !lines[index].startsWith("```")) {
    block.push(lines[index]);
    index += 1;
  }
  return { block: block.join("\n"), language, nextIndex: Math.min(index + 1, lines.length) };
}

function renderCodeBlock(block, language) {
  const escaped = escapeHtml(block);
  if (language === "mermaid") {
    const kind = mermaidDiagramKind(block);
    const largeClass = isLargeMermaidDiagram(block) ? " diagram-large" : "";
    return `<div class="diagram-block diagram-${kind}${largeClass}" data-diagram-kind="${kind}">
      <div class="diagram-toolbar">
        <div>
          <div class="diagram-title">Mermaid ${kind} diagram</div>
          <div class="diagram-hint">Drag horizontally to inspect the full diagram</div>
        </div>
        <button class="diagram-expand" type="button" aria-label="Open wide diagram view">Wide view</button>
      </div>
      <div class="diagram-body"><pre class="mermaid-source"><code>${escaped}</code></pre></div>
    </div>`;
  }
  return `<pre data-language="${escapeHtml(language || "code")}"><code>${escaped}</code></pre>`;
}

function mermaidDiagramKind(source) {
  const firstLine = source.split(/\r?\n/).find((line) => line.trim());
  const keyword = (firstLine || "diagram").trim().split(/\s+/)[0].toLowerCase();
  if (keyword === "sequencediagram") {
    return "sequence";
  }
  if (keyword === "graph" || keyword === "flowchart") {
    return "flowchart";
  }
  return keyword.replace(/[^a-z0-9-]/g, "") || "diagram";
}

function isLargeMermaidDiagram(source) {
  const lines = source.split(/\r?\n/).filter((line) => line.trim());
  const participants = lines.filter((line) => /^\s*(participant|actor)\s+/i.test(line)).length;
  const messages = lines.filter((line) => /[-=]+>>|-->>|->>|-->|-\)/.test(line)).length;
  const longestLine = lines.reduce((max, line) => Math.max(max, line.length), 0);
  return lines.length > 24 || participants >= 6 || messages >= 14 || longestLine > 110;
}

function estimateMermaidMinWidth(source, svgWidth = 0) {
  const lines = source.split(/\r?\n/).filter((line) => line.trim());
  const participants = lines.filter((line) => /^\s*(participant|actor)\s+/i.test(line)).length;
  const messages = lines.filter((line) => /[-=]+>>|-->>|->>|-->|-\)/.test(line)).length;
  const longestLine = lines.reduce((max, line) => Math.max(max, line.length), 0);
  const sourceEstimate = Math.max(760, participants * 210, messages * 72, longestLine * 8);
  return Math.ceil(Math.max(svgWidth || 0, sourceEstimate));
}

function isTableStart(lines, index) {
  return index + 1 < lines.length
    && isTableRow(lines[index])
    && /^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(lines[index + 1]);
}

function readTable(lines, start) {
  const rows = [];
  let index = start;
  while (index < lines.length && isTableRow(lines[index])) {
    if (!/^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(lines[index])) {
      rows.push(lines[index].trim().replace(/^\||\|$/g, "").split("|").map((cell) => cell.trim()));
    }
    index += 1;
  }
  return { rows, nextIndex: index };
}

function renderTable(rows, currentPath, linkMap) {
  if (!rows.length) {
    return "";
  }
  const header = rows[0].map((cell) => `<th>${escapeInline(cell, currentPath, linkMap)}</th>`).join("");
  const body = rows.slice(1)
    .map((row) => `<tr>${row.map((cell) => `<td>${escapeInline(cell, currentPath, linkMap)}</td>`).join("")}</tr>`)
    .join("");
  return `<table><thead><tr>${header}</tr></thead><tbody>${body}</tbody></table>`;
}

function isTableRow(line) {
  const text = line.trim();
  return text.startsWith("|") && text.endsWith("|");
}

function escapeInline(text, currentPath, linkMap) {
  const escaped = escapeHtml(text)
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/\*([^*]+)\*/g, "<em>$1</em>");
  return escaped.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_match, label, url) => {
    const resolved = resolveSiteLink(htmlDecode(url), currentPath, linkMap);
    return `<a href="${escapeHtml(resolved)}">${label}</a>`;
  });
}

function resolveSiteLink(url, currentPath, linkMap) {
  const lower = url.toLowerCase();
  if (lower.startsWith("http://") || lower.startsWith("https://") || lower.startsWith("mailto:") || lower.startsWith("#")) {
    return url;
  }
  const [target, fragment] = url.split("#");
  if (!target.endsWith(".md")) {
    return url;
  }
  const normalized = normalizeRelativePath(currentPath, target);
  const id = linkMap.get(normalized);
  return id ? `#${id}${fragment ? `#${fragment}` : ""}` : url;
}

function normalizeRelativePath(currentPath, target) {
  const base = currentPath.split("/").slice(0, -1);
  const parts = [...base, ...target.split("/")];
  const normalized = [];
  for (const part of parts) {
    if (!part || part === ".") {
      continue;
    }
    if (part === "..") {
      normalized.pop();
      continue;
    }
    normalized.push(part);
  }
  return normalized.join("/");
}

function plainText(markdown) {
  return markdown
    .replace(/```[\s\S]*?```/g, " ")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/[#`*_|\[\]()<>-]+/g, " ");
}

function slugId(text) {
  return String(text || "document")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9\u4e00-\u9fff]+/g, "-")
    .replace(/^-|-$/g, "") || "document";
}

function titleCase(text) {
  return String(text || "Document")
    .replace(/[-_]+/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function htmlDecode(value) {
  return String(value).replace(/&amp;/g, "&").replace(/&quot;/g, '"').replace(/&#39;/g, "'");
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[char]);
}

async function pickDirectory() {
  if (!window.showDirectoryPicker) {
    dom.folderInput.click();
    return;
  }
  try {
    const handle = await window.showDirectoryPicker();
    const files = [];
    await collectDirectoryFiles(handle, "", files);
    await loadAndRender(files);
  } catch (error) {
    if (error.name === "AbortError") {
      return;
    }
    dom.reader.innerHTML = `<p class="error">读取文件夹失败：${escapeHtml(error.message)}</p>`;
  }
}

async function collectDirectoryFiles(handle, prefix, files) {
  for await (const [name, child] of handle.entries()) {
    const path = prefix ? `${prefix}/${name}` : name;
    if (child.kind === "directory") {
      await collectDirectoryFiles(child, path, files);
    } else if (name.toLowerCase().endsWith(".md")) {
      try {
        const file = await child.getFile();
        files.push({ path, text: await file.text() });
      } catch (_error) {
        // 跳过单个文件读取失败，不中断整个文件夹加载
      }
    }
  }
}

async function loadInputFiles(fileList) {
  const files = [];
  for (const file of fileList) {
    if (file.name.toLowerCase().endsWith(".md")) {
      files.push({ path: file.webkitRelativePath || file.name, text: await file.text() });
    }
  }
  await loadAndRender(files);
}

async function loadAndRender(files) {
  const documents = await buildDocumentsFromFiles(files);
  const treeRoot = buildTreeNodes(documents);
  state = { documents, activeId: documents[0]?.id || "", treeRoot };
  dom.search.disabled = documents.length === 0;
  dom.search.value = "";
  dom.title.textContent = documents[0]?.title || "未发现 project-context 文档";
  render();
}

function render() {
  if (!dom) {
    return;
  }
  if (!state.documents.length) {
    renderEmptyProject();
    return;
  }
  const matches = matchingDocuments();
  if (searchQuery() && matches.length === 0) {
    renderEmptySearch();
    return;
  }
  const visible = visibleIds();
  if (searchQuery() && !visible.has(state.activeId)) {
    state.activeId = matches[0].id;
  }
  const doc = byId().get(state.activeId) || state.documents[0];
  state.activeId = doc.id;
  dom.reader.innerHTML = doc.html;
  dom.breadcrumbs.textContent = breadcrumbs(doc).join(" / ");
  renderTree(visible);
  renderDetails(doc);
  renderMermaid();
}

function buildTreeNodes(documents) {
  const root = { type: "dir", name: "", children: [], expanded: true };
  for (const doc of documents) {
    const parts = doc.path.split("/").filter(Boolean);
    let current = root;
    for (let i = 0; i < parts.length - 1; i++) {
      let child = current.children.find((c) => c.type === "dir" && c.name === parts[i]);
      if (!child) {
        child = { type: "dir", name: parts[i], children: [], expanded: true };
        current.children.push(child);
      }
      current = child;
    }
    current.children.push({ type: "doc", docId: doc.id });
  }
  return root;
}

function renderTree(visible) {
  dom.tree.innerHTML = "";
  if (!state.treeRoot) {
    return;
  }
  for (const node of state.treeRoot.children) {
    renderTreeNode(node, visible, 0, dom.tree);
  }
  dom.tree.querySelectorAll(".tree-toggle").forEach((btn) => {
    btn.addEventListener("click", (event) => {
      event.stopPropagation();
      const dir = btn.closest(".tree-dir");
      dir.classList.toggle("collapsed");
    });
  });
}

function renderTreeNode(node, visible, depth, parentEl) {
  if (node.type === "doc") {
    const doc = byId().get(node.docId);
    if (!doc || !visible.has(doc.id)) {
      return;
    }
    const button = document.createElement("button");
    button.type = "button";
    button.className = `tree-item tree-${doc.kind}${doc.id === state.activeId ? " active" : ""}`;
    button.style.paddingLeft = `${depth * 16 + 8}px`;
    button.textContent = `${kindIcon(doc.kind)} ${doc.title}`;
    button.addEventListener("click", () => {
      state.activeId = doc.id;
      render();
    });
    parentEl.appendChild(button);
  } else {
    const canShow = node.children.some((child) => {
      if (child.type === "doc") {
        return visible.has(child.docId);
      }
      return child.children.some((gc) => gc.type === "doc" && visible.has(gc.docId));
    });
    if (!canShow) {
      return;
    }
    const wrapper = document.createElement("div");
    wrapper.className = "tree-dir";
    const header = document.createElement("div");
    header.className = "tree-dir-header";
    header.style.paddingLeft = `${depth * 16 + 8}px`;
    header.innerHTML = `<span class="tree-toggle">▼</span> 📁 ${escapeHtml(node.name)}`;
    wrapper.appendChild(header);
    const container = document.createElement("div");
    container.className = "tree-dir-children";
    for (const child of node.children) {
      renderTreeNode(child, visible, depth + 1, container);
    }
    wrapper.appendChild(container);
    parentEl.appendChild(wrapper);
  }
}

function renderDetails(doc) {
  const children = doc.children.map((id) => byId().get(id)).filter(Boolean);
  dom.details.innerHTML = `
    <div class="detail-row"><div class="detail-label">类型</div><span class="badge">${doc.kind}</span></div>
    <div class="detail-row"><div class="detail-label">路径</div><code>${escapeHtml(doc.path)}</code></div>
    <div class="detail-row"><div class="detail-label">模块</div>${escapeHtml(doc.module || "Project")}</div>
    <div class="detail-row outline"><div class="detail-label">大纲</div>${renderOutline(doc)}</div>
    <div class="detail-row related"><div class="detail-label">下级文档</div>${children.length ? children.map((child) => `<a href="#" data-open="${child.id}">${escapeHtml(child.title)}</a>`).join("") : '<p class="empty">无下级文档。</p>'}</div>
  `;
  dom.details.querySelectorAll("[data-open]").forEach((link) => {
    link.addEventListener("click", (event) => {
      event.preventDefault();
      state.activeId = link.getAttribute("data-open");
      render();
    });
  });
}

function renderOutline(doc) {
  if (!doc.headings.length) {
    return '<p class="empty">无标题大纲。</p>';
  }
  return doc.headings.map((heading) => `<a href="#${heading.anchor}">${"-".repeat(Math.max(heading.level - 1, 0))} ${escapeHtml(heading.text)}</a>`).join("");
}

function renderEmptyProject() {
  dom.tree.innerHTML = '<p class="empty">未发现可展示的 Markdown。</p>';
  dom.reader.innerHTML = '<h2>未发现 project-context 文档</h2><p class="empty">请选择包含 project.md、module.md 或 flow 文档的文件夹。</p>';
  dom.details.innerHTML = '<p class="empty">没有可用上下文。</p>';
  dom.breadcrumbs.textContent = "";
}

function renderEmptySearch() {
  dom.tree.innerHTML = '<p class="empty">没有匹配文档。</p>';
  dom.reader.innerHTML = `<h2>没有匹配文档</h2><p class="empty">没有项目、模块或业务流匹配 "${escapeHtml(dom.search.value)}"。</p>`;
  dom.details.innerHTML = '<p class="empty">搜索没有返回结果。</p>';
  dom.breadcrumbs.textContent = "搜索";
}

function matchingDocuments() {
  const query = searchQuery();
  return query ? state.documents.filter((doc) => doc.searchText.includes(query)) : state.documents;
}

function visibleIds() {
  const query = searchQuery();
  if (!query) {
    return new Set(state.documents.map((doc) => doc.id));
  }
  const ids = new Set();
  const docsById = byId();
  for (const match of matchingDocuments()) {
    let current = match;
    while (current) {
      ids.add(current.id);
      current = docsById.get(current.parent);
    }
  }
  return ids;
}

function breadcrumbs(doc) {
  const items = [];
  const docsById = byId();
  let current = doc;
  while (current) {
    items.unshift(current.title);
    current = docsById.get(current.parent);
  }
  return items;
}

function byId() {
  return new Map(state.documents.map((doc) => [doc.id, doc]));
}

function searchQuery() {
  return dom.search.value.trim().toLowerCase();
}

function kindIcon(kind) {
  return kind === "project" ? "P" : kind === "module" ? "M" : "F";
}

function renderMermaid() {
  if (typeof mermaid === "undefined") {
    bindDiagramControls();
    return;
  }
  requestAnimationFrame(async () => {
    const blocks = dom.reader.querySelectorAll(".mermaid-source code");
    if (!blocks.length) {
      bindDiagramControls();
      return;
    }
    for (const block of blocks) {
      const source = block.textContent;
      const container = block.closest(".diagram-block");
      if (!container) {
        continue;
      }
      try {
        const id = "mermaid-" + Math.random().toString(36).slice(2);
        const { svg } = await mermaid.render(id, source);
        const body = container.querySelector(".diagram-body") || container;
        body.innerHTML = `<div class="diagram-viewport">${svg}</div>`;
        sizeRenderedDiagram(container, source);
      } catch (_) {
        // 渲染失败保持源码显示
      }
    }
    bindDiagramControls();
  });
}

function sizeRenderedDiagram(container, source) {
  const svg = container.querySelector("svg");
  if (!svg) {
    return;
  }
  const viewBox = svg.getAttribute("viewBox") || "";
  const viewBoxWidth = Number(viewBox.split(/\s+/)[2]) || Number.parseFloat(svg.getAttribute("width")) || 0;
  const wideWidth = estimateMermaidMinWidth(source, viewBoxWidth);
  svg.dataset.fitWidth = "100%";
  svg.dataset.wideWidth = `${wideWidth}px`;
  applyDiagramScale(container, false);
}

function applyDiagramScale(container, expanded) {
  const svg = container.querySelector("svg");
  if (!svg) {
    return;
  }
  if (expanded) {
    svg.style.width = svg.dataset.wideWidth || "";
    svg.style.minWidth = svg.dataset.wideWidth || "";
    svg.style.maxWidth = "none";
  } else {
    svg.style.width = svg.dataset.fitWidth || "100%";
    svg.style.minWidth = "0";
    svg.style.maxWidth = "100%";
  }
  svg.style.height = "auto";
}

function bindDiagramControls() {
  dom.reader.querySelectorAll(".diagram-expand").forEach((button) => {
    if (button.dataset.bound === "true") {
      return;
    }
    button.dataset.bound = "true";
    button.addEventListener("click", () => {
      const block = button.closest(".diagram-block");
      if (!block) {
        return;
      }
      const expanded = block.classList.toggle("diagram-expanded");
      applyDiagramScale(block, expanded);
      button.textContent = expanded ? "Exit wide view" : "Wide view";
      button.setAttribute("aria-label", expanded ? "Exit wide diagram view" : "Open wide diagram view");
    });
  });
}

if (dom) {
  dom.pickFolder.addEventListener("click", () => {
    pickDirectory().catch((error) => {
      dom.reader.innerHTML = `<p class="error">读取文件夹失败：${escapeHtml(error.message)}</p>`;
    });
  });
  dom.folderInput.addEventListener("change", () => {
    loadInputFiles(dom.folderInput.files)
      .catch((error) => {
        dom.reader.innerHTML = `<p class="error">读取文件夹失败：${escapeHtml(error.message)}</p>`;
      })
      .finally(() => {
        dom.folderInput.value = "";
      });
  });
  dom.search.addEventListener("input", render);
}

// Node.js exports (for testing)
if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    buildDocumentsFromFiles,
    discoverDocumentSources,
    estimateMermaidMinWidth,
    isLargeMermaidDiagram,
    mermaidDiagramKind,
    normalizePath,
    renderMarkdown,
    stripCommonRoot,
  };
}
