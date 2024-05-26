from typing import List

from pydantic import BaseModel

from models.form_representation import FormRepresentation


class Lemma(BaseModel):
    form_representations: List[FormRepresentation] = []

    @classmethod
    def from_soup(cls, soup):
        form_representations = [
            FormRepresentation.from_soup(fr)
            for fr in soup.find_all("FormRepresentation")
        ]
        if not form_representations:
            logger.warning(f"no representations found for soup: {soup}")
        return cls(form_representations=form_representations)
