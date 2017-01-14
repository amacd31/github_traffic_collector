import argparse
import os
import pandas as pd
import requests
import shutil
import yaml

from datetime import datetime
from phildb.create import create
from phildb.database import PhilDB
from phildb.exceptions import DuplicateError
from prompt_toolkit import prompt

GITHUB_API_HOST = 'https://api.github.com'

def main():
    parser = argparse.ArgumentParser(description='Github traffic collector.')
    parser.add_argument('datastore', help="Location to store data including a PhilDB database", nargs='?')

    args = parser.parse_args()

    if not os.path.exists(args.datastore):
        os.mkdir(args.datastore)

    db_path = os.path.join(args.datastore, 'gtc_phildb')
    if not os.path.exists(db_path):
        create(db_path)

        db = PhilDB(db_path)

        db.add_source('GITHUB', 'Github')
        db.add_measurand('C', 'CLONES', 'Total number of git clones')
        db.add_measurand('UC', 'UNIQUE_CLONES', 'Number of unique git clones')
        db.add_measurand('V', 'VIEWS', 'Total number of views')
        db.add_measurand('UV', 'UNIQUE_VIEWS', 'Number of unique views')
    else:
        db = PhilDB(db_path)

    config_path = os.path.join(args.datastore, 'config.yaml')
    if not os.path.exists(config_path):
        access_token = prompt('Enter Github API personal acess token to use for authentication: ')
        config = {
            'access_token': access_token
        }
        with open(config_path, 'w') as c:
            yaml.dump(config, c)

    else:
        with open(config_path, 'r') as c:
            config = yaml.safe_load(c)

    params = { 'access_token': config['access_token'] }

    repos_url = GITHUB_API_HOST + '/user/repos'
    repo_list = requests.get(repos_url, params = params).json()

    views_url = GITHUB_API_HOST + "/repos/{0}/traffic/views"
    clones_url = GITHUB_API_HOST + "/repos/{0}/traffic/clones"
    referrers_url = GITHUB_API_HOST + "/repos/{0}/traffic/popular/referrers"

    now = datetime.today()
    year = now.year
    month = now.month
    date_str = now.strftime('%Y%m%d_%H%M')
    for repo in repo_list:
        repo_name = repo['full_name']
        print('Processing: {0}'.format(repo_name))

        repo_data_path = os.path.join(args.datastore, repo_name, str(year), str(month))
        os.makedirs(repo_data_path, exist_ok=True)

        r = requests.get(referrers_url.format(repo_name), params = params, stream=True)
        with open(os.path.join(repo_data_path, '{0}_referrer.json'.format(date_str)), 'wb') as f:
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

        clones_json = requests.get(clones_url.format(repo_name), params = params).json()
        clones_df = pd.DataFrame(clones_json['clones'])

        if len(clones_df) > 0:
            clones_df.set_index(pd.to_datetime(clones_df['timestamp']), inplace=True)
            clones_df = clones_df.asfreq('D').fillna(0)

            db.write(repo_name, 'D', clones_df['count'], measurand = 'C')
            db.write(repo_name, 'D', clones_df['uniques'], measurand = 'UC')


        views_json = requests.get(views_url.format(repo_name), params = params).json()
        views_df = pd.DataFrame(views_json['views'])

        if len(views_df) > 0:
            views_df.set_index(pd.to_datetime(views_df['timestamp']), inplace=True)
            views_df = views_df.asfreq('D').fillna(0)

            db.write(repo_name, 'D', views_df['count'], measurand = 'V')
            db.write(repo_name, 'D', views_df['uniques'], measurand = 'UV')

if __name__ == "__main__":
    main()
