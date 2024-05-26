from typing import List

from pydantic import BaseModel

from models.sense_relation import SenseRelation


class Sense(BaseModel):
    id: str
    sense_relations: List[SenseRelation] = []

    @classmethod
    def from_soup(cls, soup):
        sense_relations = [
            SenseRelation.from_soup(sr) for sr in soup.find_all("SenseRelation")
        ]
        return cls(id=soup["id"], sense_relations=sense_relations)

    # @property
    # def url(self):
    #     return f"https://spraakbanken.gu.se/ws/saldo-ws/lid/html/{self.id}"

    # async def check_sense_url(self, session):
    #     """Check if the senseexists at the URL."""
    #     if self.url:
    #         async with session.head(self.url) as response:
    #             if response.status in [200, 405, 502]:
    #                 self.sense_url_found = True
    #             elif response.status in [404]:
    #                 self.sense_url_found = False
    #             else:
    #                 raise Exception(f"Unexpected response code: {response.status} for URL: {self.url}")
