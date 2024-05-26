from pydantic import BaseModel


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
