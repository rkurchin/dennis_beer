# dennis_beer

Some Python code to get the list of beers currently available at [Belmont Beer Cellar](https://belmont.craftbeercellar.com) and cross-reference to their scores at [BeerAdvocate](https://www.beeradvocate.com). Built for my uncle Dennis, who has been valiantly trying to get me to like beer since grad school. Some portions of the code are adapted from the (now deprecated) [pybeer](https://github.com/jfach/beer-for-python).

Main script is `get_beercellar_scores.py`. The code herein is not beautiful, but it gets the job done!

## Features
* Compiles list of beers and brewers from Belmont Beer Cellar, then gets (if available) style, alcohol content and  scores from BeerAdvocate, sorts in descending order of score, and saves to a CSV file
* If search on BeerAdvocate yields multiple results, uses fuzzy string matching (via the Levenshtein distance as implemented in the `fuzzywuzzy` and `python-Levenshtein` packages) to choose the best match (if this happens, a remark will be put in the "note" column of output and you can check the included BeerAdvocate link to make sure it's the right brew)
* Since running the script when ~800 beers are available takes ~40 minutes, optionally check previous output file (see `check_old_scores` flag) and only query for beers that don't have scores listed there (this reduces runtime to ~10-15 minutes for a relatively recent output file).
* Customizable categorization into categories of style (e.g. English and American IPA both categorized as IPA)

## Requirements
Easiest is to use conda and duplicate my environment (in the `environment.yml` file). If that's not your style, here are the packages you'll need (all available via `pip`, should be workable in Python 2 or 3):
* numpy
* pandas
* mechanize
* fuzzywuzzy (and, optionally, python-Levenshtein to speed it up)

## I don't live near Belmont, MA!
If you want to adapt it for your own local shop's listing, you'll need to work out how to do the web parsing yourself and then modify the beginning of the main script (`get_beercellar_scores.py`) and first big loop accordingly, but the BeerAdvocate part should work regardless, as long as you format the DataFrame correctly.

If you do so, please fork this and credit me appropriately, and also let me know because it would be cool to see!
