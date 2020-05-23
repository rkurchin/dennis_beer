# parts of this are adapted from https://github.com/jfach/beer-for-python
import numpy as np
import mechanize
from fuzzywuzzy import fuzz

search = mechanize.Browser()
search.set_handle_robots(False)
search.addheaders = [("User-agent", 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8 GTB7.1 (.NET CLR 3.5.30729)')]

def findline(lines, url):
    for line in lines:
        if url in line:
            return line

def get_inds(link_list):
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

def num_search_results(raw):
    ind = raw.find("Beers Found:")
    num =  raw[ind+11:ind+20].split()[1]
    return int("".join(num.split(",")))
    
def generate_link(beer):
    beer_name = beer.replace(" ", "+")
    query = "http://www.beeradvocate.com/search/?q={}&qt=beer".format(beer_name)
    return query

def beer_profile(beer):
    beer_page = generate_link(beer)
    response = search.open(beer_page)
    raw = response.read()
    response.close()
    search.clear_history()
    raw = str(raw)
    # check if it wasn't found
    ind = raw.find(beer)
    if ind==-1:
        return (-1, "none", "couldn't find BeerAdvocate page")
    subset = raw[ind+len(beer):ind+len(beer)+10]
    if "Search" in subset:
        #return num_search_results(raw)
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

class Beer:
    def __init__(self, name):
        self.name = name
        raw, link, note = beer_profile(name)
        self.note = note
        self.link = link
        if type(raw)==int or type(raw)==float:
            self.score=np.nan
            self.brewer="?"
            self.abv="?"
        else:
            self.score = self.get_score(raw)
            #self.brewer = self.get_brewer(raw)
            #self.style = self.get_style(self.name)
            self.abv = self.get_abv(raw)
            
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

    # haven't fixed this one yet
    def get_style(self, raw):
        style_pointer = raw.find('Style | ABV')
        style_area = raw[style_pointer:style_pointer+100]
        style_start = style_area.find("><b>")
        style_end = style_area.find("</b></a>")
        style = style_area[style_start+4:style_end]
        return style

    def get_brewer(self, raw):
        brewer_pointer = raw.find("<title>")
        brewer_end_pointer = raw.find("</title>")
        brewer_area = raw[brewer_pointer+7:brewer_end_pointer]
        brewer = brewer_area.split(" | ")[1]
        return brewer

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
