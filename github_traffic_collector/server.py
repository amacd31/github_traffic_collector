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
    'UV': 'Number of unique views'
}

@app.route("/")
def index():
    return """
<ul>
  <li><a href="/summary/UV">Unique views summary</a></li>
  <li><a href="/summary/V">Views summary</a></li>
  <li><a href="/summary/UC">Unique clones summary</a></li>
  <li><a href="/summary/C">Clones summary</a></li>
</ul>
"""

@app.route("/plot/<measurand>/<user>/<repo>")
def plot(measurand, user, repo):


    fig=Figure(figsize=(10,2.5))
    ax=fig.add_subplot(111)

    user_repo = user + '/' + repo

    ts = db.read(user_repo, 'D', measurand = measurand)

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
    img = '<img src="/plot/{0}/{1}" alt="{2}" />\n'
    for ts_id in db.list_ids():
        if len(db.read(ts_id, 'D', measurand = measurand)) > 0:
            title = "{0} for {1}".format(MEASURAND_NAME[measurand], ts_id)
            content += img.format(measurand, ts_id, title)

    return content

@app.route("/repo/<user>/<repo>/<int:year>/<int:month>/<int:day>")
def repo(user, repo, year, month, day):
    content = ""
    data_dir = os.path.join(DATASTORE, user, repo, str(year), str(month))
    date_str = date(year, month, day).strftime('%Y%m%d')

    referrer_glob = os.path.join(data_dir, date_str + "*_referrer.json")
    infile = glob.glob(referrer_glob)[-1]
    referrer_data = pd.read_json(infile)

    referrer_data.set_index('referrer', inplace=True)
    referrer_data.to_html()
    content += referrer_data.to_html()

    path_glob = os.path.join(data_dir, date_str + "*_path.json")
    infile = glob.glob(path_glob)[-1]
    path_data = pd.read_json(infile)

    path_data.set_index('title', inplace=True)
    path_data.to_html()

    content += path_data.to_html()

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
