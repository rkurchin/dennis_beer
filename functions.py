# coding: utf8

# parts of the Beer class in this file are adapted from https://github.com/jfach/beer-for-python
import numpy as np
import mechanize
from fuzzywuzzy import fuzz
import sys

version = sys.version_info.major

search = mechanize.Browser()
search.set_handle_robots(False)
search.addheaders = [("User-agent", 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8 GTB7.1 (.NET CLR 3.5.30729)')]

# find the line containing a given url
def findline(lines, url):
    for line in lines:
        if version==2:
            line_check = line.decode('utf8').replace(u'\xe1','a').replace(u'\xf3','').replace(u'\xe9','')
        else:
            line_check = line
        if url in line_check:
            return line_check

# find (first) indices of first and last links to the different location pages (every link shows up multiple times)
def get_loclink_inds(link_list, first_loc, last_loc):
    first_link_ind = -1
    last_link_ind = -1
    skip_link_ind = -1
    for i in range(len(link_list)):
        if link_list[i].text==first_loc and first_link_ind==-1:
            first_link_ind = i
        elif link_list[i].text==last_loc and last_link_ind==-1:
            last_link_ind = i
        elif link_list[i].text=="BEER: US" and skip_link_ind==-1:
            skip_link_ind = i

    return [link_list[i].url for i in range(first_link_ind, last_link_ind+1) if not i==skip_link_ind]

# on a BeerAdvocate search results page, get links to beer pages
def get_beerlink_inds(link_list):
    start_ind = 0
    end_ind = 0
    for i in range(len(link_list)):
        l = link_list[i]
        if start_ind==0 and len(l.attrs)>1:
            if l.attrs[1][1]=='product-link productnameTitle':
                start_ind = i
        elif (l.text=="<<" or l.text=='Get Beer Mail!' or l.text=='1') and end_ind==0:
            end_ind = i
    return (start_ind, end_ind)

def generate_link(beer):
    beer_name = beer.replace(" ", "+")
    query = "http://www.beeradvocate.com/search/?q={}&qt=beer".format(beer_name)
    return query

def beer_profile(beer):
    # ampersands don't play nice with URLs...
    beer_search = beer.replace("&","").replace("  ", " ")
    beer_page = generate_link(beer_search)
    response = search.open(beer_page)
    raw = response.read()
    response.close()
    search.clear_history()
    raw = str(raw)
    # check if it wasn't found
    ind = raw.find(beer_search)
    if ind==-1:
        return (-1, "none", "couldn't find BeerAdvocate page")
    subset = raw[ind+len(beer_search):ind+len(beer_search)+10]
    if "Search" in subset:
        if "Beers Found: 0" in raw:
            # no search results
            return (-1, "none", "couldn't find BeerAdvocate page")
        # multiple search results, find best match
        links = search.links()
        for i in range(len(links)):
            if "Search Places" in links[i].text:
                first_ind = i + 2
        link_inds = [first_ind]
        done = False
        ind = first_ind + 4
        while not done:
            if "/beer/profile/" in links[ind].url:
                link_inds.append(ind)
                ind = ind + 4
            else:
                done = True
        names = [links[i].text for i in link_inds]
        best_match_ind = np.argmax([fuzz.ratio(beer, name) for name in names])
        best_match_link = links[link_inds[best_match_ind]]
        link = "https://www.beeradvocate.com" + best_match_link.url
        response = search.follow_link(best_match_link)
        raw = response.read()
        note = "multiple results, guessed best match"
    else:
        note = ""
        link = beer_page
    return (str(raw), link, note)

# bin specific style to more general categories defined by options_dict
# there might be some prioritizations (e.g. IPA's will probably also have "Ale" in style name)
def categorize_style(style, style_dict, priority_list):
    match_dict = {key:False for key in style_dict.keys()}
    for key in style_dict.keys():
        if key in style:
            match_dict[key] = True
    if not any(match_dict.values()):
        return "Other"
    else:
        options = [style_dict[k] for k in match_dict.keys() if match_dict[k]]
        if len(options)==1:
            return options[0]
        else: # need to prioritize, find first one in priority list that is in options
            for option in priority_list:
                if option in options:
                    return option

class Beer:
    def __init__(self, name):
        self.name = name
        raw, link, note = beer_profile(name)
        self.note = note
        self.link = link
        if type(raw)==int or type(raw)==float:
            self.score=np.nan
            self.abv="?"
            self.style="?"
            self.rating=np.nan
        else:
            self.score = self.get_score(raw)
            self.abv = self.get_abv(raw)
            self.style = self.get_style(raw)
            self.rating = self.get_rating(raw)

    def get_abv(self, raw):
        abv_pointer = raw.find('<b>ABV:</b>')
        abv_area = raw[abv_pointer:abv_pointer+120]
        end_ind = abv_area.find("%")
        abv_area = abv_area[end_ind-10:end_ind]
        abv = abv_area.split(">")[-1]
        if abv=='':
            return "?"
        else:
            return float(abv)

    def get_score(self, raw):
        score_pointer = raw.find("Score: ")
        if score_pointer==-1:
            return np.nan
        score_area = raw[score_pointer+7:score_pointer+10]
        score = score_area.split(" ")[0]
        if score=='n/a':
            self.note = "No score yet"
            return np.nan
        else:
            return int(score)

    def get_style(self, raw):
        style_pointer = raw.find("Style:")
        style_area = raw[style_pointer:style_pointer+200]
        style_area = style_area.split("<b>")[1]
        style = style_area.split("</b>")[0]
        return style

    def get_rating(self, raw):
        rating_pointer = raw.find("Avg:")
        rating_area = raw[rating_pointer:rating_pointer+200]
        rating_area = rating_area.split('for this beer.">')[1]
        return float(rating_area.split("</span>")[0])
