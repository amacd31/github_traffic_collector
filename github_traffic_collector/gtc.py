import argparse
import os
import pandas as pd
import requests
import shutil
import yaml

import logging
LOGGER = logging.getLogger(__name__)

from datetime import datetime
from phildb.create import create
from phildb.database import PhilDB
from phildb.exceptions import DuplicateError
from prompt_toolkit import prompt
from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

GITHUB_API_HOST = 'https://api.github.com'

def __get_page_links(request):
    links = {}
    if 'Link' in request.headers:
        headers = request.headers['Link'].split(', ')
        for header in headers:
            link, ref = header.split('; ')
            link = link.strip('<').strip('>')
            links[ref[5:][:-1]] = link

    return links


def main():
    parser = argparse.ArgumentParser(description='Github traffic collector.')
    parser.add_argument('datastore', help="Location to store data including a PhilDB database", nargs='?')
    parser.add_argument('--debug', action='store_true', help="Enable debug logging information.")
    parser.add_argument('--version', action='version', version='%(prog)s ' + __version__)

    args = parser.parse_args()

    logging.basicConfig()
    LOGGER.setLevel(logging.INFO)
    if args.debug:
        LOGGER.setLevel(logging.DEBUG)
        LOGGER.critical(
            "\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
            "DEBUG OUTPUT INCLUDES URLS WITH YOUR GITHUB AUTH TOKEN.\n"
            "BE SURE TO REDACT THE TOKEN BEFORE SHARING THE OUTPUT.\n"
            "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
        )

    collect_traffic_data(args.datastore)


def collect_traffic_data(datastore):
    if not os.path.exists(datastore):
        os.mkdir(datastore)

    db_path = os.path.join(datastore, 'gtc_phildb')
    if not os.path.exists(db_path):
        create(db_path)

        db = PhilDB(db_path)

        db.add_source('GITHUB', 'Github')
    else:
        db = PhilDB(db_path)

    try:
        db.add_measurand('C', 'CLONES', 'Total number of git clones')
    except DuplicateError:
        pass

    try:
        db.add_measurand('UC', 'UNIQUE_CLONES', 'Number of unique git clones')
    except DuplicateError:
        pass

    try:
        db.add_measurand('V', 'VIEWS', 'Total number of views')
    except DuplicateError:
        pass

    try:
        db.add_measurand('UV', 'UNIQUE_VIEWS', 'Number of unique views')
    except DuplicateError:
        pass

    try:
        db.add_measurand('S', 'STARGAZERS', 'Number of repository stars')
    except DuplicateError:
        pass

    try:
        db.add_measurand('W', 'WATCHERS', 'Number of repository watchers')
    except DuplicateError:
        pass

    config_path = os.path.join(datastore, 'config.yaml')
    if not os.path.exists(config_path):
        access_token = prompt('Enter Github API personal access token to use for authentication: ')
        config = {
            'access_token': access_token
        }
        with open(config_path, 'w') as c:
            yaml.dump(config, c)

    else:
        with open(config_path, 'r') as c:
            config = yaml.safe_load(c)

    params = { 'access_token': config['access_token'], 'per_page': 100}

    repos_url = GITHUB_API_HOST + '/user/repos'
    repo_request = requests.get(repos_url, params = params)
    LOGGER.debug(repo_request.url)

    repo_list = repo_request.json()

    links = __get_page_links(repo_request)
    while 'last' in links:
        repo_request = requests.get(links['next'])
        LOGGER.debug(repo_request.url)
        repo_list += repo_request.json()
        links = __get_page_links(repo_request)

    views_url = GITHUB_API_HOST + "/repos/{0}/traffic/views"
    clones_url = GITHUB_API_HOST + "/repos/{0}/traffic/clones"
    referrers_url = GITHUB_API_HOST + "/repos/{0}/traffic/popular/referrers"
    paths_url = GITHUB_API_HOST + "/repos/{0}/traffic/popular/paths"
    repo_info_url = GITHUB_API_HOST + "/repos/{0}"

    now = datetime.today()
    year = now.year
    month = now.month
    date_str = now.strftime('%Y%m%d_%H%M')
    num_repos = len(repo_list)
    LOGGER.info("Found %d repositories to fetch traffic information for", num_repos)
    count = 1
    for repository in repo_list:
        repo_name = repository['full_name']
        LOGGER.info('Processing %d/%d: %s', count, num_repos, repo_name)

        repo_data_path = os.path.join(datastore, repo_name, str(year), str(month))
        os.makedirs(repo_data_path, exist_ok=True)

        r = requests.get(referrers_url.format(repo_name), params = params, stream=True)
        LOGGER.debug(r.url)
        with open(os.path.join(repo_data_path, '{0}_referrer.json'.format(date_str)), 'wb') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)

        r = requests.get(paths_url.format(repo_name), params = params, stream=True)
        LOGGER.debug(r.url)
        with open(os.path.join(repo_data_path, '{0}_path.json'.format(date_str)), 'wb') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)

        try:
            db.add_timeseries(repo_name)
        except DuplicateError:
            pass

        try:
            db.add_timeseries_instance(repo_name, 'D', '', source = 'GITHUB', measurand = 'C')
            db.add_timeseries_instance(repo_name, 'D', '', source = 'GITHUB', measurand = 'UC')
            db.add_timeseries_instance(repo_name, 'D', '', source = 'GITHUB', measurand = 'V')
            db.add_timeseries_instance(repo_name, 'D', '', source = 'GITHUB', measurand = 'UV')
        except DuplicateError:
            pass

        clones_request = requests.get(clones_url.format(repo_name), params = params)
        LOGGER.debug(clones_request.url)
        clones_json = clones_request.json()
        clones_df = pd.DataFrame(clones_json['clones'])

        if len(clones_df) > 0:
            clones_df.set_index(pd.to_datetime(clones_df['timestamp']), inplace=True)
            clones_df = clones_df.asfreq('D').fillna(0)

            db.write(repo_name, 'D', clones_df['count'], measurand = 'C')
            db.write(repo_name, 'D', clones_df['uniques'], measurand = 'UC')


        views_request = requests.get(views_url.format(repo_name), params = params)
        LOGGER.debug(views_request.url)
        views_json = views_request.json()
        views_df = pd.DataFrame(views_json['views'])

        if len(views_df) > 0:
            views_df.set_index(pd.to_datetime(views_df['timestamp']), inplace=True)
            views_df = views_df.asfreq('D').fillna(0)

            db.write(repo_name, 'D', views_df['count'], measurand = 'V')
            db.write(repo_name, 'D', views_df['uniques'], measurand = 'UV')

        repo_request = requests.get(repo_info_url.format(repo_name), params = params)
        LOGGER.debug(repo_request.url)
        repo = repo_request.json()
        try:
            db.add_timeseries_instance(repo_name, 'D', '', source = 'GITHUB', measurand = 'S')
        except DuplicateError:
            pass

        db.write(repo_name, 'D', pd.Series([repo['stargazers_count']], [now.date()]), measurand = 'S')

        try:
            db.add_timeseries_instance(repo_name, 'D', '', source = 'GITHUB', measurand = 'W')
        except DuplicateError:
            pass
        db.write(repo_name, 'D', pd.Series([repo['subscribers_count']], [now.date()]), measurand = 'W')

        count += 1

if __name__ == "__main__":
    main()
