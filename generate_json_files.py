import os
import shutil
import json
from typing import List

from pydantic import BaseModel

from models.lexical_entry import LexicalEntry


class LexiconProcessor(BaseModel):
    jsonl_path: str = "data/lexsaldo_v1.jsonl"
    lexical_entries: List[LexicalEntry] = []

    def _load_words(self):
        with open(self.jsonl_path, mode="r", encoding="utf-8") as file:
            for line in file:
                word = json.loads(line.strip())
                self.lexical_entries.append(word)

    def output_to_individual_json_files(self, directory_path: str = "data/v1"):
        self._load_words()
        # Remove existing directory if it exists
        shutil.rmtree(directory_path, ignore_errors=True)
        # Create the directory if it doesn't exist
        os.makedirs(directory_path, exist_ok=False)

        # Iterate over each Word and write it to a separate JSON file
        for word in self.lexical_entries:
            # Save word to JSON file
            word_file_path = os.path.join(directory_path, f"{word['lemgram']}.json")
            with open(word_file_path, mode="w", encoding="utf-8") as file:
                json.dump(word, file, ensure_ascii=False)

# Example usage:
processor = LexiconProcessor()
processor.output_to_individual_json_files()
