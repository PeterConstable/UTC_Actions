# UTC_Actions

Python module to get the yearly UTC document registries, UTC meeting minutes and UTC actions, since 2000.

## Overview of features

This module has functions to retrieve UTC document registry pages since 2000; to massage the content of each page derive the yearly registry as a a list of lists (list of rows, each a list of cell values); and to retrieve all of the UTC meeting minutes pages from across the years since 2000.

To avoid repeating page retrievals on each use, or repeating other slow operations like processing the raw HTML pages, HTML page contents and other results are stored locally using the Python pickle module. If the .pickle file for pages or other content isn't present, the slower operations will be run and a new .pickle file will be generated.

**Coming:** functions to extract motion, consensus and action-item details from the minutes.

## Maintenance

The module has a hard-coded list of URLs for the yearly UTC document registry pages. (Actually, it's a dictionary—year: url.) That will need to be maintained year by year to add additional years.

There are functions to update certain data, such as the .pickle file with the raw HTML pages. These functions only update for the most recent year (since the UTC doc register for the current year is live and frequently updated), or for recent years that are missing from the data (as the list of per-year URLs is updated).

## Dependencies

This module relies on some packages that not typically bundled with Python distributions:

* [**reguests**](https://requests.readthedocs.io/en/master/): provides high-level HTTP support, used here to get pages
* [**BeautifulSoup**](https://www.crummy.com/software/BeautifulSoup/): provides support for parsing HTML content
* [**lxml**](https://lxml.de/): low-level XML and HTML parsing support, utilized here in conjunction with BeautifulSoup
