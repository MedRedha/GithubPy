import os, sys, unittest, time, re, requests
from bs4 import BeautifulSoup
import traceback

import json
import hashlib
import urllib.error
from urllib.request import Request, urlopen, build_opener, install_opener, HTTPBasicAuthHandler, HTTPPasswordMgrWithDefaultRealm
from lxml import etree
import csv
import time
import logging
from datetime import date, timedelta
import subprocess
from requests import session

import pprint as pp
import argparse
import constants

USER = constants.GITHUB_ID
PASSWORD = constants.GITHUB_PASS
GITHUB_SESSION_URL = 'https://github.com/session'
headers = {'Authorization': 'token %s' % constants.GITHUB_API_TOKEN}

def get_bio(s, profile_url):
    line = ''
    try:
        html_source = s.get(profile_url).text
        parsed_html = BeautifulSoup(html_source, 'html.parser')

        username_val = profile_url.split('/')[-1]
        print('username:', username_val)
        line = line + username_val + ', '

        print('profile_url:', profile_url)
        line = line + profile_url + ', '

        fullname = parsed_html.find("span", class_="vcard-fullname")
        if fullname is not None:
            fullname_val = fullname.find(text=True, recursive=False)
            print('fullname:', fullname_val)
            if fullname_val is not None:
                line = line + fullname_val
        line = line + ', '

        email_li = parsed_html.find("li", {'itemprop':"email"}, class_="vcard-detail")
        if email_li is not None:
            email = email_li.find("a", class_="u-email")
            if email is not None:
                email_val = email.find(text=True, recursive=False)
                print('email: ', email_val)
                if email_val is not None:
                    line = line + email_val
        line = line + ', '

        org_li = parsed_html.find("li", {'itemprop':"worksFor"}, class_="vcard-detail")
        if org_li is not None:
            org = org_li.find("span", class_="p-org")
            if org is not None:
                org_val = org.find(text=True, recursive=True)
                print('organisation:', org_val)
                if org_val is not None:
                    line = line + org_val

        line = line + '\n'
        print()
    except Exception:
        traceback.print_exc()
    return line

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo')
    args = parser.parse_args()
    url = args.repo
    url = url.replace('https://github.com/', 'https://api.github.com/repos/')
    url = url + '/contributors?per_page=1000'
    r = requests.get(url, headers=headers)
    repo_items = json.loads(r.text or r.content)

    with open(args.repo.split('/')[3] + '_' + args.repo.split('/')[4] + '_contributors.csv','wb') as file:
        file.write(bytes('Username, RepoUrl, Fullname, EmailAddress, Organisation\n', 'UTF-8'))
        with session() as s:
            req = s.get(GITHUB_SESSION_URL).text
            html = BeautifulSoup(req, 'html.parser')
            token = html.find("input", {"name": "authenticity_token"}).attrs['value']
            com_val = html.find("input", {"name": "commit"}).attrs['value']

            login_data = {
                'login': USER,
                'password': PASSWORD,
                'commit' : com_val,
                'authenticity_token' : token
            }

            s.post(GITHUB_SESSION_URL, data = login_data)

            for repo_item in repo_items:
                line = get_bio(s, repo_item['html_url'])
                file.write(bytes(line, 'UTF-8'))
                time.sleep(2)

if __name__ == '__main__':
    main()
