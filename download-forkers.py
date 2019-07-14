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

import argparse
import constants

USER = constants.GITHUB_ID
PASSWORD = constants.GITHUB_PASS
GITHUB_SESSION_URL = 'https://github.com/session'

def get_bio(s, fork_url):
    profile_url = '/'.join(fork_url.split('/')[0:-1])
    html_source = s.get(profile_url).text
    line = ''
    try:
        parsed_html = BeautifulSoup(html_source, 'html.parser')

        username_val = profile_url.split('/')[-1]
        print('username:', username_val)
        line = line + username_val + ', '

        print('repourl:', fork_url)
        line = line + fork_url + ', '

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

def get_forkers_url(root_url):
    mem_url = root_url + "/network/members"
    fork_urls = []
    try:
        req = Request(mem_url , headers={'User-Agent': 'Mozilla/5.0'})
        html_source = urlopen(req).read()
        parsed_html = BeautifulSoup(html_source, 'html.parser')
        forks = parsed_html.find_all("div", class_="repo")
        for fork in forks:
            links = fork.find_all("a", class_="")
            for l in links:
                if len(l['href'].split('/')) > 2:
                    fork_urls.append("https://github.com" + l['href'])
    except urllib.error.URLError as e:
        print("Seems URL changed for: " + mem_url)
        print(e)
    except Exception as e:
        print("Unknown Error: " + mem_url)
        print(e)
    return fork_urls

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo')
    args = parser.parse_args()
    fork_urls = get_forkers_url(args.repo)
    with open(args.repo.split('/')[3] + '_' + args.repo.split('/')[4] + '_forkers.csv','wb') as file:
        file.write(bytes('Username, RepoUrl, Fullname, EmailAddress, Organisation\n', 'UTF-8'))
        with session() as s:
            req = s.get(GITHUB_SESSION_URL).text
            html = BeautifulSoup(req, 'html.parser')
            token = html.find("input", {"name": "authenticity_token"}).attrs['value']
            com_val = html.find("input", {"name": "commit"}).attrs['value']

            login_data = {'login': USER,
                        'password': PASSWORD,
                        'commit' : com_val,
                        'authenticity_token' : token}

            s.post(GITHUB_SESSION_URL, data = login_data)

            for fork_url in fork_urls:
                line = get_bio(s, fork_url)
                file.write(bytes(line, 'UTF-8'))

if __name__ == '__main__':
  main()