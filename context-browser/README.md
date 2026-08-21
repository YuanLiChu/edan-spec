# Project Context Browser

This is a local static website for browsing `project-context` Markdown output directly from a folder.

## Use

1. Open `context-browser/index.html` in a modern browser, or serve this folder with a local static server.
2. Click **添加文件夹**.
3. Select a folder that contains `project.md`, `module.md`, and `flow.md` documents.

The app reads files in the browser. It does not upload project documents or require a backend.

## Supported Layouts

Preferred layout:

```text
project.md
modules/
  admission/
    module.md
    flows/
      create-admission.md
```

Loose layouts are also supported when they contain Markdown files named `module.md` or `flow.md`.

## Browser Notes

- Chromium browsers can use the File System Access API through **添加文件夹**.
- The **兼容选择** control uses the `webkitdirectory` file input fallback.
- Search matches title, path, summary, headings, and body text.
- Large Mermaid diagrams use a horizontal viewport and a wide-view mode for detailed inspection.
