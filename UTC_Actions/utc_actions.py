import requests
from bs4 import BeautifulSoup, Comment, Tag, NavigableString
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
    2024: "https://www.unicode.org/L2/L2024/Register-2024.html",
    2025: "https://www.unicode.org/L2/L-curdoc.htm"
    }

# The doc registry index pages don't reliably include meeting #s for
# UTC meetings before UTC #90. The following hard codes the index
# table row data for some early meetings.
earlyUtcMinutesRows = {
    82: (2000, 1, ['L2/00-005', '00005.htm', 'Minutes of UTC #82 in San Jose', 'Lisa Moore', '2000-02-09']),
    83: (2000, 2, ['L2/00-115', '00115.htm', 'Minutes Of UTC Meeting #83', 'Lisa Moore', '2000-05-07']),
    84: (2000, 3, ['L2/00-187', '00187.htm', 'UTC minutes – Boston, August 8-11, 2000', 'Lisa Moore', '2000-08-23']),
    85: (2000, 4, ['L2/00-324', '00324.htm', 'Minutes from the UTC meeting in San Diego', 'Lisa Moore', '2000-12-27']),
    86: (2001, 1, ['L2/01-012', '01012.htm', 'Minutes UTC #86 in Mountain View, Jan 2001', 'Lisa Moore', '2001-02-07']),
    87: (2001, 2, ['L2/01-184', '01184.htm', 'Minutes from the UTC/L2 meeting ', 'Lisa Moore', '2001-06-18']),
    88: (2001, 3, ['L2/01-295', '01295.htm', 'Minutes from the UTC/L2 meeting #88 (R)', 'Lisa Moore', '2001-09-07']),
    89: (2001, 4, ['L2/01-405', '01405.htm', 'Minutes from the UTC/L2 meeting in Mountain View, November 6-9, 2001', 'Lisa Moore', '2001-11-12'])
}
earlyMinutes = {
    2000: [82, 83, 84, 85],
    2001: [86, 87, 88, 89]
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


def getAllDocRegistryTables(forceRefresh = False):
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
    if pickle_file.is_file() and not forceRefresh:
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


def updateDocRegTablesWithLatest():
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



def searchForTextInDocRegTable(text, year, ignoreCase = True, textIsRegExPattern = False):
    ### Searches in the subject field of the doc registry index for the specified year, 
    ### and returns a list of results.
    ###
    ### The results are a list of row metadata from the doc registry table, i.e.,
    ### [ [docNum, url, subject, author, date]* ].
    ###
    ### When searching in the subject field, \t, \r and \n will be converted to space before
    ### the search is performed, and will be converted in the result.
    ###
    ### If a doc row has 'NOTPOSTED' in the url, a match in the subject can still be returned.
    ###
    ### If textIsRegExPattern is True, that will be used as the search pattern over the
    ### entire content of the subject field. If False, then


    # check that year is in range of known years
    if year not in list(utcDocRegistry_urls):
        print(f'UTC document registry infomation is not available for {year}.')
        return
    
    if not textIsRegExPattern:
        text = ".*" + text + ".*"
    if ignoreCase:
        pattern = re.compile(text, re.IGNORECASE)
    else:
        pattern = re.compile(text)

    docRegTable = utcDocRegTables[year]
    docResultRows = [
        r for r in docRegTable
        if re.match(pattern, re.sub('\s+', ' ', r[2])) is not None
    ]
    return docResultRows


def searchForTextInAllDocRegTables(text, ignoreCase = True):
    # returns a dict {year: [results]}
    results = {}
    count = 0
    for year in list(utcDocRegTables):
        result = searchForTextInDocRegTable(text, year, ignoreCase)
        if len(result) != 0:
            count += len(result)
            results[year] = result
    if count == 0:
        print("No matches found")
    elif count == 1:
        print("1 match found")
    else:
        print(f'{count} matches found')
    return results


def writeToFileSearchForTextInDocRegistryResults(filename:str, text:str, year = None, ignoreCase = True):
    if year is None:
        results = searchForTextInAllDocRegTables(text, ignoreCase)
    else:
        results = searchForTextInDocRegTable(text, year, ignoreCase)
    if len(results) == 0:
        print("No results found")
    else:
        f = open(filename, "w", encoding="utf-8")
        for year, resultRows in results.items():
            f.write(f'{str(year)}:\n')
            for i in range(len(resultRows)):
                resultRow = resultRows[i]
                subjectText = re.sub('\s+', ' ', resultRow[2])
                f.write(f'    {i+1}: {resultRow[0]}: {subjectText}\n')
        f.close()


#--------------------------------------------------------
#  Functions for UTC meeting minutes documents

def getFirstAndLastKnownUtcMeetings():
    tables = utcDocRegTables
    earliest = 999
    latest = 0
    for y, t in tables.items():
        if y in list(earlyMinutes):
            if earlyMinutes[y][0] < earliest:
                earliest = earlyMinutes[y][0]
            if earlyMinutes[y][-1] > latest:
                latest = earlyMinutes[y][-1]
        else:
            minutes_rows = findMinutesRowsInYearRows(y, t)
            firstMtgNum = getMeetingNumberFromMinutesRow(minutes_rows[0])
            if firstMtgNum < earliest:
                earliest = firstMtgNum
            lastMtgNum = getMeetingNumberFromMinutesRow(minutes_rows[-1])
            if lastMtgNum > latest:
                latest = lastMtgNum
    return (earliest, latest)


def getMeetingNumberFromMinutesRow(minutesRow):
    # Assumes the row is not from years 2001 and earlier
    m = re.search('(UTC ?#?)([0-9]*)', minutesRow[2])
    assert m is not None
    return int(m.group(2))

def getMinutesRowsForEarlyYear(year):
    meetings = earlyMinutes[year]
    minutesRows = []
    for m in meetings:
        minutesRows.append(earlyUtcMinutesRows[m][2])
    return minutesRows

def findMinutesRowsInYearRows(year, table:list):
    if year in (earlyMinutes.keys()):
        return getMinutesRowsForEarlyYear()
    minutes_rows = [
        row for row in table
        if re.search('minute', row[2].lower()) is not None
        and re.search('(utc|uct)', row[2].lower()) is not None
        and re.search('#[0-9]{2,3}', row[2]) is not None
        and row[1][-3:] != 'pdf'
        and row[1][-9:] != 'NOTPOSTED'
        ]
    return minutes_rows


def findMinutesRowForMeeting(meetingNumber):
    tables = utcDocRegTables
    for y, t in tables.items():
        # looking at doc registry for year y, check for meetingNumber
        if (meetingNumber in earlyUtcMinutesRows.keys()):
            r = earlyUtcMinutesRows(meetingNumber)
            return (r[0], r[1], r)
        else:
            minutes_rows = findMinutesRowsInYearRows(y, t)
        for i in range(len(minutes_rows)):
            r = minutes_rows[i]
            m = re.search('(UTC ?[a-zA-Z ]*#?)([0-9]*)', r[2])
            if m.group(2) != '' and meetingNumber == int(m.group(2)):
                return (y, i + 1, r)
            else:
                continue


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


def fetchMinutesForMeetingRange(firstMeeting=1, lastMeeting=999):
    ### Fetches meeting minutes for a range or meetings. Returns
    ### a dict with structure {mtg#: [year, qtr, doc #, title, page content] }.
    ###
    ### If not specified, firstMeeting will be the first meeting from the
    ### first supported year; and lastMeeting will be the last meeting with
    ### posted minutes in the last supported year.

    firstMeeting = max(firstMeeting, min(list(utc_minutes.keys())))
    lastMeeting = min(lastMeeting, max(list(utc_minutes.keys())))

    print("Fetching minutes for meetings", firstMeeting, "to", lastMeeting)

    # Docs will be fetched from the server; pickled docs are not used.

    allMtgMinutes = {}
    for i in range(firstMeeting, lastMeeting + 1):
        allMtgMinutes[i] = fetchMeetingMinutes(i)
    return allMtgMinutes


def refreshUtcMinutes():
    utc_minutes = getAllMeetingMinutes()


def getAllMeetingMinutes(forceRefresh = False):
    ### Returns a dict with data for all UTC meeting minutes in the supported range.
    ### The dict structure is {mtg#: [year, qtr, doc #, title, page content]}.
    ### Uses pickled data if present; if not, it will pickle the results.

    pickle_file = Path(utcMinutesPages_pickleFile)
    if pickle_file.is_file() and not forceRefresh:
        with open(utcMinutesPages_pickleFile, 'rb') as file:
            allMtgMinutes = pickle.load(file)
    else:
        allMtgMinutes = {}
        tables = utcDocRegTables
        for y, t in tables.items():
            # looking at doc registry for one year (y)
            year_reg_url = utcDocRegistry_urls[y]
            base_url = year_reg_url[:year_reg_url.rindex("/") + 1]
            # get the doc registry rows for UTC minutes -- minutes_rows is a list of lists
            if (y in earlyMinutes.keys()):
                minutes_rows = getMinutesRowsForEarlyYear(y)
            else:
                minutes_rows = findMinutesRowsInYearRows(y, t)
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


def updatePickledMeetingMinutesForMeetingList(meetingList):
    for i in meetingList:
        updatePickledMeetingMinutes(i)

def updatePickledMeetingMinutes(meetingNumber):
    updatePickledMeetingMinutesForMeetingRange(meetingNumber, meetingNumber)

def updatePickledMeetingMinutesForMeetingRange(firstMeeting = 1, lastMeeting = 999):
    ### Opens an existing utcMinutesPages_pickleFile, fetches the pages for
    ### specified meetings and replaces the content for those meetings, then
    ### saves the updated pickle file. Also updates utc_minutes.
    ### 
    ### If utcMinutesPages_pickleFile doesn't exist, calls getAllMeetingMinutes.
    ###
    ### If not specified, firstMeeting will be the first meeting from the
    ### first supported year; and lastMeeting will be the last meeting with
    ### posted minutes in the last supported year.

    pickle_file = Path(utcMinutesPages_pickleFile)
    if pickle_file.is_file():
        with open(utcMinutesPages_pickleFile, 'rb') as file:
            allMtgMinutes = pickle.load(file)
    else:
        print("Pickle file for meeting minutes not found; fetching all meeting minutes...")
        getAllMeetingMinutes()
        return
    
    # Limit range to known meetings
    firstKnown, lastKnown = getFirstAndLastKnownUtcMeetings()
    if firstMeeting < firstKnown:
        firstKnown = firstKnown
    if lastMeeting > lastKnown:
        lastMeeting = lastKnown

    # Fetch the file and update data
    for i in range(firstMeeting, lastMeeting + 1):
        allMtgMinutes[i] = fetchMeetingMinutes(i)

    with open(pickle_file, 'wb') as file:
        print("Saving updated pickle file")
        pickle.dump(allMtgMinutes, file, protocol=pickle.HIGHEST_PROTOCOL)

    # Since this has been updated, update utc_minutes
    global utc_minutes
    utc_minutes = allMtgMinutes



def fetchMeetingMinutes(meetingNumber):
    ### Returns the doc content & details for minutes of a given UTC meeting.
    ### If minutes are not found, returns None.

    if meetingNumber in earlyUtcMinutesRows.keys():
        (year, sequenceInYear, minutesRow) = earlyUtcMinutesRows[meetingNumber]
    else:
        (year, sequenceInYear, minutesRow) = findMinutesRowForMeeting(meetingNumber)
    if minutesRow is None: return

    year_reg_url = utcDocRegistry_urls[year]
    base_url = year_reg_url[:year_reg_url.rindex("/") + 1]
    minutesURL = base_url + minutesRow[1]
    print(f"retrieving UTC meeting {meetingNumber} minutes doc")
    page = requests.get(minutesURL).text
    soup = BeautifulSoup(page, 'lxml')
    title = soup.title.text
    m = re.search('(UTC ?#?)([0-9]*)', title)
    assert m is not None
    mtg_num = int(m.group(2))
    return [year, sequenceInYear, str(minutesRow[0]), str(title), page]


def updateAllMeetingMinutesWithLatest():
    pickle_file = Path(utcMinutesPages_pickleFile)
    if not pickle_file.is_file():
        allMtgMinutes = getAllMeetingMinutes()
    else:
        # get pickled minutes info
        with open(utcMinutesPages_pickleFile, 'rb') as file:
            allMtgMinutes = pickle.load(file)
        # get details on last stored meeting
        allStoredMeetings = list(allMtgMinutes)
        lastStoredMeetingNumber = allStoredMeetings[-1]
        lastStoredMeetingYear = allMtgMinutes[lastStoredMeetingNumber][0]
        # compare to known
        lastKnownYear = list(utcDocRegistry_urls)[-1]
        yearsToCheck = list(range(lastStoredMeetingYear, lastKnownYear + 1))

        docRegTables = utcDocRegTables
        for y in yearsToCheck:
            # looking at doc registry for one year (y)
            year_reg_url = utcDocRegistry_urls[y]
            base_url = year_reg_url[:year_reg_url.rindex("/") + 1]
            # get the doc registry rows for UTC minutes
            yearTable = docRegTables[y]
            minutes_rows = findMinutesRowsInYearRows(y, yearTable)

            for i in range(len(minutes_rows)):
                mtg_num = getMeetingNumberFromMinutesRow(minutes_rows[i])
                if mtg_num > lastStoredMeetingNumber:
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

        The approach taken here is to search for strings ("Action Item", etc.)
        and then look for a parent element. The list of parent element types
        is determined by what has historically been used in minutes pages.
    '''
    pageContent = doc[-1]
    soup = BeautifulSoup(pageContent, 'lxml')

    # define the re patterns for the action types
    patterns = {
        "AI": "A(C|c)(T|t)(I|i)(O|o)(N|n) (I|i)(T|t)(E|e)(M|m)",
        "consensus": "C(O|o)(N|n)(S|s)(E|e)(N|n)(S|s)(U|u)(S|s)",
        "motion": "M(O|o)(T|t)(I|i)(O|o)(N|n)",
        "note": "N(O|o)(T|t)(E|e):"
        }
    pattern = patterns[actionType]
    actionStrings = soup.find_all(string = re.compile(pattern))
    actions = [
        # Different minutes docs are structured differently (and some, badly)
        re.sub('\s+', ' ', s.find_parent(["blockquote", "dd", "div", "p", "ul"]).text)
        for s in actionStrings
        if not isinstance(s, Comment)
        ]
    return actions


def getAnchorParentText(a):
    try:
        p = re.sub('\s+',' ', a.find_parent(["blockquote", "dd", "div", "p", "ul"]).text)
    except:
        print(f"exception: {a.text}")
        p = None
    return p


def validateActionType(actionType, acceptNone = True):
    if actionType is None and acceptNone:
        return True
    elif actionType is None:
        return False
    elif actionType not in ["ai", "consensus", "decision", "lballot", "motion", "note", "all"]:
        print("The actionType parameter must be 'ai', 'consensus', 'decision', 'lballot', 'motion', or 'note'.")
        return False
    else:
        return True


def findTaggedActionsInMinutes(doc:list, actionType = "all"):
    ''' Gets a list of actions (all types) from a minutes doc. This assumes a
        convention applied since UTC #90 that a "tagging" tool is run on the
        minutes file turning the ID prefix for each action (e.g., "[123-C45]")
        into an anchor element.

        (More precisely, the anchor is applied to the string within square brackets.)

        Takes a row from a minutes entry and returns a list of action strings.
    '''
    patterns = {
        "ai": '[0-9]{0,3}-AI?[0-9a-z]{1,4}',
        "consensus": '[0-9]{0,3}-C[0-9a-z]{1,4}',
        "decision": '[0-9]{0,3}-(C|L|M)[0-9a-z]{1,4}',
        "motion": '[0-9]{0,3}-M[0-9a-z]{1,4}',
        "note": '[0-9]{0,3}-N[0-9a-z]{1,4}',
        "lballot": '[0-9]{0,3}-L[0-9a-z]{1,4}',
        "all": '[0-9]{0,3}-(AI?|C|L|M|N)[0-9a-z]{1,4}'
    }
    postAnchorPattern = re.compile("^[a-z]?\s*]")

    if not validateActionType(actionType):
        return

    pageContent = doc[-1]
    soup = BeautifulSoup(pageContent, 'lxml')
    # define the pattern for the action ID contained in the anchor element
    pattern = patterns[actionType]
    actionAnchorElements = soup.find_all("a", string=re.compile(pattern))
    actions = [
        # a.find_parent(["blockquote", "div", "p", "ul"]).text
        # getAnchorParentText(a)
        re.sub('\s+',' ', a.find_parent(["blockquote", "dd", "div", "p", "ul"]).text).strip()
        for a in actionAnchorElements
        if isinstance(a.next_sibling, NavigableString) and postAnchorPattern.match(a.next_sibling) is not None
            and isinstance(a.previous_sibling, NavigableString) and a.previous_sibling.strip() == '[' #some cases have whitespace
        ]
    return actions



def compileActionsFromAllMinutes(actionType):
    ''' Compiles all actions of a given type from all UTC meetings.

        Takes an action type string: "AI", "consensus", "motion" or "note".

        Returns a dictionary with entries of the form mtgNum: [actions list].
        For example compilesActionsFromAllMinutes("AI")[179] would return the
        list of all action items from meeting 179.
    '''

    if not validateActionType(actionType, acceptNone=False):
        return

    allActions = {}
    meetings = utc_minutes
    for mtgNum, mtg in meetings.items():
        print(f"getting actions for meeting {mtgNum}")
        actions = findActionsInMinutes(mtg, actionType)
        if len(actions) > 0:
            allActions[mtgNum] = actions
    return allActions


def compileTaggedActionsFromAllMinutes(actionType = "all", minutesData = None):
    ### Compiles all actions of all types from all UTC meetings for which
    ### the minutes have had the "tag" tool applied (started with UTC #90).
    ###
    ### The optional minutesData parameter can be used to pass in custom
    ### minutes data (e.g., for a limited range of meetings). Otherwise,
    ### minutes for all supported meetings will be used, using pickled data
    ### if present.


    if not validateActionType(actionType):
        return

    if minutesData is None:
        allMinutes = utc_minutes
    else:
        allMinutes = minutesData

    allActions = {}
    for mtgNum, mtg in allMinutes.items():
        if mtgNum >= 90:
            print(f"getting actions for meeting {mtgNum}")
            actions = findTaggedActionsInMinutes(mtg, actionType)
            if len(actions) > 0 :
                allActions[mtgNum] = actions
    return allActions


def writeToFileTaggedActionsFromAllMinutes(filename: str, actionType = "all", minutesData = None):

    if not validateActionType(actionType):
        return

    allActions = compileTaggedActionsFromAllMinutes(actionType, minutesData)
    f = open(filename, "w", encoding="utf-8")
    for mtgNum, actions in allActions.items():
        f.write(str(mtgNum) + "\n")
        for a in actions:
            f.write(a + "\n")
    f.close()


def findUtcAction(actionID):
    pattern = re.compile('([0-9]{1,3})-((?i:AI?|C|M|M|N))[0-9]{1,3}[a-z]?')
    m = re.match(pattern, actionID)
    if m is None:
        print(f'{actionID} is not a valid action ID')
    else:
        mtgNum = int(m.group(1))
        actionType = m.group(2).upper()
        actionTypeKeys = {"A": "ai", "C": "consensus", "L": "lballot", "M": "motion", "N": "note"}
        actionTypeKey = actionTypeKeys[actionType]
        actions = findTaggedActionsInMinutes(utc_minutes[mtgNum], actionTypeKey)
        for a in actions:
            if a[0:len(actionID)+2] == "[" + actionID + "]":
                return a
        print(f'Action {actionID} not found in UTC #{mtgNum} minutes')


def searchForTextInAllMinutes(text, ignoreCase = True):
    # return a dict {mtgNum: [results]}
    results = {}
    count = 0
    for mtgNum in list(utc_minutes):
        result = searchForTextInMinutes(text, mtgNum, ignoreCase, True, False)
        if result is not None:
            count += len(result)
            results[mtgNum] = result
    if count == 0:
        print("No matches found")
    elif count == 1:
        print("1 match found")
    else:
        print(f'{count} matches found')
    return results

def searchForTextInMinutes(text, meetingNumber, ignoreCase = True, reportMatch = True, reportNoMatch = True):
    ### Searches in the minutes for the specified meeting number, and
    ### returns a list of results. 
    ### 
    ### Each result is the text content of the parent element from a match,
    ### with extra whitespace removed.
    
    # check that meetingNumber is in range of known meetings
    firstKnown, lastKnown = getFirstAndLastKnownUtcMeetings()
    if meetingNumber not in range(firstKnown, lastKnown + 1):
        print("Meeting number ", meetingNumber, " is not a known UTC meeting.")
        return
    
    minutes = utc_minutes[meetingNumber]
    soup = BeautifulSoup(minutes[-1],'lxml')
    if ignoreCase:
        matches = soup.find_all(string=re.compile(text, re.IGNORECASE))
    else:
        matches = soup.find_all(string=re.compile(text))
    if len(matches) == 0:
        if reportNoMatch:
            print("No matches found")
        return
    else:
        if reportMatch:
            if len(matches) == 1:
                print(f'1 match found in UTC #"{meetingNumber}')
            else:
                print(f'{len(matches)} matches found in UTC #{meetingNumber}')
        results = [
            re.sub('\s+', ' ', s.parent.text)
            for s in matches
            if not isinstance(s, Comment)
        ]
        return results


def writeToFileSearchForTextInMinutesResults(filename: str, text: str, meetingNumber = None, ignoreCase = True):
    ### Writes search results to a file. If meetingNumber is None, searches all meetings.

    if meetingNumber is None:
        results = searchForTextInAllMinutes(text, ignoreCase)
    else:
        results = searchForTextInMinutes(text, meetingNumber, ignoreCase, reportMatch=False, reportNoMatch=False)
    if len(results) == 0:
        print("No results found")
    else:
        f = open(filename, "w", encoding="utf-8")
        for mtgNum, mtgResults in results.items():
            f.write(f'{str(mtgNum)}:\n')
            for i in range(len(mtgResults)):
                f.write(f'    {i+1}: {results[mtgNum][i]}\n')
        f.close()



# utcDocRegPages = getAllDocRegistryPages()
# utcDocRegPages = updateDocRegPagesToLatest()

utcDocRegTables = updateDocRegTablesWithLatest()
utc_minutes = updateAllMeetingMinutesWithLatest() #{mtg#: [year, qtr, doc #, title, page content]}

# write out text file with all "tagged" actions from all UTC minutes
# writeToFileTaggedActionsFromAllMinutes("UTC-actions.txt")

# write out text file with "tagged" decisions (motion, letter ballot, consensus) from all UTC minutes
# writeToFileTaggedActionsFromAllMinutes("UTC-decisions.txt", "decision")