
'''
Module for scraping data from the hiking website AllTrails.
'''


import requests
from bs4 import BeautifulSoup
import re
from selenium import webdriver
import time
import numpy as np

user_agent = {'User-agent': 'Mozilla/5.0'}

def get_links(url,n_trails=100):
    '''
    Input: a link to an AllTrails overview page.  For example, the page listing all hikes in 
    California.
    
    Returns: sub-links to every trail in the list up to n_trails.
    '''
    
    # initiate chromedriver and open the url
    chromedriver = '/Applications/chromedriver'
    driver = webdriver.Chrome(chromedriver)
    driver.get(url)
    time.sleep(3)
    
    # page is dynamic, need to keep clicking "more trails" button until desired number reached
    # or until it reaches the bottom
    button = '//button[text()="Show more trails"]'
    
    for i in range(n_trails//10-1):
        try:
            driver.find_element_by_xpath(button).click()
            time.sleep(1)
        except:
            break
    
    # convert to soup after enough trails have been loaded
    soup = BeautifulSoup(driver.page_source,'html.parser')
    
    # add all trail sub-links to list and close the chromedriver
    links = []
    
    hikes = soup.find_all('a',class_=re.compile('xlate-none'))
    for hike in hikes:
        links.append(hike.get('href'))
        
    driver.quit()
    
    final = []
    for link in links:
        try: 
            if link.startswith('/trail'):
                final.append(link)
        except:
            pass
        
    return final


def get_trail_info(url):
    '''
    Input: link to an AllTrails trail url.
    Returns: all information about the trail contained on the webpage.
    '''
    
    # load page to parsable soup
    response = requests.get(url,headers=user_agent)
    soup = BeautifulSoup(response.content,features = 'lxml')
    
    # add each item as a dictionary element
    d = {}
    
    d['trail_name'] = soup.find('h1').text
    
    try:
        d['difficulty'] = soup.find('span',class_=re.compile('styles-module__diff')).text
    except:
        d['difficulty'] = np.nan
        
    d['star_rating'] = float(soup.find('span',class_=re.compile('MuiRating')).get('aria-label').split()[0])
    
    count = soup.find('span',class_=re.compile('styles-module__count')).text
    d['rating_count'] = re.sub('[^0-9]','',count)
    
    d['summary'] = soup.find('p',id='auto-overview').text
    
    detail_data = soup.find_all('span',class_=re.compile('detail-data'))
    d['length_mi'] = float(detail_data[0].text.strip().split()[0].replace(',',''))
    
    try:
        d['elevation_change'] = int(''.join(detail_data[1].text.strip().split()[0].split(',')))
    except:
        d['elevation_change'] = np.nan
        
    try:
        d['route_type'] = detail_data[2].text
    except:
        d['route_type'] = np.nan
    
    try:
        tags = soup.find_all('span',class_='tag')
        tag_list = []
        for tag in tags:
            tag_list.append(tag.text.strip())
        d['tags'] = tag_list
    except:
        d['tags'] = np.nan
    
    location_path = soup.find_all('li',itemprop='itemListElement')
    loc_list = []
    for loc in location_path:
        loc_list.append(loc.text.strip().split('\n')[-1])
    d['location_path'] = loc_list
    
    try:
        d['full_description'] = soup.find('p',id='text-container-description').text
    except:
        d['full_description'] = np.nan
    
    # save the headline image with a name matching the exact trail name
    try:
        image = soup.find(itemprop='image').get('content')
        with open(f'../images/{d["trail_name"]}.jpg','wb') as f:
            f.write(requests.get(image,headers=user_agent).content)
    except:
        pass
        
    try:
        reviews = soup.find_all('p',itemprop='reviewBody')
        review_list = []
        for review in reviews:
            review_list.append(review.text)
    except:
        review_list = np.nan
        
    d['reviews'] = review_list
    d['link'] = url
        
    return d