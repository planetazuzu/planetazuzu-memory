---
name: pptx
description: Handle anything involving PowerPoint files (.pptx). Use for creating slide decks, pitch decks, or presentations; reading or extracting text from .pptx files; editing or updating existing presentations; combining or splitting slide files; working with templates, layouts, speaker notes, or comments. Trigger when the user mentions "deck", "slides", "presentation", or references a .pptx filename.
license: MIT
compatibility: opencode
---

## What I do

- Create slide decks, pitch decks, and presentations from scratch
- Read and extract text/content from existing .pptx files
- Edit and update existing presentations
- Work with templates, layouts, speaker notes, comments
- Combine or split slide files

## When to use me

Trigger whenever the user mentions "deck", "slides", "presentation", or a `.pptx` filename — regardless of whether they want to create, read, or edit.

## How I work

### Reading content

```bash
# Extract text from a presentation
python -m markitdown presentation.pptx
```

Or with python-pptx:

```python
from pptx import Presentation

prs = Presentation("presentation.pptx")
for slide in prs.slides:
    for shape in slide.shapes:
        if shape.has_text_frame:
            print(shape.text_frame.text)
```

### Creating from scratch (python-pptx)

```bash
pip install python-pptx
```

```python
from pptx import Presentation
from pptx.util import Inches, Pt

prs = Presentation()
slide_layout = prs.slide_layouts[1]  # Title and Content
slide = prs.slides.add_slide(slide_layout)

title = slide.shapes.title
title.text = "Slide Title"

content = slide.placeholders[1]
content.text = "Slide content here"

prs.save("output.pptx")
```

### Creating from scratch (pptxgenjs — Node.js, richer styling)

```bash
npm install pptxgenjs
```

```js
const PptxGenJS = require("pptxgenjs");
const pptx = new PptxGenJS();

let slide = pptx.addSlide();
slide.addText("Hello World!", {
  x: 1, y: 1, w: 8, h: 1,
  fontSize: 36,
  bold: true,
  color: "363636",
});

pptx.writeFile({ fileName: "output.pptx" });
```

### Editing existing presentations

```python
from pptx import Presentation

prs = Presentation("existing.pptx")
slide = prs.slides[0]

# Find and replace text
for shape in slide.shapes:
    if shape.has_text_frame:
        for para in shape.text_frame.paragraphs:
            for run in para.runs:
                if "old text" in run.text:
                    run.text = run.text.replace("old text", "new text")

prs.save("modified.pptx")
```

### Adding images

```python
from pptx.util import Inches

slide.shapes.add_picture("image.png", Inches(1), Inches(1), Inches(4), Inches(3))
```
