import logging
import uuid
from typing import List

import jsonlines
from bs4 import BeautifulSoup
from pydantic import BaseModel

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

"""
Sources:
https://spraakbanken.gu.se/parole/Docs/SUC2.0-manual.pdf
https://www.diva-portal.org/smash/get/diva2:656074/FULLTEXT01.pdf
https://fileadmin.cs.lth.se/cs/Education/EDA171/Reports/2007/peter.pdf
"""
pos_mapping = {
    "abbrev": "Q102786",  # abbreviation
    "jj": "Q34698",  # adjective # see https://fileadmin.cs.lth.se/cs/Personal/Pierre_Nugues/ilppp/slides/ch07.pdf
    "rg": "Q163875",  # cardinal number
    "prefix": "Q134830",  # prefix
    "article": "Q103184",  # article
    "suffix": "Q102047",  # suffix
    "hp": "Q1050744",  # relative pronoun
    "ps": "Q1502460",  # possessive pronoun
    "nn": "Q1084",  # noun
    "av": "Q34698",  # adjective
    "vb": "Q24905",  # verb
    "pm": "Q147276",  # proper noun
    "ab": "Q192420",  # adverb
    "in": "Q198061",  # interjection
    "pp": "Q168713",  # preposition
    "nl": "Q13164",  # numeral
    "pn": "Q149667",  # pronoun
    "sn": "Q107715",  # subjunction
    "kn": "Q11376",  # conjunction
    "al": "Q7247",  # article
    "ie": "Q213443",  # infinitive particle
    "mxc": "Q4115189",  # multiword prefix
    "sxc": "Q59019669",  # prefix
    "abh": "Q15563735",  # adverb suffix
    "avh": "Q5307395",  # adjective suffix
    "nnh": "Q4961746",  # noun suffix
    "nnm": "Q724908",  # multiword noun
    "nna": "Q1077132",  # noun, abbreviation
    "avm": "Q729",  # multiword adjective
    "ava": "Q25132092",  # adjective, abbreviation
    "vbm": "Q181714",  # multiword verb
    "vba": "Q4231319",  # verb, abbreviation
    "pmm": "Q188627",  # multiword proper noun
    "pma": "Q24888353",  # proper noun, abbreviation
    "abm": "Q6734441",  # multiword adverb
    "aba": "Q40482579",  # adverb, abbreviation
    "pnm": "Q10828648",  # multiword pronoun
    "inm": "Q69556741",  # multiword interjection
    "ppm": "Q30840955",  # multiword preposition
    "ppa": "Q32736580",  # preposition, abbreviation
    "nlm": "Q22069880",  # multiword numeral
    "knm": "Q69559303",  # multiword conjunction
    "snm": "Q69559308",  # multiword subjunction
    "kna": "Q69559304",  # conjunction, abbreviation
    "ssm": "Q69559307",  # multiword, clause
}

def get_lexical_category(pos: str) -> str:
    if pos in pos_mapping:
        return pos_mapping[pos]
    elif not pos:
        # we ignore this for now
        return ""
    else:
        raise ValueError(
            "No matching QID found for word class: {}".format(pos)
        )


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
    sense_relations: List[SenseRelation] = []

    @classmethod
    def from_soup(cls, soup):
        sense_relations = [
            SenseRelation.from_soup(sr) for sr in soup.find_all("SenseRelation")
        ]
        return cls(id=soup["id"], sense_relations=sense_relations)



class LexicalEntry(BaseModel):
    lemma: Lemma
    senses: List[Sense]
    lemgram: str  # we want a validation error if no lemgram is found
    entry_id: str
    part_of_speech: str # we want a validation error if no part_of_speech is found
    wd_lexical_category: str

    @classmethod
    def from_soup(cls, soup):
        lemma = soup.find("Lemma")
        if not lemma:
            logger.warning(f"no lemma found in soup: {soup}")
        else:
            lemgram_node = soup.find("Lemma").find("feat", {"att": "lemgram"})
            if lemgram_node is None:
                # This seems to be some kind of root node
                # for the senses with no content.
                logger.warning(
                    f"no lemgram node found in soup: {soup}. Ignoring the entry"
                )
                return None
            part_of_speech_node = soup.find("Lemma").find("feat", {"att": "partOfSpeech"})
            if part_of_speech_node is None:
                logger.warning(
                    f"no lemgram node found in soup: {soup}."
                )
                return None
            else:
                lemgram = lemgram_node["val"]
                part_of_speech = part_of_speech_node["val"]
                senses = [Sense.from_soup(sense) for sense in soup.find_all("Sense")]
                return cls(
                    lemma=Lemma.from_soup(lemma) if lemma else None,
                    senses=senses,
                    lemgram=lemgram,
                    entry_id=str(uuid.uuid4())[:6],  # Generate unique ID
                    part_of_speech=part_of_speech,
                    wd_lexical_category=get_lexical_category(pos=part_of_speech)
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

    def output_to_jsonl(self, file_path: str = "data/lexsaldo_v1.jsonl"):
        if not self.verify_unique:
            raise ValueError("the generated ids of lexical_entries are not unique")
        with jsonlines.open(file_path, mode="w") as writer:
            for entry in self.lexicon.lexical_entries:
                writer.write(entry.model_dump())

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


file_path = "data/saldo.xml"  # replace with your actual file path
lexical_resource = LexicalResource.from_file(file_path)
lexical_resource.output_to_jsonl()
print("Total lexical entries:", lexical_resource.count_lexical_entries())
print("lexical entries with at least one sense:", lexical_resource.count_senses())
print("Total unique senses:", lexical_resource.count_unique_senses())
print("Total sense relations:", lexical_resource.count_total_sense_relations())
print(
    "Average number of sense relations per sense:",
    lexical_resource.calculate_avg_sense_relations_per_sense(),
)
