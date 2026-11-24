import re
from typing import List


class TextChunker:
    def __init__(self, chunk_size: int = 512, overlap: int = 128):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def clean_text(self, text: str) -> str:
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def split_by_paragraphs(self, text: str) -> List[str]:
        paragraphs = re.split(r'\n\s*\n', text)
        return [p.strip() for p in paragraphs if p.strip()]

    def chunk(self, text: str) -> List[str]:
        text = self.clean_text(text)
        paragraphs = self.split_by_paragraphs(text)

        if len(paragraphs) <= 1:
            text = text.replace('\n', ' ')
            return self._split_by_size(text)

        chunks = []
        current_chunk = ""

        for para in paragraphs:
            if not current_chunk:
                current_chunk = para
            elif len(current_chunk) + 1 + len(para) <= self.chunk_size:
                current_chunk += "\n\n" + para
            else:
                chunks.append(current_chunk.strip())
                overlap_text = self._get_overlap(current_chunk)
                current_chunk = overlap_text + "\n\n" + para if overlap_text else para

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _split_by_size(self, text: str) -> List[str]:
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            if end < len(text):
                last_space = text.rfind(' ', start, end + 1)
                if last_space > start:
                    end = last_space
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start = end - self.overlap if end < len(text) else len(text)
        return chunks

    def _get_overlap(self, chunk: str) -> str:
        words = chunk.split()
        overlap_words = []
        char_count = 0
        for word in reversed(words):
            if char_count + len(word) + 1 > self.overlap:
                break
            overlap_words.insert(0, word)
            char_count += len(word) + 1
        return " ".join(overlap_words)