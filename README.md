# LexSALDO
This is a project to analyze and add identifiers for lexemes and senses in SALDO version 2017-09-19 to Wikidata.
A unique UUID-based identifier have been added to lexical entries to facilitate linking with Wikidata 
if the community for some reason do not want to use the existing ones..

## Data model
The data model of SALDO is the same as the one in Wikidata.
* lexical_entry = lexeme in Wikidata
* sense = sense in Wikidata

Both senses and lexical entries have unique ids. 
The id of lexical entries is called `lemgram` by the source.

## API
An API has been added for easy lookup of lexical entries since that is currently missing on the website, see below. 
The goal is to upload it to Toolforge to facilitate
integration of the data into Wikidata via a property since 
this might be a good freely licensed source for Swedish lexemes to use.

## Versioning
The output jsonl is versioned v1, v2, etc.
The latest number is always consistent with the model in the code, 
old versions are kept for backwards compatibility.

## Statistics
Ingångar: 131 020 <- number from source page

Total lexical entries: 131019
Lexical entries with at least one sense: 131019
Total unique senses: 131019
Total sense relations: 192024
Average sense relations per sense: 1.5

## License
The source code is licensed under GPLv3+
The data directory files are CC-BY 4.0

## Source
See https://www.wikidata.org/wiki/Q126120096
Original source is https://spraakbanken.gu.se/resurser/saldo 
and https://svn.spraakdata.gu.se/sb-arkiv/pub/lmf/saldo/saldo.xml
The data was downloaded during may 2024.
No updates to the dump seem to happen over time since 2017. 
The project seems to have been mothballed.

The saldo-ws website enables lookups based on lemma and sense ids. 
* https://spraakbanken.gu.se/ws/saldo-ws/fl/html?segment=$1 for lemmas
* https://spraakbanken.gu.se/ws/saldo-ws/lid/html/$1 for sense ids

## Development
Run the api:
`$ uvicorn api:app --reload`

Build pack:

Make sure pack-cli-bin and docker is installed from AUR:
```
$ pack build --builder tools-harbor.wmcloud.org/toolforge/heroku-builder:22 myimage
$ docker run -e PORT=8000 -p 8000:8000 --rm --entrypoint web myimage
# navigate to http://127.0.0.1:8000 to check that it works
```