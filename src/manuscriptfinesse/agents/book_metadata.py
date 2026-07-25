"""
Book Metadata Generator for ManuscriptFinesse

This module provides professional front matter and back matter generation
for manuscripts, following traditional publishing layout conventions.
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class BookMetadata:
    """Container for book metadata used in front/back matter generation."""
    title: str
    author: str
    subtitle: Optional[str] = None
    genre: str = "Fiction"
    copyright_year: Optional[str] = None
    publisher: str = "Independent Press"
    isbn_print: Optional[str] = None
    isbn_ebook: Optional[str] = None
    lccn: Optional[str] = None
    edition: str = "First Edition"
    city: str = "United States"
    author_bio: Optional[str] = None
    author_website: Optional[str] = None
    other_books: Optional[List[str]] = None
    dedication: Optional[str] = None
    acknowledgements: Optional[str] = None


class BookMetadataGenerator:
    """
    Professional generator for front matter and back matter components
    following traditional publishing standards.
    """

    def __init__(self, metadata: BookMetadata):
        self.metadata = metadata
        if not self.metadata.copyright_year:
            self.metadata.copyright_year = str(datetime.now().year)

    def _get_genre_disclaimer(self) -> str:
        """Generate appropriate legal disclaimer based on genre."""
        genre_lower = self.metadata.genre.lower()
        
        # Fiction disclaimers
        fiction_keywords = ['fiction', 'novel', 'story', 'fantasy', 'sci-fi', 
                          'science fiction', 'romance', 'mystery', 'thriller',
                          'horror', 'noir', 'literary']
        
        if any(keyword in genre_lower for keyword in fiction_keywords):
            return (
                "This is a work of fiction. Names, characters, places, and incidents "
                "either are the product of the author's imagination or are used fictitiously. "
                "Any resemblance to actual persons, living or dead, events, or locales "
                "is entirely coincidental."
            )
        
        # Non-fiction disclaimers
        non_fiction_keywords = ['non-fiction', 'nonfiction', 'biography', 'memoir',
                               'self-help', 'business', 'history', 'science', 'technical']
        
        if any(keyword in genre_lower for keyword in non_fiction_keywords):
            return (
                "This book is intended for informational purposes only. While the author "
                "and publisher have made every effort to ensure the accuracy of the "
                "information presented, they assume no responsibility for errors, "
                "omissions, or contrary interpretation of the subject matter herein. "
                "Any perceived slight of any individual or organization is unintentional."
            )
        
        # Default generic disclaimer
        return (
            "No part of this publication may be reproduced, distributed, or transmitted "
            "in any form or by any means without the prior written permission of the "
            "publisher, except in the case of brief quotations embodied in critical "
            "reviews and certain other noncommercial uses permitted by copyright law."
        )

    def generate_half_title(self) -> str:
        """Generate minimalist half title page."""
        return f"# {self.metadata.title.upper()}\n"

    def generate_title_page(self) -> str:
        """Generate full title page with all bibliographic elements."""
        lines = [f"# {self.metadata.title.upper()}"]
        
        if self.metadata.subtitle:
            lines.append(f"\n*{self.metadata.subtitle}*")
        
        lines.append(f"\n### **{self.metadata.author}**")
        lines.append(f"\n*{self.metadata.publisher}*")
        
        return "\n".join(lines)

    def generate_copyright_page(self) -> str:
        """Generate complete copyright page with legal notices."""
        lines = ["### COPYRIGHT"]
        lines.append(f"Copyright © {self.metadata.copyright_year} by {self.metadata.author}")
        lines.append("All rights reserved.\n")
        lines.append(f"Published by {self.metadata.publisher}\n")
        
        # Add genre-appropriate disclaimer
        lines.append(self._get_genre_disclaimer())
        lines.append("")
        
        # ISBNs
        if self.metadata.isbn_print or self.metadata.isbn_ebook:
            if self.metadata.isbn_print:
                lines.append(f"ISBN (Print): {self.metadata.isbn_print}")
            if self.metadata.isbn_ebook:
                lines.append(f"ISBN (E-book): {self.metadata.isbn_ebook}")
        else:
            lines.append("ISBN (Print): 978-X-XXX-XXXXX-X")
            lines.append("ISBN (E-book): 978-X-XXX-XXXXX-X")
        
        lines.append("")
        
        # LCCN
        if self.metadata.lccn:
            lines.append(f"Library of Congress Control Number: {self.metadata.lccn}")
        else:
            lines.append("Library of Congress Control Number: [Pending]")
        
        lines.append("")
        lines.append(f"{self.metadata.edition}")
        lines.append(f"Printed in the {self.metadata.city}")
        
        return "\n".join(lines)

    def generate_dedication(self) -> str:
        """Generate dedication page."""
        if self.metadata.dedication:
            return f"### DEDICATION\n\n*{self.metadata.dedication}*"
        else:
            return "### DEDICATION\n\n*For those who journey through words.*"

    def generate_table_of_contents(self, chapter_titles: Optional[List[str]] = None) -> str:
        """Generate table of contents structure."""
        lines = ["## TABLE OF CONTENTS"]
        lines.append("")
        
        # Front matter entries (not numbered typically)
        lines.append("- [Title Page](#title-page)")
        lines.append("- [Copyright](#copyright)")
        lines.append("- [Dedication](#dedication)")
        
        # Chapter entries
        if chapter_titles:
            for idx, title in enumerate(chapter_titles, start=1):
                lines.append(f"- [Chapter {idx}: {title}](#chapter-{idx})")
        else:
            # Placeholder for unknown chapters
            lines.append("- [Chapter 1](#chapter-1)")
            lines.append("- [Chapter 2](#chapter-2)")
            lines.append("- [Chapter 3](#chapter-3)")
            lines.append("...")
        
        # Back matter entries
        lines.append("")
        lines.append("### Back Matter")
        lines.append("- [Acknowledgements](#acknowledgements)")
        lines.append("- [About the Author](#about-the-author)")
        lines.append("- [Also By](#also-by)")
        
        return "\n".join(lines)

    def generate_acknowledgements(self) -> str:
        """Generate acknowledgements section."""
        if self.metadata.acknowledgements:
            return f"### ACKNOWLEDGEMENTS\n\n{self.metadata.acknowledgements}"
        else:
            return (
                "### ACKNOWLEDGEMENTS\n\n"
                "The author gratefully acknowledges the support of:\n\n"
                "- Family and friends for their endless patience and encouragement\n"
                "- Beta readers and critique partners for their invaluable feedback\n"
                "- Editors and proofreaders for their meticulous attention to detail\n"
                "- All readers who make this journey possible\n\n"
                "*Thank you.*"
            )

    def generate_about_author(self) -> str:
        """Generate about the author section."""
        lines = ["### ABOUT THE AUTHOR"]
        
        if self.metadata.author_bio:
            lines.append(self.metadata.author_bio)
        else:
            lines.append(
                f"{self.metadata.author} is an author whose work spans multiple genres. "
                "Passionate about storytelling and craft, they continue to explore new "
                "narratives and connect with readers worldwide."
            )
        
        # Add contact/social links
        links = []
        if self.metadata.author_website:
            links.append(f"Website: [{self.metadata.author_website}]({self.metadata.author_website})")
        else:
            links.append("Website: [www.authorwebsite.com](http://www.authorwebsite.com)")
        
        links.append("Find more works by this author at your favorite online retailers.")
        
        lines.append("")
        lines.append("\n".join(links))
        
        return "\n".join(lines)

    def generate_also_by(self) -> str:
        """Generate 'Also By' section."""
        lines = ["### ALSO BY", "", f"**{self.metadata.author}**", ""]
        
        if self.metadata.other_books:
            for book in self.metadata.other_books:
                lines.append(f"- *{book}*")
        else:
            lines.append("*Coming Soon*")
            lines.append("")
            lines.append("Stay tuned for upcoming releases and new adventures.")
        
        return "\n".join(lines)

    def generate_excerpt_teaser(self, next_book_title: Optional[str] = None) -> str:
        """Generate excerpt/teaser section for next book."""
        lines = ["### EXCLUSIVE PREVIEW"]
        lines.append("")
        
        if next_book_title:
            lines.append(f"*From the upcoming release:*")
            lines.append(f"# {next_book_title.upper()}")
            lines.append("")
            lines.append("[Insert excerpt from next book here...]")
        else:
            lines.append("*From the next adventure in this series...*")
            lines.append("")
            lines.append("[Excerpt coming soon]")
        
        return "\n".join(lines)

    def generate_call_to_action(self) -> str:
        """Generate reader call-to-action for reviews."""
        return (
            "### ENJOYED THIS BOOK?\n\n"
            f"If you enjoyed *{self.metadata.title}*, please consider leaving an honest review "
            "on Amazon, Goodreads, or your favorite retailer. Reader reviews make a massive "
            "difference in helping books find their audience!\n\n"
            "Thank you for your support! 📚✨"
        )

    def generate_front_matter(self, chapter_titles: Optional[List[str]] = None) -> str:
        """Generate complete front matter section."""
        sections = [
            self.generate_half_title(),
            "---",
            self.generate_title_page(),
            "---",
            self.generate_copyright_page(),
            "---",
            self.generate_dedication(),
            "---",
            self.generate_table_of_contents(chapter_titles)
        ]
        
        return "\n\n".join(sections)

    def generate_back_matter(self, next_book_title: Optional[str] = None) -> str:
        """Generate complete back matter section."""
        sections = [
            "## BACK MATTER",
            "",
            self.generate_acknowledgements(),
            "---",
            self.generate_about_author(),
            "---",
            self.generate_also_by(),
            "---",
            self.generate_excerpt_teaser(next_book_title),
            "---",
            self.generate_call_to_action()
        ]
        
        return "\n\n".join(sections)

    def generate_complete_manuscript_structure(
        self, 
        chapter_titles: Optional[List[str]] = None,
        next_book_title: Optional[str] = None
    ) -> str:
        """Generate complete front and back matter with proper separation."""
        front = self.generate_front_matter(chapter_titles)
        back = self.generate_back_matter(next_book_title)
        
        return f"{front}\n\n---\n\n{back}"


def create_metadata_generator(
    title: str,
    author: str,
    subtitle: Optional[str] = None,
    genre: str = "Fiction",
    copyright_year: Optional[str] = None,
    publisher: str = "Independent Press",
    **kwargs
) -> BookMetadataGenerator:
    """
    Factory function to create a BookMetadataGenerator with provided metadata.
    
    Args:
        title: Book title
        author: Author name
        subtitle: Optional subtitle
        genre: Book genre
        copyright_year: Copyright year (defaults to current year)
        publisher: Publisher/imprint name
        **kwargs: Additional metadata fields
    
    Returns:
        Configured BookMetadataGenerator instance
    """
    metadata = BookMetadata(
        title=title,
        author=author,
        subtitle=subtitle,
        genre=genre,
        copyright_year=copyright_year,
        publisher=publisher,
        **kwargs
    )
    
    return BookMetadataGenerator(metadata)
