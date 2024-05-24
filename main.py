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

from typing import List, Optional
from pydantic import BaseModel
from bs4 import BeautifulSoup

class Feat(BaseModel):
    att: str
    val: str

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
        feats = {feat['att']: feat['val'] for feat in soup.find_all('feat')}
        return cls(
            writtenForm=feats['writtenForm'],
            partOfSpeech=feats['partOfSpeech'],
            lemgram=feats['lemgram'],
            paradigm=feats['paradigm']
        )

class Lemma(BaseModel):
    FormRepresentation: List[FormRepresentation]

    @classmethod
    def from_soup(cls, soup):
        form_representations = [FormRepresentation.from_soup(fr) for fr in soup.find_all('FormRepresentation')]
        return cls(FormRepresentation=form_representations)

class SenseRelation(BaseModel):
    targets: str
    label: str

    @classmethod
    def from_soup(cls, soup):
        feats = {feat['att']: feat['val'] for feat in soup.find_all('feat')}
        return cls(
            targets=soup['targets'],
            label=feats['label']
        )

class Sense(BaseModel):
    id: str
    SenseRelation: Optional[SenseRelation] = None

    @classmethod
    def from_soup(cls, soup):
        sense_relation = soup.find('SenseRelation')
        return cls(
            id=soup['id'],
            SenseRelation=SenseRelation.from_soup(sense_relation) if sense_relation else None
        )

class LexicalEntry(BaseModel):
    Lemma: Optional[Lemma] = None
    Sense: List[Sense]

    @classmethod
    def from_soup(cls, soup):
        lemma = soup.find('Lemma')
        senses = [Sense.from_soup(sense) for sense in soup.find_all('Sense')]
        return cls(
            Lemma=Lemma.from_soup(lemma) if lemma else None,
            Sense=senses
        )

class Lexicon(BaseModel):
    language: str
    LexicalEntry: List[LexicalEntry]

    @classmethod
    def from_soup(cls, soup):
        language = soup.find('feat', {'att': 'language'})['val']
        lexical_entries = [LexicalEntry.from_soup(le) for le in soup.find_all('LexicalEntry')]
        return cls(language=language, LexicalEntry=lexical_entries)

class GlobalInformation(BaseModel):
    languageCoding: str

    @classmethod
    def from_soup(cls, soup):
        language_coding = soup.find('feat', {'att': 'languageCoding'})['val']
        return cls(languageCoding=language_coding)

class LexicalResource(BaseModel):
    dtdVersion: str
    GlobalInformation: GlobalInformation
    Lexicon: Lexicon

    @classmethod
    def from_xml(cls, xml_content):
        soup = BeautifulSoup(xml_content, "xml")
        dtd_version = soup.find('LexicalResource')['dtdVersion']
        global_information = GlobalInformation.from_soup(soup.find('GlobalInformation'))
        lexicon = Lexicon.from_soup(soup.find('Lexicon'))
        return cls(dtdVersion=dtd_version, GlobalInformation=global_information, Lexicon=lexicon)

    @classmethod
    def from_file(cls, file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            xml_content = file.read()
        return cls.from_xml(xml_content)

    def output_to_jsonl(self, file_path: str = "data/folkets_lexicon_v2.jsonl"):
        with jsonlines.open(file_path, mode="w") as writer:
            for word in self.words:
                writer.write(word.get_output_dict)


# Example usage:
file_path = 'data/saldo.xml'  # replace with your actual file path
lexical_resource = LexicalResource.from_file(file_path)
print(lexical_resource.json(indent=2))
