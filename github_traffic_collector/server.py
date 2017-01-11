import argparse
import seaborn as sns

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

def main():
    parser = argparse.ArgumentParser(description='Github traffic collector server.')
    parser.add_argument('datastore', help="Location of datastore to visualise")
    parser.add_argument('--debug', action="store_true", help="Location of datastore to visualise")

    args = parser.parse_args()

    global db
    db = PhilDB(args.datastore)
    app.run(debug = args.debug)

if __name__ == "__main__":
    main()
