import time
from bs4 import BeautifulSoup
import traceback
import urllib.error
from urllib.request import Request, urlopen
from requests import session
import argparse
import constants
import random

USER = constants.GITHUB_ID
PASSWORD = constants.GITHUB_PASS
GITHUB_SESSION_URL = 'https://github.com/session'

def get_bio(s, profile_url):
    html_source = s.get(profile_url).text
    line = ''
    try:
        parsed_html = BeautifulSoup(html_source, 'html.parser')

        username_val = profile_url.split('/')[-1]
        print('username:', username_val)
        line = line + username_val + ', '

        print('repourl:', profile_url)
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

def get_stargazers_url(root_url, max_page):
    mem_url = root_url + "/stargazers"
    profile_urls = []
    ctr = 0
    while mem_url and ctr < max_page:
        ctr += 1
        try:
            print("Vising:", mem_url)
            req = Request(mem_url , headers={'User-Agent': 'Mozilla/5.0'})
            html_source = urlopen(req).read()
            parsed_html = BeautifulSoup(html_source, 'html.parser')
            stars = parsed_html.find_all("h3", class_="follow-list-name")
            for star in stars:
                links = star.find_all("a", class_="")
                for l in links:
                    if len(l['href'].split('/')) == 2:
                        profile_urls.append("https://github.com" + l['href'])

            footer_links = parsed_html.find_all("a", class_="btn btn-outline BtnGroup-item")
            for footer_link in footer_links:
                button_text = footer_link.find(text=True, recursive=False)
                if button_text=="Next":
                    mem_url= footer_link['href']
                else:
                    mem_url=None
        except urllib.error.URLError as e:
            print("Seems URL changed for: " + mem_url)
            print(e)
        except Exception as e:
            print("Unknown Error: " + mem_url)
            print(e)
    return profile_urls

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo')
    parser.add_argument('--max_page', default=5)
    args = parser.parse_args()
    profile_urls = get_stargazers_url(args.repo, args.max_page)
    # pp.pprint(profile_urls)
    with open(args.repo.split('/')[3] + '_' + args.repo.split('/')[4] + '_stargazers.csv','wb') as file:
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

            for profile_url in profile_urls:
                line = get_bio(s, profile_url)
                file.write(bytes(line, 'UTF-8'))
                time.sleep(random.randint(4, 8))

if __name__ == '__main__':
    main()
