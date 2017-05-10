# anonymization

```
python3 names.py dummy-sample.tab
```

This script anonymizes the comment fields ('omschrijving') in Dutch bank transactions, by removing all person names.
It takes as input file a tab-separated text file with the following columns:
```
MINISTERIE, BOEKJAAR, NAAM LEVERANCIER, OMSCHRIJVING, BEDRAG, VALUTA, GB_DATUM, EUR_BEDRAG
```

It uses a number of external resources:
 * a list of 10,000 Dutch surnames and prefixes (‘de’, ‘ter’, ‘van’ etc.). Downloaded from [naamkunde.net](http://www.naamkunde.net/?page_id=294)
 * a list of 9,755 Dutch first names. Downloaded from [naamkunde.net](http://www.naamkunde.net/?page_id=293)
 * a list of 381,292 Dutch words. The file DFW.CD from the [CELEX database](https://catalog.ldc.upenn.edu/ldc96l14)
 * a list of abbreviations, extracted from the transaction data itself: all words of 2–4 words that consist of only capital letters and are not a prefix or salutation (‘DHR’, ‘MEVR’, etc.), and occur at least 50 and that times in the data.

The generated output is a tab-separated file with the following 3 columns:

```
item id of original row, anonymized omschrijving (names replaced by ***), list of found names
```

Evaluation showed that the coverage (recall) of the method is good, with around 95\% of the names removed. However, the price for achieving this high recall is that precision was reduced to around 50%. This implies that if 10 names are removed, 10 non-names are also removed from the data.

# License

See the [LICENSE](LICENSE.md) file for license rights and limitations (GNU-GPL v3.0).