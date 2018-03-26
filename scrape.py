#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import urllib
import requests
import re
import sys
from bs4 import BeautifulSoup as Soup
from tqdm import tqdm
from furl import furl

JOBS_FILE_PATH = 'jobs.csv'
BASE_URL = 'https://www.indeed.com/jobs'
VIEW_JOB_URL = "https://www.indeed.com/viewjob"
city = 'New York, NY'
    
def scrape_jobs_using_soup(url, df):
    """
        This function scrapes the jobs from Indeed using BeautifulSoup
    """
    target = Soup(urllib.request.urlopen(url), "lxml") 
    target_elements = target.findAll('div', attrs={'class': re.compile('row result')})

    for elem in target_elements:
        try:
            # Get the job key, company name, title and location 
            job_key = elem.attrs['data-jk']
            company_name = elem.find('span', {'class': re.compile('company')}).text.strip()
            job_title = elem.find('a', {'class': 'turnstileLink'}).attrs['title']
            job_location = elem.find('span', {'class': 'location'}).text.strip()
        except (KeyError, AttributeError):
            pass

        try:
            if (df['job_key'] == job_key).any():
                # Check if job key already exists in the csv file
                # to avoid duplicate entries 
                continue
        except KeyError:
            pass

        f = furl(VIEW_JOB_URL)
        f.args['jk'] = job_key
        job_link = f.url

        targetDesc = Soup(urllib.request.urlopen(job_link), "lxml")
        job_summary = targetDesc.find('span', {'id': 'job_summary'}).text.strip()
        
        entry = {
            'company_name': company_name,
            'job_title': job_title,
            'job_location': job_location,
            'job_key': job_key,
            'job_link': job_link,
            'job_summary':job_summary
        }
        
        return entry

def get_jobs_with_salary(job_title, salary_label, df):
    """
        This function fetches jobs with the specified job title and salary
    """
    f = furl(BASE_URL)
    f.args['q'] = '{} {}'.format(job_title, salary_label)
    f.args['l'] = city
    f.args['radius'] = 100
    f.args['sort'] = 'date'
    
    for page in tqdm(range(1,101)): 
        # Indeed only allows job ads in the first 100 pages (1101 jobs)
        # to be fetched
        page = (page-1) * 10  
        f.args['start'] = page
        url = f.url

        entry = scrape_jobs_using_soup(url, df)
        try:
            entry['salary_label'] = salary_label
        except TypeError:
            pass

        df = df.append(entry, ignore_index = True)
    
    return df
                   
def get_jobs_with_title(job_title): 
    """
        This function fetches job ads with the specified title from Indeed
    """
    try:
        # If there is a csv file with job descriptions populated already,
        # read the file using Pandas
        df = pd.read_csv(JOBS_FILE_PATH)
    except OSError: 
        # If not, intialize a new dataframe to store the jobs
        df = pd.DataFrame()
        
    salary_labels = np.arange(55000, 125001, 10000)
    salary_labels = ['$' + str(label) for label in salary_labels][::-1]
    
    for label in salary_labels:
        print('For {} jobs with salary {}'.format(job_title, label))
        df = get_jobs_with_salary(job_title, label, df)
        df.to_csv('jobs.csv', index=False)
        
    return df 


job_title = sys.argv[1]
get_jobs_with_title(job_title) 