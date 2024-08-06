# UTC_Actions

Python module to get the yearly UTC document registries, UTC meeting minutes and UTC actions, since 2000.

## Overview of features

This module has various functions for interacting with UTC document registry pages since 2000, including:
- retrieval of the document registry pages and massaging the content of each page to derive the yearly registry as a a list of lists (list of rows, each a list of cell values);
- searching for text in the subject field of the registry for a specific year or all years;
- retrieving all of the UTC meeting minutes pages from all years since 2000.
- extracting motion, consensus and action-item details from the minutes of a given UTC meeting or all UTC meetings (2002 or later)
- searching for text (regex patterns) in UTC minutes pages.

To avoid repeating page retrievals on each use, or repeating other slow operations like processing the raw HTML pages, HTML page contents and other results are stored locally using the Python pickle module. If the .pickle file for pages or other content isn't present, the slower operations will be run and a new .pickle file will be generated. When the module is loaded, the registry page for the latest year will be retrieved to update the local cache.


## Maintenance

The module has a hard-coded list of URLs for the yearly UTC document registry pages. (Actually, it's a dictionary: {year: url}.) That will need to be maintained year by year to add additional years.

There are functions to update certain data, such as the .pickle file with the raw HTML pages. These functions only update for the most recent year (since the UTC doc register for the current year is live and frequently updated), or for recent years that are missing from the data (as the list of per-year URLs is updated).

## Dependencies

This module relies on some packages that not typically bundled with Python distributions:

* [**reguests**](https://requests.readthedocs.io/en/master/): provides high-level HTTP support, used here to get pages
* [**BeautifulSoup**](https://www.crummy.com/software/BeautifulSoup/): provides support for parsing HTML content
* [**lxml**](https://lxml.de/): low-level XML and HTML parsing support, utilized here in conjunction with BeautifulSoup

Dependencies are captured in the `requirements.txt` file and can be installed using the following command line:

> python -m pip install -r requirements.txt
