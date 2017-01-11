Github Traffic Collector
==============

Download Github traffic information via the Github API into a PhilDB database.
The purpose of this project is to allow the creation of a long term record of
traffic to all the repositories owned by the running user.

Dependencies
------------

Requires Python 3.4 or greater (tested with Python 3.5 on Mac OSX).

Installation
------------

Github traffic collector is pip installable.

The latest development version can be installed from github with::

    pip install git+https://github.com/amacd31/github_traffic_collector.git

Usage
=====

The commandline tool included in this package is called `gtc`.

::

    $ gtc --help
    usage: gtc [-h] [datastore]

    Github traffic collector.

    positional arguments:
      datastore   Location to store data including a PhilDB database

      optional arguments:
        -h, --help  show this help message and exit

Running for the first time will create the output directory and prompt for a Github
personal access token (generate here: https://github.com/settings/tokens, only requires repository read permission).
Subsequent runs will load the data into the existing datastore
and use the personal token stored in a yaml configuration file inside the datastore.

::

    $ gtc amacd31_git_traffic
    Enter Github API personal acess token to use for authentication:
    Processing: amacd31/bom_data_parser
    Processing: amacd31/bom_ssf_reader
    Processing: amacd31/catchment_tools
    ...

The traffic can be read back out of the PhilDB database storing the logged data.

::

    $ phil amacd31_git_traffic/gtc_phildb
    Python 3.5.2 |Anaconda 4.2.0 (x86_64)| (default, Jul  2 2016, 17:52:12)
    Type "copyright", "credits" or "license" for more information.

    IPython 5.1.0 -- An enhanced Interactive Python.
    ?         -> Introduction and overview of IPython's features.
    %quickref -> Quick reference.
    help      -> Python's own help system.
    object?   -> Details about 'object', use 'object??' for extra details.


    Running timeseries database: amacd31_git_traffic/gtc_phildb
    Access the 'db' object to operate on the database.

    Run db.help() for a list of available commands.

    In[1]: db.read('amacd31/bom_data_parser', 'D', measurand = 'V')
    Out[2]:
    date
    2017-01-03    3.0
    2017-01-04    0.0
    2017-01-05    0.0
    2017-01-06    3.0
    Name: value, dtype: float64

The 'measurand' field specifies which data to read back out where the available measurands and their short codes are:

    ==  ===========================
    C   Total number of git clones
    UV  Number of unique git clones
    V   Total number of views
    UV  Number of unique views
    ==  ===========================

Visualise the results using the server.

::

    gtc-server amacd31_git_traffic/gtc_phildb/
     * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
