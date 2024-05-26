import logging
import uuid
from typing import List

from pydantic import BaseModel

from models.lemma import Lemma
from models.sense import Sense

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
