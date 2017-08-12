import argparse
import glob
import os
import pandas as pd
import seaborn as sns

from datetime import date
from io import BytesIO

from flask import Flask, make_response
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.dates import DateFormatter
from phildb.database import PhilDB

app = Flask("Github traffic controller data viewer")

MEASURAND_NAME = {
    'C': 'Total number of git clones',
    'UC': 'Number of unique git clones',
    'V': 'Total number of views',
    'UV': 'Number of unique views',
    'S': 'Number of Star Gazers',
    'W': 'Number of Watchers',
}

@app.route("/")
def index():
    return """
<ul>
  <li><a href="/summary/UV">Unique views summary</a></li>
  <li><a href="/summary/V">Views summary</a></li>
  <li><a href="/summary/UC">Unique clones summary</a></li>
  <li><a href="/summary/C">Clones summary</a></li>
  <li><a href="/summary/S">Star Gazers summary</a></li>
  <li><a href="/summary/W">Watchers summary</a></li>
</ul>
"""

@app.route("/plot/<measurand>/<user>/<repo>")
def plot(measurand, user, repo):


    fig=Figure(figsize=(10,2.5))
    ax=fig.add_subplot(111)

    user_repo = user + '/' + repo

    ts = db.read(user_repo, 'D', measurand = measurand).asfreq('D').fillna(0)

    ts.plot(ax = ax)

    ax.set_title("{0} for {1}".format(MEASURAND_NAME[measurand], user_repo))
    fig.tight_layout()
    canvas=FigureCanvas(fig)
    png_output = BytesIO()
    canvas.print_png(png_output)
    response=make_response(png_output.getvalue())
    response.headers['Content-Type'] = 'image/png'
    return response

@app.route("/summary/<measurand>")
def summary(measurand):
    content = ""
    img = '<a href="/repo/{1}"><img src="/plot/{0}/{1}" alt="{2}" /></a>\n'
    for ts_id in db.list_ids():
        if len(db.read(ts_id, 'D', measurand = measurand)) > 0:
            title = "{0} for {1}".format(MEASURAND_NAME[measurand], ts_id)
            content += img.format(measurand, ts_id, title)

    return content

@app.route("/repo/<user>/<repo>/<int:year>/<int:month>/<int:day>")
def repo_information(user, repo, year, month, day):
    date_str = date(year, month, day).strftime('%Y%m%d')
    glob_start = os.path.join(str(year), str(month), date_str)

    return repo_for_last_globbed(user, repo, glob_start)

@app.route("/repo/<user>/<repo>")
def latest_repo_information(user, repo):
    return repo_for_last_globbed(user, repo, os.path.join('*', '*', ''))

def repo_for_last_globbed(user, repo, glob_start):
    content = ""
    img = '<img src="/plot/{0}/{1}" alt="{2}" />\n'
    title = "{0} for {1}".format(MEASURAND_NAME['UV'], user + '/' + repo)
    content += img.format('UV', user + '/' + repo, title)
    data_dir = os.path.join(DATASTORE, user, repo)

    referrer_glob = os.path.join(data_dir, glob_start + "*_referrer.json")
    infile = glob.glob(referrer_glob)[-1]
    referrer_data = pd.read_json(infile)

    try:
        referrer_data.set_index('referrer', inplace=True)
        content += referrer_data.to_html()
    except KeyError:
        content += "<p>No referrer data found</p>"

    path_glob = os.path.join(data_dir, glob_start + "*_path.json")
    infile = glob.glob(path_glob)[-1]
    path_data = pd.read_json(infile)

    try:
        path_data.set_index('title', inplace=True)
        content += path_data.to_html()
    except KeyError:
        content += "<p>No paths data found</p>"


    return content

def main():
    parser = argparse.ArgumentParser(description='Github traffic collector server.')
    parser.add_argument('datastore', help="Location of datastore to visualise")
    parser.add_argument('--debug', action="store_true", help="Location of datastore to visualise")

    args = parser.parse_args()
    global DATASTORE
    DATASTORE = args.datastore

    global db
    db = PhilDB(os.path.join(args.datastore, 'gtc_phildb'))
    app.run(debug = args.debug)

if __name__ == "__main__":
    main()
