import html
import uuid
from typing import List, Dict, Any, Optional
from ebooklib import epub
from manuscriptfinesse.export.base_exporter import BaseExporter


def text_to_html(text: str) -> str:
    """Converts raw text or basic Markdown paragraphs to valid escaped XHTML paragraph tags."""
    if not text:
        return ""
    paragraphs = text.strip().split("\n\n")
    html_parts = []
    for p in paragraphs:
        cleaned = p.strip()
        if not cleaned:
            continue
        if cleaned.startswith("# "):
            html_parts.append(f"<h2>{html.escape(cleaned[2:])}</h2>")
        elif cleaned.startswith("## "):
            html_parts.append(f"<h3>{html.escape(cleaned[3:])}</h3>")
        elif cleaned.startswith("### "):
            html_parts.append(f"<h4>{html.escape(cleaned[4:])}</h4>")
        else:
            html_parts.append(f"<p>{html.escape(cleaned)}</p>")
    return "\n".join(html_parts)


class EPUBExporter(BaseExporter):
    """Stage 6 EPUB Exporter utilizing ebooklib."""

    def compile(
        self,
        chapters: List[Dict[str, str]],
        output_path: str,
        front_matter: Optional[Dict[str, str]] = None
    ) -> str:
        self._ensure_output_dir(output_path)

        book = epub.EpubBook()
        book.set_identifier(f"urn:uuid:{uuid.uuid4()}")
        book.set_title(self.title)
        book.set_language("en")
        book.add_author(self.author)

        # Basic eBook CSS styling
        style = (
            "body { font-family: Georgia, serif; line-height: 1.6; margin: 5%; }\n"
            "h1, h2, h3 { text-align: center; font-weight: bold; margin-top: 1.5em; }\n"
            "p { text-indent: 1.5em; margin-top: 0; margin-bottom: 0; }\n"
            ".frontmatter { text-align: center; margin-top: 3em; }\n"
        )
        css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
        book.add_item(css)

        spine_items = []
        toc_items = []

        # Front Matter
        if front_matter:
            fm_html_content = f"<div class='frontmatter'><h1>{self.title}</h1><h2>by {self.author}</h2>"
            if "copyright" in front_matter:
                fm_html_content += f"<p style='text-indent:0;'>{front_matter['copyright']}</p>"
            fm_html_content += "</div>"

            if "foreword" in front_matter:
                fm_html_content += f"<h2>Foreword</h2>{text_to_html(front_matter['foreword'])}"
            if "dedication" in front_matter:
                fm_html_content += f"<h2>Dedication</h2>{text_to_html(front_matter['dedication'])}"

            fm_doc = epub.EpubHtml(title="Front Matter", file_name="front_matter.xhtml", lang="en")
            fm_doc.content = fm_html_content
            fm_doc.add_item(css)
            book.add_item(fm_doc)
            spine_items.append(fm_doc)
            toc_items.append(fm_doc)

        # Chapters
        for i, ch in enumerate(chapters, start=1):
            title = ch.get("title", f"Chapter {i}")
            raw_content = ch.get("content", "")
            body_html = text_to_html(raw_content)

            chap_doc = epub.EpubHtml(title=title, file_name=f"chap_{i}.xhtml", lang="en")
            chap_doc.content = f"<h1>{title}</h1>{body_html}"
            chap_doc.add_item(css)

            book.add_item(chap_doc)
            spine_items.append(chap_doc)
            toc_items.append(chap_doc)

        # Back Matter (if present in front_matter dict)
        if front_matter and ("about_author" in front_matter or "acknowledgments" in front_matter):
            bm_html = ""
            if "acknowledgments" in front_matter:
                bm_html += f"<h2>Acknowledgments</h2>{text_to_html(front_matter['acknowledgments'])}"
            if "about_author" in front_matter:
                bm_html += f"<h2>About the Author</h2>{text_to_html(front_matter['about_author'])}"

            bm_doc = epub.EpubHtml(title="Back Matter", file_name="back_matter.xhtml", lang="en")
            bm_doc.content = bm_html
            bm_doc.add_item(css)
            book.add_item(bm_doc)
            spine_items.append(bm_doc)

        book.toc = tuple(toc_items)
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        book.spine = ['nav'] + spine_items
        epub.write_epub(output_path, book, {})

        return output_path
