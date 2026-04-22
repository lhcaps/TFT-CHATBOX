# TFT Set 17 / Patch 17.1 — Clean Rebuild Pack

## What this pack contains
This rebuild is designed for a clean ingest baseline for **Set 17: Space Gods** on **patch 17.1**.

Included:
- set mechanic and god system summary
- patch 17.1B system and balance highlights
- origins / vertical traits
- classes
- full current roster with costs + traits
- standard craftable item list + recipes
- explicit Radiant items surfaced in current search results
- Psionic items
- Anima weapons
- artifact pool names
- current meta comp snapshot

## What is intentionally omitted
Anything I could not verify from current reliable sources is omitted instead of guessed:
- full per-champion base stats
- exact mana / AP / AD scaling for every unit
- exact full text for every standard / radiant item not surfaced in snippets
- full augment catalog

## Recommended ingest split
1. `/patches`
2. `/systems`
3. `/traits/origins`
4. `/traits/classes`
5. `/champions`
6. `/items/combined`
7. `/items/psionic`
8. `/items/anima_weapons`
9. `/items/artifacts`
10. `/meta_comps`

## Suggested validation rules
- `cost` must be 1..5
- `traits[]` must refer to an existing origin or class or singleton trait
- no duplicate champion names
- no duplicate item names within a category
- every meta comp carry must exist in the champion roster
- preserve `patch` and `generated_on` for re-ingest versioning

## Suggested next scraper pass
If you want a production-grade DB, do a second pass for:
- champion spell text
- mana values
- stats
- full augment pool
- exact artifact and radiant numeric values

This file pairs with:
- `tft_set17_patch17_1_data_pack.json`
- `tft_set17_patch17_1_schema.json`