from pydantic import BaseModel


class SenseRelation(BaseModel):
    targets: str
    label: str

    @classmethod
    def from_soup(cls, soup):
        feats = {feat["att"]: feat["val"] for feat in soup.find_all("feat")}
        return cls(targets=soup["targets"], label=feats["label"])
