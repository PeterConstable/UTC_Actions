import requests
from bs4 import BeautifulSoup, Comment, Tag
from pathlib import Path
import pickle
import re
import os


utcDocRegistry_urls = {
    2000: "https://www.unicode.org/L2/L2000/Register-2000.html",
    2001: "https://www.unicode.org/L2/L2001/Register-2001.html",
    2002: "https://www.unicode.org/L2/L2002/Register-2002.html",
    2003: "https://www.unicode.org/L2/L2003/Register-2003.html",
    2004: "https://www.unicode.org/L2/L2004/Register-2004.html",
    2005: "https://www.unicode.org/L2/L2005/Register-2005.html",
    2006: "https://www.unicode.org/L2/L2006/Register-2006.html",
    2007: "https://www.unicode.org/L2/L2007/Register-2007.html",
    2008: "https://www.unicode.org/L2/L2008/Register-2008.html",
    2009: "https://www.unicode.org/L2/L2009/Register-2009.html",
    2010: "https://www.unicode.org/L2/L2010/Register-2010.html",
    2011: "https://www.unicode.org/L2/L2011/Register-2011.html",
    2012: "https://www.unicode.org/L2/L2012/Register-2012.html",
    2013: "https://www.unicode.org/L2/L2013/Register-2013.html",
    2014: "https://www.unicode.org/L2/L2014/Register-2014.html",
    2015: "https://www.unicode.org/L2/L2015/Register-2015.html",
    2016: "https://www.unicode.org/L2/L2016/Register-2016.html",
    2017: "https://www.unicode.org/L2/L2017/Register-2017.html",
    2018: "https://www.unicode.org/L2/L2018/Register-2018.html",
    2019: "https://www.unicode.org/L2/L2019/Register-2019.html",
    2020: "https://www.unicode.org/L2/L2020/Register-2020.html",
    2021: "https://www.unicode.org/L2/L2021/Register-2021.html",
    2022: "https://www.unicode.org/L2/L2022/Register-2022.html",
    2023: "https://www.unicode.org/L2/L2023/Register-2023.html",
    2024: "https://www.unicode.org/L2/L-curdoc.htm"
    }


# relative paths for pickle files to cache raw doc registry pages, 
# contents of the table in those pages, and content of UTC meeting
# minute pages
def createPickleJarFolder():
    if not os.path.exists("pickle_jar"):
        os.makedirs("pickle_jar")

createPickleJarFolder()
utcDocRegPages_pickleFile = 'pickle_jar/utcDocRegPages.pickle'
utcDocRegTables_pickleFile = 'pickle_jar/utcDocRegTables.pickle'
utcMinutesPages_pickleFile = 'pickle_jar/utcAllMeetingMinutesPages.pickle'

docRegistryTableColumns = ["Document Number", "URL", "Subject", "Source", "Date"]

whitespace_pattern = '[ \xa0\n]*'



#--------------------------------------------------------
#  Functions for yearly UTC document registry raw pages 

def getAllDocRegistryPages():
    """Get's html source for all of the UTC doc registry pages in
    utcDocRegistry_urls.
    
    Will load content from a local .pickle file, if present. Otherwise will fetch
    the pages from the Unicode site.

    Returns a dict with year as key and the html source text of the page as value.
    """

    pickle_file = Path(utcDocRegPages_pickleFile)
    if pickle_file.is_file():
        with open(utcDocRegPages_pickleFile, 'rb') as file:
            docRegPages = pickle.load(file)
    else:
        # retrieve pages; pickle for future use
        createPickleJarFolder()
        docRegPages = {}
        for year, url in utcDocRegistry_urls.items():
            print(f"retrieving doc registry page for {year}")
            docRegPages[year] = requests.get(url).text
        with open(utcDocRegPages_pickleFile, 'wb') as file:
            pickle.dump(docRegPages, file, protocol=pickle.HIGHEST_PROTOCOL)
    return docRegPages


def updateDocRegPagesToLatest():
    '''Gets an up-to-date dict of pages from utcDocRegistry_urls.
    
    Will start with a local .pickle file, if present. Otherwise, will fetch all
    pages from the Unicode site and create a .pickle file for future use.

    The current-year document registry is a live page, so the latest version of
    that page is always retrieved, and the .pickle file is updated.

    Returns a dict with year as key and the html source text of the page as value.
    '''

    # check if there's a pickle file; if not, we need to get all
    # pages regardless
    pickle_file = Path(utcDocRegPages_pickleFile)
    if not pickle_file.is_file():
        docRegPages = getAllDocRegistryPages
    else:
        with open(utcDocRegPages_pickleFile, 'rb') as file:
            docRegPages = pickle.load(file)

        # compare years in docRegPages with years in utcDocRegistry_urls
        # we know we need to update the current year regardless
        pickledYears = list(docRegPages)
        knownYears = list(utcDocRegistry_urls)
        yearsToGet = knownYears[len(pickledYears): -1] + [knownYears[-1]]
        for year in yearsToGet:
            print(f"retrieving doc registry page for {year}")
            url = utcDocRegistry_urls[year]
            docRegPages[year] = requests.get(url).text
        with open(utcDocRegPages_pickleFile, 'wb') as file:
            pickle.dump(docRegPages, file, protocol=pickle.HIGHEST_PROTOCOL)
    return docRegPages



#--------------------------------------------------------
#  Functions for yearly UTC document registries as dicts

def desoupTableRows(table: Tag, removeHeadingRow = True):
    '''Takes a soup of an HTML table and returns a list of the table rows, each
    a list of <td> or <th> soups.

    The soup .contents for a <table> may include items that are cruft: newlines,
    comments or <tr>...<tr> with only whitespace. Besides converting from soup of
    rows to list of rows, the cruft "rows" are removed.
    
    Also, the soup .contents for rows can include items that are cruft: newliness 
    or comments. Besides converting from soup of cells to list, the cruft "cells"
    are removed.

    If removeHeadingRow is true, removes the first row if it has <th> cells.
    '''

    # get all the <tr> elements -- returns a 'bs4.element.ResultSet' which is a list subclass
    rows = table.find_all("tr")

    # create a new list of lists: top level elements are list objects corresponding to rows;
    # 2nd level list elements are "td" or "th" soups
    rows = [ 
        [cell for cell in row.find_all(["th", "td"]) ]
         for row in rows if not (re.fullmatch(whitespace_pattern, row.text))
         ]
    
    # rows are now lists, and cells are soups

    # ignore heading row
    if removeHeadingRow and rows[0][0].name == 'th':
        del rows[0]

    return rows


def desoupDocRegTableCells(rows: list):
    '''Converts doc reg table cells from soups to strings.

    Takes a list of table rows that have soups for cells
    and returns a list of rows, each of which is a list of
    strings. The rows are assumed to come from UTC doc
    registry pages with specific columns expected. Each row
    will end up as a list of five str values:
      - doc number
      - URL (may be '')
      - subject (title; may be multi-line)
      - source (authors)
      - date

    The doc registry in some early years had an extra "project"
    column. This is removed.
    '''
    # For each row, get relevant string values out of cells.
    # The first cell has <a>; split into doc num and url.
    for row in rows:
        if len(row) > 4:
            del row[4:]
        doc_num = row[0].text
        a = row[0].a
        if a is None:
            row[0] = ''
        else:
            row[0] = a.get('href')
        row[1] = row[1].text
        row[2] = row[2].text
        row[3] = row[3].text
        row.insert(0, doc_num)
    return rows


def getDocRegTableFromPage(page):
    '''Takes doc registry HTML page content and returns a cleaned-up list.
    
    Each entry in the list represents a UTC document. The entry will be a list
    with five str values:
      - doc number
      - URL (may be '')
      - subject (title; may be multi-line)
      - source (authors)
      - date
    '''
    soup = BeautifulSoup(page, "lxml")
    tableSoup = soup.find(class_="contents").find(class_="subtle")
    rows = desoupTableRows(tableSoup)
    rows = desoupDocRegTableCells(rows)
    return rows


def getAllDocRegistryTables():
    '''Get the UTC doc registries as a dict of cleaned-up tables.
    
    Returns a dict of doc-registry tables keyed by year. Each dict is a list of
    rows, one row per document; and each row being a list of strings with
    document details:
      - doc number
      - URL (may be '')
      - subject (title; may be multi-line)
      - source (authors)
      - date
    
    Will retrieve the data from a local .pickle file, if present. If not, a
    .pickle file will be created for future use.
    '''

    # load from pickle file, if present
    pickle_file = Path(utcDocRegTables_pickleFile)
    if pickle_file.is_file():
        with open(utcDocRegTables_pickleFile, 'rb') as file:
            tables = pickle.load(file)
    else:
        # derive table soups; pickle them for future
        createPickleJarFolder()
        pages = getAllDocRegistryPages()
        tables = {}
        for year, page in pages.items():
            print(f"getting doc registry table for {year}")
            tables[year] = getDocRegTableFromPage(page)
        with open(pickle_file, 'wb') as file:
            pickle.dump(tables, file, protocol=pickle.HIGHEST_PROTOCOL)
    return tables


def updateDocRegTablesToLatest():
    '''Gets an up-to-date dict of yearly document registry tables.
    
    Will start with data from a local .pickle file, if present. Otherwise, a new
    .pickle file will be created for future use.

    The current-year document registry is a live page, so the latest version of
    that page is always retrieved, and the .pickle file is updated.

    Returns a dict with year as key and the document registry table for that
    year as value. Each yearly table is a list of lists.
    '''

    # check if there's a pickle file; if not, we need to get all
    # tables regardless
    pickle_file = Path(utcDocRegTables_pickleFile)
    if not pickle_file.is_file():
        docRegTables = getAllDocRegistryTables()
    else:
        # get pickled tables
        with open(utcDocRegTables_pickleFile, 'rb') as file:
            docRegTables = pickle.load(file)
        # compare years; we know we need to update the current year regardless
        pickledYears = list(docRegTables)
        knownYears = list(utcDocRegistry_urls)
        yearsToGet = knownYears[len(pickledYears): -1] + [knownYears[-1]]
        # before updating tables, update the pages
        docRegPages = updateDocRegPagesToLatest()
        # now update tables for recent years
        for year in yearsToGet:
            print(f"getting doc registry table for {year}")
            docRegTables[year] = getDocRegTableFromPage(docRegPages[year])
        with open(pickle_file, 'wb') as file:
            pickle.dump(docRegTables, file, protocol=pickle.HIGHEST_PROTOCOL)
    return docRegTables



#--------------------------------------------------------
#  Functions for yearly UTC meeting minutes documents

def findMinutesRowsInYearRows(table:list):
    minutes_rows = [
        row for row in table
        if re.search('minute', row[2].lower()) is not None
        and re.search('(utc|uct)', row[2].lower()) is not None
        and row[1][-3:] != 'pdf'
        and row[1][-9:] != 'NOTPOSTED'
        ]
    return minutes_rows


def getMinutesDetails(base_url, doc_row:list, lastMeetingNumber:int = 0):
    details = []
    m = re.search('((UTC|UCT) ?#?)([0-9]*)', doc_row[2])
    assert m is not None
    mtg_num = int(m.group(3))
    if mtg_num > lastMeetingNumber:
        url = base_url + doc_row[1]
        if lastMeetingNumber > 0:
            print(f"retrieving UTC meeting {mtg_num} minutes doc")
        page = requests.get(url).text
        soup = BeautifulSoup(page, 'lxml')
        title = soup.title.text
        details = [mtg_num, str(doc_row[0]), str(title), page]
    return details



def getAllMeetingMinutes():
    pickle_file = Path(utcMinutesPages_pickleFile)
    if pickle_file.is_file():
        with open(utcMinutesPages_pickleFile, 'rb') as file:
            allMtgMinutes = pickle.load(file)
    else:
        allMtgMinutes = {} #entries will have: mtg # (key), year, qtr, doc #, title, page content
        tables = updateDocRegTablesToLatest()
        for y, t in tables.items():
            # looking at doc registry for one year (y)
            year_reg_url = utcDocRegistry_urls[y]
            base_url = year_reg_url[:year_reg_url.rindex("/") + 1]
            # get the doc registry rows for UTC minutes -- minutes_rows is a list of lists
            minutes_rows = findMinutesRowsInYearRows(t)
            print(f"retrieving UTC meeting minutes docs for {y}")
            for i in range(len(minutes_rows)):
# The following lines are similar to lines in updateAllMeetingMinutesToLatest().
# However, they can't be refactored into a shared function. In getAllMeetingMinutes,
# we can fetch all minutes pages. But in updateAllMeetingMinutesToLatest() we don't
# want to fetch pages that have previously been cached. In that case, we filter
# minutes_rows checking the meeting number in the row title field. But in some early
# doc registry pages, the title field for UTC meeting docs didn't always include
# the meeting number, and the only way to get the meeting number is to fetch the
# page.
                url = base_url + minutes_rows[i][1]
                page = requests.get(url).text
                soup = BeautifulSoup(page, 'lxml')
                title = soup.title.text
                m = re.search('(UTC ?#?)([0-9]*)', title)
                assert m is not None
                mtg_num = int(m.group(2))
                allMtgMinutes[mtg_num] = [y, i + 1, str(minutes_rows[i][0]), str(title), page]

        with open(pickle_file, 'wb') as file:
            pickle.dump(allMtgMinutes, file, protocol=pickle.HIGHEST_PROTOCOL)
            pass
    return allMtgMinutes


def updateAllMeetingMinutesToLatest():
    pickle_file = Path(utcMinutesPages_pickleFile)
    if not pickle_file.is_file():
        allMtgMinutes = getAllMeetingMinutes()
    else:
        # get pickled minutes info
        with open(utcMinutesPages_pickleFile, 'rb') as file:
            allMtgMinutes = pickle.load(file)
        # get details on last stored meeting
        allMeetings = list(allMtgMinutes)
        lastMeetingNumber = allMeetings[-1]
        lastMeetingYear = allMtgMinutes[lastMeetingNumber][0]
        # compare to known
        lastKnownYear = list(utcDocRegistry_urls)[-1]
        yearsToCheck = list(range(lastMeetingYear, lastKnownYear + 1))

        docRegTables = updateDocRegTablesToLatest()
        for y in yearsToCheck:
            # looking at doc registry for one year (y)
            year_reg_url = utcDocRegistry_urls[y]
            base_url = year_reg_url[:year_reg_url.rindex("/") + 1]
            # get the doc registry rows for UTC minutes
            yearTable = docRegTables[y]
            minutes_rows = findMinutesRowsInYearRows(yearTable)

            for i in range(len(minutes_rows)):
                m = re.search('(UTC ?#?)([0-9]*)', minutes_rows[i][2])
                assert m is not None
                mtg_num = int(m.group(2))
                if mtg_num > lastMeetingNumber:
                    url = base_url + minutes_rows[i][1]
                    print(f"retrieving UTC meeting {mtg_num} minutes doc")
                    page = requests.get(url).text
                    soup = BeautifulSoup(page, 'lxml')
                    title = soup.title.text
                    m = re.search('(UTC ?#?)([0-9]*)', title)
                    assert m is not None
                    mtg_num = int(m.group(2))
                    allMtgMinutes[mtg_num] = [y, i + 1, str(minutes_rows[i][0]), str(title), page]

        with open(pickle_file, 'wb') as file:
            pickle.dump(allMtgMinutes, file, protocol=pickle.HIGHEST_PROTOCOL)
    return allMtgMinutes


def findActionsInMinutes(doc:list, actionType):
    ''' Gets a list of the actions from a minutes doc.

        Takes a row from a minutes entry, and an action type string.
       
        The minutes entry row is a list with 5 elements, the
        last element being the page content. 
        
        The expected actionType values are "AI", "consensus", "motion" or "note".

        From the page content, uses BeautifulSoup to find all the motions 
        -- that is, all <p> or <blockquote> elements containing a string
        correcponding to the action type (e.g., "Consensus" or "consensus"
        for a consensus action type). It then returns a list of the text
        content from those elements.
    '''
    pageContent = doc[-1]
    soup = BeautifulSoup(pageContent, 'lxml')

    # define the re patterns for the action types
    patterns = {
        "AI": "A(C|c)(T|t)(I|i)(O|o)(N|n) (I|i)(T|t)(E|e)(M|m)",
        "consensus": "C(O|o)(N|n)(S|s)(E|e)(N|n)(S|s)(U|u)(S|s)",
        "motion": "M(O|o)(T|t)(I|i)(O|o)(N|n)",
        "note": "N(O|o)(T|t)(E|e)"
        }
    pattern = patterns[actionType]
    actionStrings = soup.find_all(string = re.compile(pattern))
    actions = [
        # Different minutes docs are structured differently (and some, badly)
        s.find_parent(["blockquote", "dd", "div", "p", "ul"]).text.replace('\n', ' ').replace('\r', ' ').replace('\xa0', ' ')
        for s in actionStrings
        ]
    return actions


def getAnchorParentText(a):
    try:
#        p = a.find_parent(["blockquote", "dd", "div", "p", "ul"]).text.replace('\n', ' ').replace('\r', ' ').replace('\xa0', ' ').replace('  ', ' ')
        p = re.sub('\s+',' ', a.find_parent(["blockquote", "dd", "div", "p", "ul"]).text)
    except:
        print(f"exception: {a.text}")
        p = None
    return p


def findAllTaggedActionsInMinutes(doc:list):
    ''' Gets a list of actions (all types) from a minutes doc. This assumes a
        convention applied since UTC #90 that a "tagging" tool is run on the
        minutes file turning the ID prefix for each action (e.g., "[123-C45]")
        into an anchor element.

        (More precisely, the anchor is applied to the string within square brackets.)

        Takes a row from a minutes entry and returns a list of action strings.
    '''
    pageContent = doc[-1]
    soup = BeautifulSoup(pageContent, 'lxml')
    # define the pattern for the action ID contained in the anchor element
    pattern = '[0-9]{0,3}-(AI?|C|L|M|N)[0-9a-z]{1,4}'
    actionAnchorElements = soup.find_all("a", string=re.compile(pattern))
    actions = [
        # e.find_parent(["blockquote", "div", "p", "ul"]).text
        getAnchorParentText(e)
        for e in actionAnchorElements
        ]
    return actions



def compileActionsFromAllMinutes(actionType):
    ''' Compiles all actions of a given type from all UTC meetings.

        Takes an action type string: "AI", "consensus", "motion" or "note".

        Returns a dictionary with entries of the form mtgNum: [actions list].
        For example compilesActionsFromAllMinutes("AI")[179] would return the
        list of all action items from meeting 179.
    '''
    allActions = {}
    meetings = getAllMeetingMinutes()
    for mtgNum, mtg in meetings.items():
        print(f"getting actions for meeting {mtgNum}")
        actions = findActionsInMinutes(mtg, actionType)
        allActions[mtgNum] = actions
    return allActions


def compileAllTaggedActionsFromAllMinutes():
    ''' Compiles all actions of all types from all UTC meetings for which
        the minutes have had the "tag" tool applied (started with UTC #90).
    '''
    allActions = {}
    meetings = getAllMeetingMinutes()
    for mtgNum, mtg in meetings.items():
        if mtgNum >= 90:
            print(f"getting actions for meeting {mtgNum}")
            actions = findAllTaggedActionsInMinutes(mtg)
            allActions[mtgNum] = actions
    return allActions


def writeToFileAllTaggedActionsFromAllMinutes(filename: str):
    allActions = compileAllTaggedActionsFromAllMinutes()
    f = open(filename, "w", encoding="utf-8")
    for mtgNum, actions in allActions.items():
        f.write(str(mtgNum) + "\n")
        for a in actions:
            f.write(a + "\n")
    f.close()



# utcDocRegPages = getAllDocRegistryPages()
# utcDocRegPages = updateDocRegPagesToLatest()

# utcDocRegTables = getAllDocRegistryTables()
# utcDocRegTables = updateDocRegTablesToLatest()

# utc_minutes = getAllMeetingMinutes()
utc_minutes = updateAllMeetingMinutesToLatest()




