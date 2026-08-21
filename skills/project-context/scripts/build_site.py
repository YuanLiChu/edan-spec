#!/usr/bin/env python3
"""Build a static browser for project-context Markdown documents."""

from __future__ import annotations

import argparse
import html
import json
import re
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath


@dataclass(frozen=True)
class Heading:
    level: int
    text: str
    anchor: str


@dataclass(frozen=True)
class Document:
    id: str
    kind: str
    title: str
    path: str
    module: str | None
    parent: str | None
    children: list[str] = field(default_factory=list)
    html: str = ""
    headings: list[Heading] = field(default_factory=list)
    search_text: str = ""


@dataclass(frozen=True)
class DocumentSource:
    path: Path
    kind: str
    id: str
    module: str | None
    parent: str | None


def build_site(context_dir: Path, output_dir: Path) -> Path:
    context_dir = context_dir.resolve()
    output_dir = output_dir.resolve()
    documents = scan_context(context_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    index_path = output_dir / "index.html"
    index_path.write_text(render_site(documents), encoding="utf-8")
    return index_path


def scan_context(context_dir: Path) -> list[Document]:
    if not context_dir.exists():
        raise FileNotFoundError(f"context directory does not exist: {context_dir}")

    sources: list[DocumentSource] = []
    project_path = context_dir / "project.md"
    if project_path.exists():
        sources.append(DocumentSource(project_path, "project", "project", None, None))
    else:
        sources.append(DocumentSource(project_path, "project", "project", None, None))

    module_paths = sorted((context_dir / "modules").glob("*/module.md"))
    for module_path in module_paths:
        module_name = module_path.parent.name
        module_id = f"module:{module_name}"
        sources.append(DocumentSource(module_path, "module", module_id, module_name, "project"))
        flow_paths = sorted((module_path.parent / "flows").glob("*.md"))
        for flow_path in flow_paths:
            flow_name = flow_path.stem
            flow_id = f"flow:{module_name}:{flow_name}"
            sources.append(DocumentSource(flow_path, "flow", flow_id, module_name, module_id))

    link_map = build_link_map(sources, context_dir)
    raw_docs = [load_document(source, context_dir, link_map) for source in sources]
    return attach_children(raw_docs)


def build_link_map(sources: list[DocumentSource], context_dir: Path) -> dict[str, str]:
    link_map: dict[str, str] = {}
    for source in sources:
        if not source.path.exists():
            continue
        rel_path = source.path.relative_to(context_dir).as_posix()
        link_map[rel_path] = source.id
    return link_map


def load_document(source: DocumentSource, context_dir: Path, link_map: dict[str, str]) -> Document:
    rel_path = source.path.relative_to(context_dir).as_posix()
    if not source.path.exists():
        if source.kind == "project":
            return Document(
                id=source.id,
                kind=source.kind,
                title="Project Context",
                path="project.md",
                module=None,
                parent=None,
                html='<p class="empty">No project.md found.</p>',
                search_text="Project Context",
            )
        raise FileNotFoundError(f"document does not exist: {source.path}")
    try:
        markdown = source.path.read_text(encoding="utf-8").lstrip("\ufeff")
    except (OSError, UnicodeDecodeError) as error:
        title = rel_path
        return Document(
            id=source.id,
            kind=source.kind,
            title=title,
            path=rel_path,
            module=source.module,
            parent=source.parent,
            html=f'<p class="empty">Unable to read Markdown: {html.escape(str(error))}</p>',
            search_text=f"{title} {rel_path} unable to read markdown".lower(),
        )

    rendered = render_markdown(markdown, rel_path, link_map)
    title = extract_title(markdown, source.path.stem)
    return Document(
        id=source.id,
        kind=source.kind,
        title=title,
        path=rel_path,
        module=source.module,
        parent=source.parent,
        html=rendered["html"],
        headings=rendered["headings"],
        search_text=f"{title} {rel_path} {plain_text(markdown)}".lower(),
    )


def attach_children(documents: list[Document]) -> list[Document]:
    child_map: dict[str, list[str]] = {document.id: [] for document in documents}
    for document in documents:
        if document.parent in child_map:
            child_map[document.parent].append(document.id)
    return [
        Document(
            id=document.id,
            kind=document.kind,
            title=document.title,
            path=document.path,
            module=document.module,
            parent=document.parent,
            children=child_map.get(document.id, []),
            html=document.html,
            headings=document.headings,
            search_text=document.search_text,
        )
        for document in documents
    ]


def render_markdown(markdown: str, current_path: str, link_map: dict[str, str]) -> dict:
    lines = markdown.splitlines()
    parts: list[str] = []
    headings: list[Heading] = []
    index = 0
    in_list = False
    while index < len(lines):
        line = lines[index]
        if line.startswith("```"):
            block, language, index = read_code_block(lines, index)
            parts.append(render_code_block(block, language))
            continue
        if is_table_start(lines, index):
            table, index = read_table(lines, index)
            parts.append(render_table(table, current_path, link_map))
            continue
        heading = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading:
            if in_list:
                parts.append("</ul>")
                in_list = False
            level = len(heading.group(1))
            text = heading.group(2).strip()
            anchor = slugify(text)
            headings.append(Heading(level, text, anchor))
            parts.append(f'<h{level} id="{anchor}">{escape_inline(text, current_path, link_map)}</h{level}>')
        elif re.match(r"^\s*[-*]\s+", line):
            if not in_list:
                parts.append("<ul>")
                in_list = True
            item = re.sub(r"^\s*[-*]\s+", "", line).strip()
            parts.append(f"<li>{escape_inline(item, current_path, link_map)}</li>")
        elif not line.strip():
            if in_list:
                parts.append("</ul>")
                in_list = False
        else:
            if in_list:
                parts.append("</ul>")
                in_list = False
            parts.append(f"<p>{escape_inline(line.strip(), current_path, link_map)}</p>")
        index += 1
    if in_list:
        parts.append("</ul>")
    return {"html": "\n".join(parts), "headings": headings}


def read_code_block(lines: list[str], start: int) -> tuple[str, str, int]:
    language = lines[start].strip().strip("`").strip().lower()
    block: list[str] = []
    index = start + 1
    while index < len(lines) and not lines[index].startswith("```"):
        block.append(lines[index])
        index += 1
    return "\n".join(block), language, min(index + 1, len(lines))


def render_code_block(block: str, language: str) -> str:
    escaped = html.escape(block)
    if language == "mermaid":
        return (
            '<div class="diagram-block"><div class="diagram-title">Mermaid diagram source</div>'
            f"<pre><code>{escaped}</code></pre></div>"
        )
    label = html.escape(language or "code")
    return f'<pre data-language="{label}"><code>{escaped}</code></pre>'


def is_table_start(lines: list[str], index: int) -> bool:
    return (
        index + 1 < len(lines)
        and "|" in lines[index]
        and re.match(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$", lines[index + 1])
        and is_table_row(lines[index])
    )


def read_table(lines: list[str], start: int) -> tuple[list[list[str]], int]:
    rows: list[list[str]] = []
    index = start
    while index < len(lines) and is_table_row(lines[index]):
        if not re.match(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$", lines[index]):
            rows.append(split_table_row(lines[index]))
        index += 1
    return rows, index


def render_table(rows: list[list[str]], current_path: str, link_map: dict[str, str]) -> str:
    if not rows:
        return ""
    header = "".join(f"<th>{escape_inline(cell, current_path, link_map)}</th>" for cell in rows[0])
    body_rows = []
    for row in rows[1:]:
        body_rows.append(
            "<tr>" + "".join(f"<td>{escape_inline(cell, current_path, link_map)}</td>" for cell in row) + "</tr>"
        )
    return f"<table><thead><tr>{header}</tr></thead><tbody>{''.join(body_rows)}</tbody></table>"


def is_table_row(line: str) -> bool:
    return line.strip().startswith("|") and line.strip().endswith("|")


def split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def extract_title(markdown: str, fallback: str) -> str:
    for line in markdown.splitlines():
        match = re.match(r"^#\s+(.+)$", line)
        if match:
            return match.group(1).strip()
    return fallback.replace("-", " ").title()


def plain_text(markdown: str) -> str:
    without_code = re.sub(r"```.*?```", " ", markdown, flags=re.DOTALL)
    without_links = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", without_code)
    return re.sub(r"[#`*_|\[\]()<>-]+", " ", without_links)


def escape_inline(text: str, current_path: str, link_map: dict[str, str]) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    return re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda match: link_replacer(match, current_path, link_map),
        escaped,
    )


def link_replacer(match: re.Match[str], current_path: str, link_map: dict[str, str]) -> str:
    label = match.group(1)
    raw_url = html.unescape(match.group(2))
    url = resolve_site_link(raw_url, current_path, link_map)
    return f'<a href="{html.escape(url, quote=True)}">{label}</a>'


def resolve_site_link(url: str, current_path: str, link_map: dict[str, str]) -> str:
    lowered = url.lower()
    if lowered.startswith(("http://", "https://", "mailto:", "#")):
        return url
    target, separator, fragment = url.partition("#")
    if not target.endswith(".md"):
        return url
    base = PurePosixPath(current_path).parent
    normalized = normalize_posix_path(base / target)
    doc_id = link_map.get(normalized)
    if not doc_id:
        return url
    return f"#{doc_id}{separator}{fragment}" if fragment else f"#{doc_id}"


def normalize_posix_path(path: PurePosixPath) -> str:
    parts: list[str] = []
    for part in path.parts:
        if part in {"", "."}:
            continue
        if part == "..":
            if parts:
                parts.pop()
            continue
        parts.append(part)
    return "/".join(parts)


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", text.strip().lower()).strip("-")
    return slug or "section"


def render_site(documents: list[Document]) -> str:
    payload = {
        "projectTitle": documents[0].title if documents else "Project Context",
        "documents": [document_to_json(document) for document in documents],
    }
    data = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" href="data:,">
  <title>{html.escape(payload["projectTitle"])} - Context Browser</title>
  <style>{site_css()}</style>
</head>
<body>
  <header>
    <div>
      <span class="eyebrow">Hybrid explorer</span>
      <h1>{html.escape(payload["projectTitle"])}</h1>
    </div>
    <input id="search" type="search" placeholder="Search project, modules, flows..." aria-label="Search">
  </header>
  <main>
    <nav aria-label="Context tree">
      <div class="panel-title">Project Context</div>
      <div id="tree"></div>
    </nav>
    <article>
      <div id="breadcrumbs"></div>
      <section id="reader"></section>
    </article>
    <aside>
      <div class="panel-title">Context</div>
      <div id="details"></div>
    </aside>
  </main>
  <script id="context-data" type="application/json">{data}</script>
  <script>{site_js()}</script>
</body>
</html>
"""


def document_to_json(document: Document) -> dict:
    return {
        "id": document.id,
        "kind": document.kind,
        "title": document.title,
        "path": document.path,
        "module": document.module,
        "parent": document.parent,
        "children": document.children,
        "html": document.html,
        "headings": [heading.__dict__ for heading in document.headings],
        "searchText": document.search_text,
    }


def site_css() -> str:
    return """
:root{color-scheme:light;--bg:#f6f7f9;--panel:#fff;--ink:#1f2933;--muted:#687385;--line:#d9dee7;--accent:#2166d1;--accent-soft:#e8f1ff;--code:#f1f3f7}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.55 "Segoe UI",Arial,sans-serif}
header{height:76px;display:flex;align-items:center;justify-content:space-between;gap:24px;padding:14px 22px;border-bottom:1px solid var(--line);background:var(--panel)}
h1{font-size:22px;margin:2px 0 0}h2{font-size:22px;margin-top:18px}h3{font-size:18px}.eyebrow,.panel-title{font-size:12px;text-transform:uppercase;color:var(--muted);font-weight:700;letter-spacing:.04em}
#search{width:min(460px,42vw);padding:10px 12px;border:1px solid var(--line);border-radius:6px;background:#fff}
main{display:grid;grid-template-columns:280px minmax(0,1fr)300px;height:calc(100vh - 76px)}
nav,aside{overflow:auto;background:var(--panel);padding:16px;border-right:1px solid var(--line)}aside{border-right:0;border-left:1px solid var(--line)}
article{overflow:auto;padding:22px 34px}.tree-item{width:100%;display:block;text-align:left;border:0;background:transparent;border-radius:6px;padding:7px 8px;margin:2px 0;color:var(--ink);cursor:pointer}
.tree-item:hover,.tree-item.active{background:var(--accent-soft);color:var(--accent)}.tree-project{font-weight:700}.tree-module{padding-left:18px}.tree-flow{padding-left:36px}
#breadcrumbs{color:var(--muted);margin-bottom:14px}#reader{max-width:980px;background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:24px}
#reader table{border-collapse:collapse;width:100%;margin:14px 0}th,td{border:1px solid var(--line);padding:8px;text-align:left}th{background:#f3f5f8}
pre{overflow:auto;background:var(--code);padding:12px;border-radius:6px}code{font-family:Consolas,monospace}.diagram-block{border:1px solid var(--line);border-radius:8px;background:#fbfcff;margin:14px 0}.diagram-title{padding:8px 12px;border-bottom:1px solid var(--line);color:var(--muted);font-weight:700}
.detail-row{margin:0 0 12px}.detail-label{font-size:12px;color:var(--muted);text-transform:uppercase}.outline a,.related a{display:block;color:var(--accent);text-decoration:none;margin:6px 0}.badge{display:inline-block;padding:2px 7px;border:1px solid var(--line);border-radius:999px;color:var(--muted);font-size:12px}.empty{color:var(--muted)}
@media(max-width:980px){main{grid-template-columns:1fr;height:auto}nav,aside,article{border:0;height:auto}#search{width:100%}header{height:auto;align-items:flex-start;flex-direction:column}}
"""


def site_js() -> str:
    return """
const data=JSON.parse(document.getElementById('context-data').textContent);
const docs=data.documents;
const byId=new Map(docs.map(doc=>[doc.id,doc]));
let activeId=location.hash?decodeURIComponent(location.hash.slice(1)):(docs[0]&&docs[0].id);
function searchQuery(){return document.getElementById('search').value.trim().toLowerCase()}
function matchingDocs(){const q=searchQuery();return q?docs.filter(doc=>doc.searchText.includes(q)):docs}
function visibleIds(){const q=searchQuery();if(!q)return new Set(docs.map(doc=>doc.id));const ids=new Set();for(const match of matchingDocs()){let current=match;while(current){ids.add(current.id);current=byId.get(current.parent)}}return ids}
function renderTree(){const ids=visibleIds();const tree=document.getElementById('tree');tree.innerHTML='';if(ids.size===0){tree.innerHTML='<p class="empty">No matching documents.</p>';return}for(const doc of docs){if(!ids.has(doc.id))continue;const btn=document.createElement('button');btn.className=`tree-item tree-${doc.kind}${doc.id===activeId?' active':''}`;btn.textContent=`${kindIcon(doc.kind)} ${doc.title}`;btn.onclick=()=>selectDoc(doc.id);tree.appendChild(btn)}}
function selectDoc(id){activeId=id;location.hash=encodeURIComponent(id);render()}
function render(){const doc=byId.get(activeId)||docs[0];if(!doc)return;activeId=doc.id;document.getElementById('reader').innerHTML=doc.html||'<p class="empty">No content.</p>';document.getElementById('breadcrumbs').textContent=breadcrumbs(doc).join(' / ');renderDetails(doc);renderTree()}
function renderEmptySearch(){const q=escapeHtml(document.getElementById('search').value.trim());document.getElementById('breadcrumbs').textContent='Search';document.getElementById('reader').innerHTML=`<h2>No matching documents</h2><p class="empty">No project, module, or flow document matched "${q}". Try a module name, flow name, source path, or term from the Markdown body.</p>`;document.getElementById('details').innerHTML='<p class="empty">Search returned no documents.</p>';renderTree()}
function handleSearch(){const matches=matchingDocs();if(searchQuery()&&matches.length===0){renderEmptySearch();return}if(searchQuery()&&!visibleIds().has(activeId)){activeId=matches[0].id}render()}
function renderDetails(doc){const children=doc.children.map(id=>byId.get(id)).filter(Boolean);document.getElementById('details').innerHTML=`<div class="detail-row"><div class="detail-label">Type</div><span class="badge">${doc.kind}</span></div><div class="detail-row"><div class="detail-label">Path</div><code>${escapeHtml(doc.path)}</code></div><div class="detail-row"><div class="detail-label">Module</div>${escapeHtml(doc.module||'Project')}</div><div class="detail-row outline"><div class="detail-label">Outline</div>${doc.headings.length?doc.headings.map(h=>`<a href="#${doc.id}-${h.anchor}" onclick="event.preventDefault();document.getElementById('${h.anchor}')?.scrollIntoView({behavior:'smooth'});">${'-'.repeat(Math.max(h.level-1,0))} ${escapeHtml(h.text)}</a>`).join(''):'<p class="empty">No headings.</p>'}</div><div class="detail-row related"><div class="detail-label">Related</div>${children.length?children.map(child=>`<a href="#${child.id}" onclick="event.preventDefault();selectDoc('${child.id}')">${escapeHtml(child.title)}</a>`).join(''):'<p class="empty">No child documents.</p>'}</div>`}
function breadcrumbs(doc){const items=[];let current=doc;while(current){items.unshift(current.title);current=byId.get(current.parent)}return items}
function kindIcon(kind){return kind==='project'?'P':kind==='module'?'M':'F'}
function escapeHtml(value){return String(value).replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]))}
document.getElementById('search').addEventListener('input',handleSearch);
window.addEventListener('hashchange',()=>{if(location.hash){activeId=decodeURIComponent(location.hash.slice(1));render()}});
render();
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a static project-context browser.")
    parser.add_argument("--context-dir", default="EdanSpec/context", help="Directory containing project.md and modules/.")
    parser.add_argument("--output-dir", default=None, help="Output directory. Defaults to <context-dir>/site.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    context_dir = Path(args.context_dir)
    output_dir = Path(args.output_dir) if args.output_dir else context_dir / "site"
    index_path = build_site(context_dir, output_dir)
    print(f"Wrote {index_path}")


if __name__ == "__main__":
    main()
