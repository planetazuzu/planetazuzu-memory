---
name: pdf
description: Handle anything involving PDF files. Use for reading/extracting text or tables, merging or splitting PDFs, rotating pages, adding watermarks, creating new PDFs, filling PDF forms, encrypting/decrypting, extracting images, and OCR on scanned PDFs. If the user mentions a .pdf file or asks to produce one, use this skill.
license: MIT
compatibility: opencode
---

## What I do

- Read and extract text or tables from PDFs
- Merge multiple PDFs into one / split PDFs apart
- Rotate pages, add watermarks, encrypt/decrypt
- Create new PDFs from scratch
- Fill PDF forms programmatically
- Extract images from PDFs
- OCR on scanned PDFs to make them searchable

## When to use me

Use whenever the user mentions a `.pdf` file or asks to produce one.

## How I work

### Primary library: pypdf (Python)

```bash
pip install pypdf
```

```python
from pypdf import PdfReader, PdfWriter

# Read a PDF
reader = PdfReader("document.pdf")
print(f"Pages: {len(reader.pages)}")

# Extract text
text = ""
for page in reader.pages:
    text += page.extract_text()
print(text)
```

### Merging PDFs

```python
from pypdf import PdfMerger

merger = PdfMerger()
merger.append("file1.pdf")
merger.append("file2.pdf")
merger.write("merged.pdf")
merger.close()
```

### Splitting PDFs

```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("document.pdf")
writer = PdfWriter()

# Extract pages 1-3
for i in range(3):
    writer.add_page(reader.pages[i])

with open("split.pdf", "wb") as f:
    writer.write(f)
```

### Rotating pages

```python
reader = PdfReader("document.pdf")
writer = PdfWriter()

for page in reader.pages:
    page.rotate(90)
    writer.add_page(page)

with open("rotated.pdf", "wb") as f:
    writer.write(f)
```

### Adding watermarks

```python
from pypdf import PdfReader, PdfWriter

watermark = PdfReader("watermark.pdf").pages[0]
reader = PdfReader("document.pdf")
writer = PdfWriter()

for page in reader.pages:
    page.merge_page(watermark)
    writer.add_page(page)

with open("watermarked.pdf", "wb") as f:
    writer.write(f)
```

### OCR on scanned PDFs

```bash
pip install ocrmypdf
ocrmypdf scanned.pdf searchable.pdf
```

### Creating PDFs from HTML (alternative)

```bash
pip install weasyprint
```

```python
from weasyprint import HTML
HTML(string="<h1>Hello PDF</h1>").write_pdf("output.pdf")
```
