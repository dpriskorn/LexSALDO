# LexSALDO
This is a project to analyze and add identifiers for words 
from SALDO to Wikidata.

## TODO
* investigate if a unique identifier is present for both entries and senses.

## API
An API has been added for easy lookup. The goal is to upload it to Toolforge to facilitate
integration of the data into Wikidata via a property since 
this might be a good freely licensed source for Swedish lexemes to use.

## Versioning
The output jsonl is versioned v1, v2, etc.
The latest number is always consistent with the model in the code, 
old versions are kept for backwards compatibility.

## Statistics
Ingångar: 131 020

## License
The source code is licensed under GPLv3+
The data directory files are CC-BY 4.0

## Source
Original source is https://spraakbanken.gu.se/resurser/saldo and https://svn.spraakdata.gu.se/sb-arkiv/pub/lmf/saldo/saldo.xml
The data was downloaded during may 2024.
No updates to the dump seem to happen over time since 2017. The project seems to have been mothballed.

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