#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import requests
import re
import numpy as np
from bs4 import BeautifulSoup


# In[ ]:


root = "http://gyakorikerdesek.hu"
page = requests.get(root)
soup = BeautifulSoup(page.content, 'html.parser')
html = list(soup.children)[2]

menus = [] 
for menu in soup.find_all(class_='menu'):
    menus.append(menu.a.get("href"))
    
page = requests.get(root + menus[1])
allatok = BeautifulSoup(page.content, 'html.parser')


# In[ ]:


def get_valasz(page):
    valasz_hasznos = re.compile("A válasz (\d+)%-ban hasznosnak tűnik.")
    iro_hasznos = re.compile("A válaszíró (\d+)%-ban hasznos válaszokat ad.")
    valasz_page = page.find_all("td", class_="valaszok vtop")
    return_valasz = None
    if valasz_page:
        valaszok = []
        scoreok = []
        for val in valasz_page:
            val_text = val.get_text().strip("\n")
            if val_text:
                valasz_m = valasz_hasznos.findall(val_text)
                iro_m = iro_hasznos.findall(val_text)
                if valasz_m and iro_m:
                    avg = (int(valasz_m[0]) + int(iro_m[0])) / 2
                    valasz = valasz_hasznos.search(val_text)
                    valasz = val_text.split(valasz.group())
                    valaszok.append(valasz[0])
                    scoreok.append(avg)
        if valaszok and scoreok:
            return_valasz = valaszok[np.argmax(scoreok)]
    return return_valasz


# In[ ]:


corp = {}
for i,kerdes in enumerate(allatok.find_all(class_="kerdes_lista")[1].find_all("tr")):
    try:
        kerdes_url = kerdes.find("a").get("href")
        subpage = requests.get(root + kerdes_url)
        allatok_kerdes = BeautifulSoup(subpage.content, 'html.parser')
        hosszu_kerdes = allatok_kerdes.find(class_="kerdes").find_all("td")[2].get_text()
        rovid_kerdes = allatok_kerdes.find(class_="kerdes").find_all("td")[2].h1.get_text()
        kategoriak = []
        for kategoria in allatok_kerdes.find("select").find_all("option")[1:]:
            kategoriak.append(kategoria.get_text())
        valasz = get_valasz(allatok_kerdes)
        if valasz:
            corp[i] = {"rovid_kerdes": rovid_kerdes, "hosszu_kerdes": hosszu_kerdes, "kategoriak": kategoriak, "valasz": valasz}
        print(i)
    except Exception as e:
        print(e)
        continue


# In[ ]:


for k in range(1,1000):
    page = requests.get(root + "/allatok__oldal-"+str(k))
    allatok = BeautifulSoup(page.content, 'html.parser')
    kerdesek_raw = allatok.find_all(class_="kerdes_lista")
    if len(kerdesek_raw) == 1:
        kerdesek = kerdesek_raw[0].find_all("tr")
    elif len(kerdesek_raw) == 2:
        kerdesek = kerdesek_raw[1].find_all("tr")
    for kerdes in kerdesek:
        try:
            kerdes_url = kerdes.find("a").get("href")
            subpage = requests.get(root + kerdes_url)
            allatok_kerdes = BeautifulSoup(subpage.content, 'html.parser')
            hosszu_kerdes = allatok_kerdes.find(class_="kerdes").find_all("td")[2].get_text()
            rovid_kerdes = allatok_kerdes.find(class_="kerdes").find_all("td")[2].h1.get_text()
            kategoriak = []
            for kategoria in allatok_kerdes.find("select").find_all("option")[1:]:
                kategoriak.append(kategoria.get_text())
            valasz = get_valasz(allatok_kerdes)
            if valasz:
                corp[i] = {"rovid_kerdes": rovid_kerdes, "hosszu_kerdes": hosszu_kerdes, "kategoriak": kategoriak, "valasz": valasz}
            i += 1
            print(i)
        except Exception as e:
            print(e)
            continue
    print("page: " + str(k))


felhasznalo_kerdese = re.compile("(^\w+) nevű felhasználó kérdése:")
felhasznalo_valasza = re.compile("(^\w+) nevű felhasználó válasza:")
inds = []
for c in corp:
    hosszu_kerdes = corp[c]["hosszu_kerdes"].strip("\n").replace("(adsbygoogle = window.adsbygoogle || []).push({});","").split("\n")
    hosszu_kerdes = " ".join(hosszu_kerdes)
    valasz_unfiltered = corp[c]["valasz"]
    m = felhasznalo_valasza.search(valasz_unfiltered)
    if m:
        valasz_unfiltered = valasz_unfiltered.replace(m.group(), "")
    hosszu_valasz = valasz_unfiltered.strip("\n").replace("(adsbygoogle = window.adsbygoogle || []).push({});","").replace("\n", " ").strip()
    corp[c]["valasz"] = hosszu_valasz
    if "Keress kérdéseket hasonló témákban:" in hosszu_kerdes:
        kerdes = hosszu_kerdes.split("Keress kérdéseket hasonló témákban:")
        kerdes_text = kerdes[0].strip().replace("\n"," ")
        m = felhasznalo_kerdese.search(kerdes_text)
        if m:
            kerdes_text = kerdes_text.replace(m.group(), "")
        corp[c]["hosszu_kerdes"] = kerdes_text
        corp[c]["keywords"] = [i.strip() for i in kerdes[1].split(",")]
        kat = corp[c]["kategoriak"]
        kat_filt = [i.replace("» ", "") for i in kat]
        corp[c]["kategoriak"] = kat_filt
        inds.append(c)
        
filtered_corp = [corp[i] for i in corp if i in inds]
unique_corp = []
rovid_kerdesek = []
for i in filtered_corp:
    if i["rovid_kerdes"] not in rovid_kerdesek:
        unique_corp.append(i)
        rovid_kerdesek.append(i["rovid_kerdes"])


import json
with open("gyakori_corpus_allatok", "w+") as f:
    s = json.dumps(unique_corp)
    f.write(s)




