import json
import os.path
import re
from collections import defaultdict

import requests
from bs4 import BeautifulSoup


def save_json(data, filename):
    print(f"saving file: {filename}")
    with open(filename, 'w') as f:
        json.dump(data, f)


def read_json(filename):
    print(f"reading file: {filename}")
    with open(filename, 'r') as f:
        data = json.load(f)
    return data


def clean_str(input_str):
    input_str = str(input_str)
    pattern = re.compile('[\W_]+')
    return pattern.sub('', input_str).lower()


def scrape_voting_location_by_county(counties):
    output = defaultdict(list)
    for county_id, county_name in counties.items():
        headers = {
            'authority': 'elections.sos.ga.gov',
            'cache-control': 'max-age=0',
            'upgrade-insecure-requests': '1',
            'origin': 'https://elections.sos.ga.gov',
            'content-type': 'application/x-www-form-urlencoded',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4283.0 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'sec-fetch-dest': 'document',
            'referer': 'https://elections.sos.ga.gov/Elections/advancedVotingInfo.do',
            'accept-language': 'en-US,en;q=0.9',
            'cookie': 'JSESSIONID=sTO7dIy-Cdl02MYw9fFR9EHsAxqnu5jbskfqEZ3t.ports-02; __cfduid=da5ee1548d3ba6d15d5ad0cba675f83fd1602533696',
            'dnt': '1',
            'sec-gpc': '1',
        }

        data = {
            'townId': county_id,
            'SubmitCounty': 'Submit',
            'nmTown': county_name
        }

        response = requests.post('https://elections.sos.ga.gov/Elections/advancedVotingInfoResult.do', headers=headers,
                                 data=data)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find("table", {"id": "Table1"})
        print(f"working on: {county_name}")
        for location_row in table.findAll("tr"):
            for loc_detail_row in location_row.findAll("tr"):
                detail_cells = loc_detail_row.findAll('td')
                first_col_label = detail_cells[0].findAll("label")
                if len(first_col_label) == 1 and len(detail_cells) == 2:
                    l_key = clean_str(first_col_label[0].text)
                    if l_key == 'pollplacename':
                        output[county_name].append(detail_cells[1].text)
    return output


def scrape_counties():
    headers = {
        'authority': 'elections.sos.ga.gov',
        'content-length': '0',
        'cache-control': 'max-age=0',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4283.0 Safari/537.36',
        'origin': 'https://elections.sos.ga.gov',
        'content-type': 'application/x-www-form-urlencoded',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-user': '?1',
        'sec-fetch-dest': 'document',
        'referer': 'https://elections.sos.ga.gov/Elections/advancedVotingInfoResult.do',
        'accept-language': 'en-US,en;q=0.9',
        'cookie': 'JSESSIONID=sTO7dIy-Cdl02MYw9fFR9EHsAxqnu5jbskfqEZ3t.ports-02; __cfduid=da5ee1548d3ba6d15d5ad0cba675f83fd1602533696; __cf_bm=4aaa4dcfba548bddac12a0ad18b729c0cccbc4ca-1602533779-1800-AeoCO/zWVbmT11B5JG1ViWqchK3OSaCN2wG3UBj+x+xd',
        'dnt': '1',
        'sec-gpc': '1',
    }

    response = requests.post('https://elections.sos.ga.gov/Elections/advancedVotingInfo.do', headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    print("parsing county list")
    counties = {}
    for option in soup.find_all('option'):
        counties[option['value']] = option.text
    return counties


def get_state_data(f_counties, f_voting_locations):
    if os.path.isfile(f_counties):
        counties = read_json(f_counties)
    else:
        counties = scrape_counties()
        save_json(counties, f_counties)
    if os.path.isfile(f_voting_locations):
        voting_locations = read_json(f_voting_locations)
    else:
        voting_locations = scrape_voting_location_by_county(counties)
        save_json(voting_locations, f_voting_locations)

    return counties, voting_locations


if __name__ == '__main__':
    counties, voting_locations = get_state_data('data/counties.json', 'data/voting_location.json')
