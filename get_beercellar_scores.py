# coding: utf
import pandas as pd
from functions import *
import numpy as np
from time import sleep, time
from datetime import datetime
import sys

url = 'https://belmont.craftbeercellar.com/beer-international-116/'

# label on first and last links
first_loc = "AUSTRALIA"
last_loc = "WYOMING"

# pull from old file?
check_old_scores = False
# if pulling from old file, should we keep entries that had no score found? (False increases runtime by checking again for every old entry that didn't have a score for any reason)
keep_old_noscores = True
old_filename = "beercellar_scores_2020-05-23.csv"

# file to save to
filename = "beercellar_scores_"+str(datetime.today()).split()[0]+".csv"

style_dict = {"Ale": "Ale", "IPA": "IPA", "Gose":"Sour", "Lambic":"Sour", "Lager":"Lager", "Berliner Weisse":"Sour","Stout":"Stout"}
# priority for resolving ambiguities
priority_list = ["IPA", "Sour", "Stout", "Lager", "Ale"]

start_time = time()

version = sys.version_info.major

# get old file if necessary
if check_old_scores:
    old_data = pd.read_csv(old_filename)
    if not keep_old_noscores:
        old_data = old_data[np.isfinite(old_data.score)]
    overlap = 0

browser = mechanize.Browser()
browser.set_handle_robots(False)
browser.addheaders = [("User-agent", 'Mozilla/5.0 (Windows; U; Windows NT 5.1;en-US; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8 GTB7.1 (.NET CLR 3.5.30729)')]

page = browser.open(url)
links = browser.links()

# pull links to location subpages
loc_links = get_loclink_inds(links, first_loc, last_loc)

beer_list = []
name_list = []
brewer_list = []

# go to each page and pull beer info
# compile list of beers, get brewery too so that search hopefully returns just one thing
print("\n...COLLECTING LIST OF BEERS...\n")
for loc_link in loc_links:
    print(loc_link[41:])
    page = browser.open(loc_link)
    lines = [str(l) for l in page.readlines()]
    links = browser.links()
    page.close()
    browser.clear_history()

    home_link_ind = 0
    for i in range(len(links)):
        if "Home" in links[i].text:
            home_link_ind = i

    page_list = [loc_link]
    # if there are multiple pages, find and iterate through
    k = 3
    page2_link = links[home_link_ind+k]
    if page2_link.text=='2': # then we have multiple pages
        found = False
        while not found:
            link = links[home_link_ind+k]
            if link.text=='>>':
                found = True
            else:
                page_list.append(link.base_url + link.url)
                k = k+1

    page_ind = 0
    for url in page_list:
        page = browser.open(url)
        lines = [str(l) for l in page.readlines()]
        links = browser.links()
        start_ind, end_ind = get_beerlink_inds(links)
        for j in range(start_ind, end_ind, 5):
            link = links[j]
            beer_name = str(link.text.replace(u'\xe1','a').replace(u'\xf3','o').replace(u'\xe9','e').split(" - ")[0])
            #print(beer_name)
            name_list.append(beer_name)
            if version==2:
                url = str(link.attrs[0][1].decode('utf-8').replace(u'\xe1','a').replace(u'\xf3','').replace(u'\xe9',''))
            else:
                url = link.attrs[0][1]
            line = findline(lines, url)
            ind = line.find(url)
            subline = line[ind:ind+1000].split("Quick View")[1].split("h6")[1]
            brewer = str(subline[1:-2].lower())
            brewer = brewer.strip()
            brewer = " ".join([s.capitalize() for s in brewer.split()])
            brewer_list.append(brewer)
            beer_list.append(str(brewer + " " + beer_name).strip())
        page_ind = page_ind + 1
    sleep(0.02) # so the site doesn't block us

# remove duplicates
interim_df = pd.DataFrame(data={"data":beer_list}).drop_duplicates()
inds = interim_df.drop_duplicates().index
beer_list = [beer_list[i] for i in inds]
brewer_list = [brewer_list[i] for i in inds]
name_list = [name_list[i] for i in inds]

intermediate_time = time()
print("\nGenerating list of beers took " + str(np.round((intermediate_time-start_time)/60.0,1)) + " minutes.")
time_check = intermediate_time

# pull beer info
print("\n...PULLING BEERADVOCATE SCORES...\n")
ratings_list = []
score_list = []
abv_list = []
note_list = []
link_list = []
style_list = []
query_count = 0
for i in range(len(beer_list)):
    if i%50==0:
        t = time()
        print("..."+str(i)+"/"+str(len(beer_list))+"...("+str(np.round((t-time_check)/60.0,1))+" min)")
        time_check = t
    # pause for longer every so often to avoid the throttle...hopefully
    if query_count % 50 == 0:
        sleep(1.0)
    brewer_name = beer_list[i]
    #print(brewer_name)
    name = name_list[i]
    if check_old_scores:
        if name in list(old_data.name):
            old_entry = dict(old_data[old_data.name==name].iloc[0])
            ratings_list.append(old_entry["rating"])
            score_list.append(old_entry["score"])
            abv_list.append(old_entry["abv"])
            note_list.append(old_entry["note"])
            link_list.append(old_entry["link"])
            style_list.append(old_entry["style"])
            overlap = overlap + 1
            continue
    query_count = query_count + 1
    beer_info = Beer(brewer_name)
    if np.isnan(beer_info.score) and len(name)>2: # couldn't find it, try with just name and no brewer
        beer_info = Beer(name)
        query_count = query_count + 1
    score_list.append(beer_info.score)
    ratings_list.append(beer_info.rating)
    abv_list.append(beer_info.abv)
    note_list.append(beer_info.note)
    link_list.append(beer_info.link)
    style_list.append(beer_info.style)
    sleep(0.1)

# compile to dataframe and sort by score
df = pd.DataFrame(data={'name':name_list, 'style':style_list, 'score':score_list, 'rating':ratings_list, 'brewer':brewer_list, 'abv':abv_list, 'link':link_list, 'note':note_list})
df = df.sort_values(by="score",ascending=False).reset_index(drop=True)
# add generalized categories
df["category"] = [categorize_style(style, style_dict, priority_list) for style in df['style']]
# save results
df.to_csv(filename, index=False)
end_time = time()

nopage_count = str(len(df[df.note=="couldn't find BeerAdvocate page"]))
bestguess_count = str(len(df[df.note=="multiple results, guessed best match"]))
noscoreyet_count = str(len(df[df.note=="No score yet"]))
total_num = str(len(df))

# print some information to screen
output_str = "\nDone! Getting scores took "+str(np.round((end_time-intermediate_time)/60.0, 1)) + " minutes, for a total of " + str(np.round((end_time-start_time)/60.0, 1)) + " minutes.\n\nResults written to "+filename+".\n\nSome more info:\n    There was no BeerAdvocate page found for " + nopage_count + "/" + total_num + " beers.\n    For " + bestguess_count + "/" + total_num + " beers, multiple pages were found and I took my best guess.\n    For " + noscoreyet_count + "/" + total_num + " beers, there weren't enough reviews yet for a score to be reported.\n"

if check_old_scores:
    output_str = output_str + "    Finally, I saved time in " + str(overlap) + "/" + total_num + " cases by copying the score from the old spreadsheet. Woohoo!"

print(output_str)
