import sys
import re
from bs4 import BeautifulSoup

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QUrl
from PyQt5.QtWebEngineWidgets import QWebEnginePage

BASE_URL = 'https://www.crunchbase.com'

companies = []
pages = []


class Page(QWebEnginePage):
    def __init__(self, url):
        self.app = QApplication(sys.argv)
        QWebEnginePage.__init__(self)
        self.html = ''
        self.loadFinished.connect(self._on_load_finished)
        self.load(QUrl(url))
        self.app.exec_()

    def _on_load_finished(self):
        self.html = self.toHtml(self.Callable)

    def Callable(self, html_str):
        self.html = html_str
        self.app.quit()


def get_page(route):
    if not route:
        return None

    try:
        url = f'{BASE_URL}{route}'
        pages.append(Page(url))
        soup = BeautifulSoup(pages[-1].html, 'lxml')
        pages[-1].deleteLater()
    except:
        return None
    else:
        return soup


def format_name(name):
    return name.lower().replace('\n', '').strip().replace('.', '-').replace(' ', '-').replace(':', '-')


def extract_link(element):
    return re.search(r'(https?:\/\/)(www\.)?([a-zA-Z0-9]+(-?[a-zA-Z0-9])*\.)+([a-z]{2,})(\/\S*)?', element).group(0)


def print_green(s):
    print(f'\033[92m{s}\033[0m')


def scrape_data(company_name):
    name = format_name(company_name)

    print_green(f'Checking {company_name} alias {name}')

    # load the page in "soup" variable
    soup = get_page(f'/organization/{name}')
    if not soup:
        print_green(
            f'{company_name}, alias {name} gave an error while loading')
        with open('../data/error.csv', 'a') as file:
            file.write('\n' + company_name)
        return

    # extract website and social media links
    html_links = soup.find_all(
        'a', class_="cb-link component--field-formatter field-type-link layout-row layout-align-start-end ng-star-inserted")
    links = []
    for html in html_links:
        link = extract_link(str(html))
        links.append(link)

    # the name wasn't correct if there are no social links on the page
    if len(links) == 0:
        print_green(f'{company_name}, alias {name} could not be found')
        with open('../data/not_found.csv', 'a') as file:
            file.write('\n' + company_name)
        return

    website = links[0]
    company_twitter = None
    if 'twitter' in links[-1]:
        company_twitter = links[-1].split('/')[-1]

    # extract the personans in the team
    html_persons = soup.find_all(
        'div', class_='flex cb-padding-medium-left cb-break-word cb-hyphen')

    ceo = None
    cto = None
    founders = []

    for html_person in html_persons:
        name_link = html_person.find('a')['href']
        position = html_person.find('span')['title']

        if re.search(r'(\s|^)((ceo)|(Chief Executive Officer))(\s|$)', position, re.I):
            ceo = name_link

        if re.search(r'(\s|^)((cto)|(Chief Technical Officer)|(Chief technology officer))(\s|$)', position, re.I):
            cto = name_link

        if re.search(r'founder', position, re.I):
            founders.append(name_link)

    # just to be safe
    if not ceo and not cto:
        if len(founders) >= 2:
            (ceo, cto) = founders
        elif len(founders) == 1:
            ceo = founders[0]

    ceo_twitter = None
    cto_twitter = None

    for person in (ceo, cto):
        if not person:
            continue

        soup = get_page(person)
        if not soup:
            print(f'Could not find {person}')
            continue

        card = soup.find(
            'mat-card', class_='component--section-layout mat-card')

        person_twitter = re.search(r'twitter.com/([^"]*)"', str(card))
        if not person_twitter:
            print_green(f"{person} doesn't have a twitter account")
            continue

        if person is ceo:
            ceo_twitter = person_twitter.group(1)
        else:
            cto_twitter = person_twitter.group(1)

    with open('../data/found.csv', 'a') as file:
        file.write(
            f'\n"{company_name}","{website}","{company_twitter}","{ceo_twitter}","{cto_twitter}"')


with open('../data/list_of_company_names_raw.csv', 'r') as fp:
    line = fp.readline()

    while line:
        companies.append(line.replace('\n', ''))

        line = fp.readline()

companies = list(dict.fromkeys(companies))

for company in companies:
    scrape_data(company)
