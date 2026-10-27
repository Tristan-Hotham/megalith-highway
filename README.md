# The Megalith Highway

Portugal, Galicia, Brittany, Ireland, Wales, Orkney and Scandinavia built recognisably the same great stone tombs. Did the idea travel by sea? 13,280 megalithic monuments from OpenStreetMap on one map, and three honest tests: distance to the coast, the earliest radiocarbon dates by region, and the Atlantic facade against inland Europe, type by type.

**Interactive version:** https://tristan-hotham.github.io/megalith-highway/

This repository holds the interactive page, the cleaned data and the analysis code for the data study *The Megalith Highway: Did the Idea of the Great Stone Tomb Travel by Sea?* by Dr Tristan Hotham (Independent researcher, ORCID 0000-0003-4931-9349). Companion studies from the same data pull: [Stone Circles](https://tristan-hotham.github.io/stone-circles/) and [Barrows of Europe](https://tristan-hotham.github.io/barrows-of-europe/).

## Headline results

- 13,280 megalithic monuments in 34 European countries, from 65,670 OpenStreetMap objects: 4,352 dolmens, 3,064 menhirs and standing stones, 1,345 stone circles, 1,142 nuraghi and talaiots, 5,752 tombs of all kinds.
- 29.1% stand within 10 km of the sea, against 12.8% of random land in the same countries (2.27 times) and 22.5% of non-megalithic barrows in the same country mix (1.29 times). The 95% interval for the megaliths, resampling 50 km cells, is 22.2% to 37.3%, so the gap over barrows is not secure.
- Tombs alone: 20.3% within 10 km against 15.8% of barrows. Menhirs, rows and circles: 35.1% against 20.7%.
- Radiocarbon: 254 monuments linked to p3k14c dates by name rules (42 of 50 sampled links correct, 7 unclear, 1 wrong). Tombs begin first in north-west France (10th percentile of start dates 4885 BC, 95% interval 5145 to 4382 BC, 13 tombs). Atlantic-facing regions start earlier than the rest (median 3465 against 2590 BC), but within regions an earlier start is not linked to being nearer the coast (Spearman 0.00, n = 118).
- Atlantic facade: 47% of megaliths lie within 50 km of the Atlantic and northern seas, against 27% of random land; long barrows 90%, stone rows 79%, stone circles 73%, but tombs as a whole 41%, the same as barrows (42%).

## Files

- `index.html`: the interactive page (Leaflet map drawn on one canvas, inline SVG charts). `header.png`: social card.
- `data/megaliths.csv`: one row per monument: OSM id, lat, lon, name, class, raw megalith_type and archaeological_site tags, normalised period tag and its source, Wikidata id, country, distance to the coast (km), nearest sea and zone.
- `data/tumuli_baseline.csv`: the non-megalithic barrows and tumuli used as the second baseline.
- `data/coast_by_country.csv`, `data/coast_bands.csv`: the coast test by country and by distance band.
- `data/radiocarbon_sites.csv`: every p3k14c site linked to a megalith, with the rule that linked it, the OSM monument, the earliest calibrated date in the window and its lab code. `primary` marks rules K or N; `dup_of_earlier` marks a second site name for the same monument.
- `data/radiocarbon_regions.csv`: start dates by region. `data/link_check.csv`: the 50 sampled links and the judgement on each.
- `data/zones_by_type.csv`: Atlantic, Mediterranean and inland shares by type, with baselines.
- `data/results.json`: every number quoted on the page, in the paper and in the blog post.
- `code/`: run in order `01_prepare.py`, `02_coast_test.py`, `03_radiocarbon.py`, `04_zones.py`, `05_link_check.py`, `build_site.py`, `make_header.py`. Step 1 writes a temporary `work/` folder used by steps 2 and 4.

## Method in brief

Monuments are OpenStreetMap objects tagged archaeological_site=megalith, megalith_type=*, or historic=menhir, standing_stone, stone_circle or dolmen, plus stone circles found by a multilingual name search and checked against tags and names. Points of the same type within 15 m were merged (2,809 removed). Ways and relations are placed at their first vertex, which is fine at map scale. Countries are from Natural Earth (European countries only).

Coast distances use the Natural Earth 1:10m coastline in the ETRS89 equal-area projection (EPSG:3035). Baseline A is ten random land points per monument in the same country; baseline B is the OSM barrows and tumuli without a megalithic tag, reweighted to the megaliths' country mix. Intervals come from a bootstrap over 50 km grid cells.

Radiocarbon dates are from p3k14c (uncalibrated; shell removed), calibrated individually with IntCal20 on a 5 year grid (median). The IntCal20 file comes from the rcarbon package (https://github.com/ahb108/rcarbon, `inst/extdata/intcal20.14c`; set the `INTCAL` environment variable to its path). A site is linked to a megalith if its name contains a megalithic keyword (rule K) or shares a distinctive word with the name of an OSM megalith within 1 km (rule N). A looser proximity rule (within 150 m, rule P) is reported as a sensitivity check. A monument's start is its earliest calibrated median between 5500 and 500 BC; regional starts are the 10th percentile of those, with 2,000 bootstrap resamples, for regions with at least eight dated tombs.

Caveats: OpenStreetMap coverage and tagging vary greatly by country (France 4,063 megaliths, Denmark 306, where 25,669 mounds are tagged as plain tumuli); radiocarbon coverage is densest in Britain and Ireland; the earliest date at a site can predate the monument; present coastlines are not Neolithic coastlines; and none of these tests can separate maritime spread from other explanations.

## Sources and licences

- Monuments: © OpenStreetMap contributors, Open Database Licence (ODbL 1.0), https://www.openstreetmap.org/copyright. Extract pulled from the QLever OSM planet endpoint on 27 October 2026.
- Radiocarbon dates: Bird, D., Miranda, L., Vander Linden, M. et al. 2022. p3k14c, a synthetic global database of archaeological radiocarbon dates. *Scientific Data* 9, 27. https://doi.org/10.1038/s41597-022-01118-7 (data CC0 1.0, attribution requested; https://github.com/people3k/p3k14c).
- Calibration: Reimer, P. et al. 2020. The IntCal20 Northern Hemisphere radiocarbon age calibration curve (0 to 55 cal kBP). *Radiocarbon* 62. https://doi.org/10.1017/RDC.2020.41
- Period and culture labels in part: Wikidata (CC0).
- Countries and coastline: Natural Earth (public domain).
- Base map tiles on the page: Esri, HERE, Garmin, © OpenStreetMap contributors, and the GIS user community. Map library: Leaflet.
- Literature: Schulz Paulsson, B. 2019. Radiocarbon dates and Bayesian modeling support maritime diffusion model for megaliths in Europe. *PNAS* 116 (9), 3460 to 3465. https://doi.org/10.1073/pnas.1813268116

**Licences.** The derived monument data in `data/` (which come from OpenStreetMap) are released under the Open Database Licence (ODbL 1.0); please credit "© OpenStreetMap contributors". Text and figures are CC BY 4.0. Code is MIT (see `LICENSE`).

## Citation

Hotham, T. 2026. *The Megalith Highway: Did the Idea of the Great Stone Tomb Travel by Sea?* Zenodo. https://doi.org/10.5281/zenodo.23685254

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
