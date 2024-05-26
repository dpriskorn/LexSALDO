import csv
import logging
from pathlib import Path
from typing import List

import jsonlines
from bs4 import BeautifulSoup
from pydantic import BaseModel

from models.lexical_entry import LexicalEntry

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

version = "v1"
# DISABLED lookup because we got errors and timeouts
# lookup_url = False


class Lexicon(BaseModel):
    language: str
    lexical_entries: List[LexicalEntry]

    @classmethod
    def from_soup(cls, soup):
        language = soup.find("feat", {"att": "language"})["val"]
        lexical_entries = [
            LexicalEntry.from_soup(le) for le in soup.find_all("LexicalEntry")
        ]
        # remove None from the list
        lexical_entries = [entry for entry in lexical_entries if entry is not None]
        return cls(language=language, lexical_entries=lexical_entries)


class GlobalInformation(BaseModel):
    languageCoding: str

    @classmethod
    def from_soup(cls, soup):
        language_coding = soup.find("feat", {"att": "languageCoding"})["val"]
        return cls(languageCoding=language_coding)


class LexicalResource(BaseModel):
    dtdVersion: str
    GlobalInformation: GlobalInformation
    lexicon: Lexicon

    @classmethod
    def from_xml(cls, xml_content):
        soup = BeautifulSoup(xml_content, "xml")
        dtd_version = soup.find("LexicalResource")["dtdVersion"]
        global_information = GlobalInformation.from_soup(soup.find("GlobalInformation"))
        lexicon = Lexicon.from_soup(soup.find("Lexicon"))
        return cls(
            dtdVersion=dtd_version,
            GlobalInformation=global_information,
            lexicon=lexicon,
        )

    @classmethod
    def from_file(cls, file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            xml_content = file.read()
        return cls.from_xml(xml_content)

    @property
    def verify_unique(self):
        """Count number of lexical_entries and add all ids to a set.
        Then verify that the set and count is the same"""
        lexical_entry_ids = [
            sense.id for entry in self.lexicon.lexical_entries for sense in entry.senses
        ]
        return len(lexical_entry_ids) == len(set(lexical_entry_ids))

    def verify_lookup_and_output(self):
        if not self.verify_unique:
            raise ValueError("the generated ids of lexical_entries are not unique")
        # if lookup_url:
        #     asyncio.run(self.update_sense_url_status())
        self.save_outputs_to_disk()

    def save_outputs_to_disk(self):
        self.output_to_jsonl()
        self.output_to_csv()

    def output_to_jsonl(self, file_path: str = f"data/lexsaldo_{version}.jsonl"):
        with jsonlines.open(file_path, mode="w") as writer:
            for entry in self.lexicon.lexical_entries:
                writer.write(entry.model_dump())

    def output_to_csv(self, version: str = version):
        """This outputs 2 csv files for mishramilan, see https://mishramilan.toolforge.org/
        1) one with columns writtenForm, part_of_speech, lemgram for each form_representation
        2) one with columns writtenForm, sense_id for each lemma"""
        data_dir = Path("data")
        data_dir.mkdir(parents=True, exist_ok=True)

        # Prepare data for the first CSV file
        form_representation_data = []
        for entry in self.lexicon.lexical_entries:
            if entry.lemma:
                for form_rep in entry.lemma.form_representations:
                    form_representation_data.append([
                        form_rep.writtenForm,
                        entry.wd_lexical_category,
                        form_rep.lemgram
                    ])

        form_representation_csv_path = data_dir / f"form_representation_{version}.csv"
        with form_representation_csv_path.open(mode="w", newline='', encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["writtenForm", "lexical_category", "lemgram"])
            writer.writerows(form_representation_data)

        # Prepare data for the second CSV file
        lemma_sense_data = []
        for entry in self.lexicon.lexical_entries:
            if entry.lemma:
                written_forms = [form_rep.writtenForm for form_rep in entry.lemma.form_representations]
                for sense in entry.senses:
                    for written_form in written_forms:
                        lemma_sense_data.append([
                            written_form,
                            entry.wd_lexical_category,
                            sense.id,
                        ])

        lemma_sense_csv_path = data_dir / f"senses_{version}.csv"
        with lemma_sense_csv_path.open(mode="w", newline='', encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["writtenForm", "lexical_category", "sense_id"])
            writer.writerows(lemma_sense_data)

    def count_lexical_entries(self):
        """Count the number of lexical entries."""
        return len(self.lexicon.lexical_entries)

    def count_senses(self):
        """Count the number of senses."""
        return sum(len(entry.senses) for entry in self.lexicon.lexical_entries)

    def count_unique_senses(self):
        """Count the number of unique senses based on Sense.id."""
        sense_ids = [
            sense.id for entry in self.lexicon.lexical_entries for sense in entry.senses
        ]
        return len(set(sense_ids))

    def count_total_sense_relations(self):
        """Count the total number of sense relations."""
        sense_relations = [
            sense_relation
            for entry in self.lexicon.lexical_entries
            for sense in entry.senses
            for sense_relation in sense.sense_relations
        ]
        return len(sense_relations)

    def calculate_avg_sense_relations_per_sense(self):
        """Calculate the average number of sense relations per sense."""
        total_senses = sum(len(entry.senses) for entry in self.lexicon.lexical_entries)
        total_sense_relations = self.count_total_sense_relations()

        if total_senses == 0:
            return 0

        return round(total_sense_relations / total_senses, 1)

    # async def update_sense_url_status(self):
    #     print("Looking up senses on https://spraakbanken.gu.se/ws/saldo-ws/lid/html/")
    #     # We limit number of parallel connections because we get a ServerDisconnectedError
    #     connector = aiohttp.TCPConnector(limit=150, force_close=True)
    #     async with aiohttp.ClientSession(connector=connector) as session:
    #         tasks = []
    #         for entry in self.lexicon.lexical_entries:
    #             for sense in entry.senses:
    #                 tasks.append(sense.check_sense_url(session))
    #         try:
    #             await tqdm_asyncio.gather(*tasks)
    #         except (TimeoutError, ClientConnectorError):
    #             print("Got an error, skipping lookup")

file_path = "data/saldo.xml"  # replace with your actual file path
lexical_resource = LexicalResource.from_file(file_path)
lexical_resource.verify_lookup_and_output()
print("Total lexical entries:", lexical_resource.count_lexical_entries())
print("lexical entries with at least one sense:", lexical_resource.count_senses())
print("Total unique senses:", lexical_resource.count_unique_senses())
print("Total sense relations:", lexical_resource.count_total_sense_relations())
print(
    "Average number of sense relations per sense:",
    lexical_resource.calculate_avg_sense_relations_per_sense(),
)
