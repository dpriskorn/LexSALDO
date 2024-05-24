"""
<?xml version="1.0" encoding="utf-8"?>
<!-- $Id: saldo.xml 167452 2017-07-04 00:36:44Z jonatan $ -->
<LexicalResource dtdVersion="16">
  <GlobalInformation>
    <feat att="languageCoding" val="ISO 639-3" />
  </GlobalInformation>
  <Lexicon>
    <feat att="language" val="swe" />
    <LexicalEntry>
      <Lemma />
      <Sense id="PRIM..1" />
    </LexicalEntry>
    <LexicalEntry>
      <Lemma>
        <FormRepresentation>
          <feat att="writtenForm" val="a-bomb" />
          <feat att="partOfSpeech" val="nn" />
          <feat att="lemgram" val="a-bomb..nn.1" />
          <feat att="paradigm" val="nn_3u_salong" />
        </FormRepresentation>
        <FormRepresentation>
          <feat att="writtenForm" val="A-bomb" />
          <feat att="partOfSpeech" val="nn" />
          <feat att="lemgram" val="A-bomb..nn.1" />
          <feat att="paradigm" val="nn_3u_salong" />
        </FormRepresentation>
      </Lemma>
      <Sense id="A-bomb..1">
        <SenseRelation targets="atombomb..1">
          <feat att="label" val="primary" />
        </SenseRelation>
      </Sense>
    </LexicalEntry>
"""
import logging
import uuid
from typing import List, Optional

import jsonlines
from pydantic import BaseModel
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# class Feat(BaseModel):
#     att: str
#     val: str
#
#     @classmethod
#     def from_soup(cls, soup):
#         return cls(att=soup["att"], val=soup["val"])


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
        return cls(FormRepresentation=form_representations)


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
    lemma: Optional[Lemma] = None
    sense: List[Sense]
    # Not all entries have a lemma with a lemgram so
    # lemgram is not a good unique identifier for lexical entries
    # lemgram: str  # we want a validation error if no lemgram is found
    entry_id: str

    @classmethod
    def from_soup(cls, soup):
        lemma = soup.find("Lemma")
        # lemgram = soup.find('Lemma').find('feat', {'att': 'lemgram'})['val']
        senses = [Sense.from_soup(sense) for sense in soup.find_all("Sense")]
        return cls(
            lemma=Lemma.from_soup(lemma) if lemma else None,
            sense=senses,
            # lemgram=lemgram,
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
