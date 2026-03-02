---
name: docx
description: Create, read, edit, or manipulate Word documents (.docx files). Use for Word docs, .docx files, reports, memos, letters, templates with formatting like tables of contents, headings, page numbers, or letterheads. Also for extracting content, inserting images, find-and-replace, tracked changes, or converting content into a polished Word document. Do NOT use for PDFs, spreadsheets, or Google Docs.
license: MIT
compatibility: opencode
---

## What I do

- Create new Word documents (.docx) from scratch with professional formatting
- Read and extract content from existing .docx files
- Edit existing documents: headings, tables, images, tracked changes
- Convert documents to/from other formats (PDF, Markdown, etc.)
- Apply formatting: table of contents, page numbers, letterheads, styles

## When to use me

Use when the user mentions "Word doc", "word document", ".docx", or asks for a report, memo, letter, or template as a Word file.

Do NOT use for PDFs, spreadsheets, Google Docs, or coding tasks unrelated to document generation.

## How I work

A .docx file is a ZIP archive containing XML files.

| Task | Approach |
|------|----------|
| Read/analyze content | `pandoc` or unpack for raw XML |
| Create new document | Use `docx-js` (Node.js) |
| Edit existing document | Unpack → edit XML → repack |

### Reading content

```bash
# Text extraction
pandoc --track-changes=all document.docx -o output.md

# Raw XML access
unzip document.docx -d unpacked/
```

### Creating a new document (Node.js with docx library)

```bash
npm install docx
```

```js
const { Document, Paragraph, TextRun, HeadingLevel, Packer } = require("docx");
const fs = require("fs");

const doc = new Document({
  sections: [{
    properties: {},
    children: [
      new Paragraph({
        text: "Document Title",
        heading: HeadingLevel.HEADING_1,
      }),
      new Paragraph({
        children: [new TextRun("Your content here.")],
      }),
    ],
  }],
});

Packer.toBuffer(doc).then((buffer) => {
  fs.writeFileSync("output.docx", buffer);
});
```

### Converting .doc to .docx

```bash
soffice --headless --convert-to docx document.doc
```

### Editing existing documents

```bash
# Unpack
unzip document.docx -d unpacked/

# Edit XML files in unpacked/word/document.xml

# Repack
cd unpacked && zip -r ../output.docx .
```
