import logging
import uuid
from typing import List, Optional

import jsonlines
from pydantic import BaseModel
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class FormRepresentation(BaseModel):
    writtenForm: str
    partOfSpeech: str
    lemgram: str
    paradigm: str

    @classmethod
    def from_soup(cls, soup):
        feats = {feat["att"]: feat["val"] for feat in soup.find_all("feat")}
        return cls(
            writtenForm=feats["writtenForm"],
            partOfSpeech=feats["partOfSpeech"],
            lemgram=feats["lemgram"],
            paradigm=feats["paradigm"],
        )


class Lemma(BaseModel):
    form_representation: List[FormRepresentation] = []

    @classmethod
    def from_soup(cls, soup):
        form_representations = [
            FormRepresentation.from_soup(fr)
            for fr in soup.find_all("FormRepresentation")
        ]
        if not form_representations:
            logger.warning(f"no representations found for soup: {soup}")
        return cls(form_representation=form_representations)


class SenseRelation(BaseModel):
    targets: str
    label: str

    @classmethod
    def from_soup(cls, soup):
        feats = {feat["att"]: feat["val"] for feat in soup.find_all("feat")}
        return cls(targets=soup["targets"], label=feats["label"])


class Sense(BaseModel):
    id: str
    sense_relation: Optional[SenseRelation] = None

    @classmethod
    def from_soup(cls, soup):
        sense_relation = soup.find("SenseRelation")
        return cls(
            id=soup["id"],
            sense_relation=SenseRelation.from_soup(sense_relation)
            if sense_relation
            else None,
        )


class LexicalEntry(BaseModel):
    lemma: Lemma
    sense: List[Sense]
    # Not all entries have a lemma with a lemgram so
    # lemgram is not a good unique identifier for lexical entries
    lemgram: str  # we want a validation error if no lemgram is found
    entry_id: str

    @classmethod
    def from_soup(cls, soup):
        lemma = soup.find("Lemma")
        if not lemma:
            logger.warning(f"no lemma found in soup: {soup}")
        else:
            lemgram_node = soup.find('Lemma').find('feat', {'att': 'lemgram'})
            if lemgram_node is None:
                # This seems to be some kind of root node for the senses with no content.
                logger.warning(f"no lemgram node found in soup: {soup}. Ignoring the entry")
                return None
            else:
                lemgram = lemgram_node['val']
                senses = [Sense.from_soup(sense) for sense in soup.find_all("Sense")]
                return cls(
                    lemma=Lemma.from_soup(lemma) if lemma else None,
                    sense=senses,
                    lemgram=lemgram,
                    entry_id=str(uuid.uuid4())[:6],  # Generate unique ID
                )


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
        lexical_entries = [l for l in lexical_entries if l is not None]
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
            sense.id for entry in self.lexicon.lexical_entries for sense in entry.sense
        ]
        return len(lexical_entry_ids) == len(set(lexical_entry_ids))

    def output_to_jsonl(self, file_path: str = "data/lexsaldo_v1.jsonl"):
        if not self.verify_unique:
            raise ValueError("the generated ids of lexical_entries are not unique")
        with jsonlines.open(file_path, mode="w") as writer:
            for entry in self.lexicon.lexical_entries:
                writer.write(entry.model_dump())


# Example usage:
file_path = "data/saldo.xml"  # replace with your actual file path
lexical_resource = LexicalResource.from_file(file_path)
lexical_resource.output_to_jsonl()
# print(lexical_resource.json(indent=2))
