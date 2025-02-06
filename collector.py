#!/usr/bin/env python3

##########################
#   Administrative Data  #
##########################
__title__       = "GovDataCollector"
__description__ = '''This module searches the Data.Gov API and mass-downloads all matching datasets.'''
__example__     = "https://docs.ckan.org/en/2.8/api/index.html"
__author__      = "Robert G. Jamison"
__copyright__   = "Copyright 2021"

__license__     = '''"MIT License" - Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions: The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.  THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.'''
__version__     = "1.0.1"
__status__      = "Production"

##########################
#        LIBRARIES       #
##########################

import requests
import json
import pandas
import xlsxwriter
import os
import sys
import getopt
from os.path import exists

##########################
#         CLASSES        #
##########################

class GovDataCollector:

    def __init__(self, search_term, max_records, path):
        self.width = os.get_terminal_size()[0]
        self.path = path
        self.data_path = path + "data/"
        # create directory if it does not exist
        if not exists(self.path):
            os.mkdir(self.path)
        if not exists(self.data_path):
            os.mkdir(self.data_path)
        # Set search criteria via query for url
        # URL = https://catalog.data.gov/api/3//action/package_search?q=salary&fq=groups:local&rows=200
        url  = "https://catalog.data.gov/api/3" # base URL for data.gov API
        url += "/action/package_search?"        # search within the packages
        url += "q=" + search_term               # search for term "salary"
        url += "&fq=groups:local"               # filter for "local-government"
        url += "&rows=" + str(max_records)      # show the first 200 results

        # Prevents us from looking like python
        header = {
            'User-Agent': 'Mozilla/5.0'
        }
        # Make the HTTP request.
        self.msg("Requesting the Data.Gov catalog")
        self.response = requests.get(url, headers=header)
        assert self.response.status_code == 200

        # Use the json module to load CKAN's response into a dictionary.
        self.response_dict = self.response.json()

        # Check the contents of the response.
        assert self.response_dict['success'] is True
        self.result = self.response_dict['result']['results']
        return

    def msg(self, message):
        print()
        print("=" * self.width)
        print(message)
        print("=" * self.width)
        print()
        return

    def save_response(self):
        # Save raw JSON index for catalog
        buffer = self.response.text
        filename = self.path + "Response.json"
        file = open(filename, 'w')
        file.write(buffer)
        file.close()
        self.msg("Catalog request was saved at " + filename)
        return

    def enumerate(self, format, download):

        self.msg("Enumerating catalog details")

        if format == "csv":
            self.mimetype = "text/csv"
            self.format = ".csv"
        elif format == "json":
            self.mimetype = "application/json"
            self.format = ".json"

        # Enumerate packages
        self.publishers = []
        self.organizations = []
        self.maintainers = []
        self.maint_emails = []
        self.file_url = []
        self.create_date = []
        self.modify_date = []

        for record in self.result:
            if record['maintainer']:
                self.maintainers.append(record['maintainer'])
            else: self.maintainers.append("NULL")
            if record['maintainer_email']:
                self.maint_emails.append(record['maintainer_email'])
            else: self.maint_emails.append("NULL")
            extras = record['extras']
            placeholder = "NULL"
            create = "NULL"
            modify = "NULL"
            if extras:
                for i in extras:
                    key = i['key']
                    value = i['value']
                    if key == 'publisher':
                        placeholder = value
                    if key == 'issued':
                        create = value
                    if key == 'modified':
                        modify = value
            self.publishers.append(placeholder)
            self.create_date.append(create)
            self.modify_date.append(modify)
            resources = record['resources']
            placeholder = "NULL"
            if resources:
                for j in resources:
                    if j['mimetype'] == self.mimetype:
                        placeholder = j['url']
                        break
                    else: continue
            self.file_url.append(placeholder)
            org = record['organization']['name']
            placeholder = "NULL"
            if org:
                placeholder = org
            self.organizations.append(placeholder)

        # Save publisher data to index file
        self.index_filename = self.path + "Index.xlsx"

        self.index_writer = pandas.ExcelWriter(self.index_filename, engine = 'xlsxwriter')

        self.tbl_publishers = pandas.DataFrame({
            'Publisher':self.publishers,
            'Organization':self.organizations,
            'Maintainer':self.maintainers,
            'Maintainer E-Mail':self.maint_emails,
            'URL':self.file_url,
            'Create Date':self.create_date,
            'Modify Date':self.modify_date
            })
        self.tbl_publishers.index.rename('Key', inplace=True)
        self.tbl_publishers.to_excel(self.index_writer, sheet_name = 'Publishers')
        if download == False:
            self.index_writer.save()
        return

    def download(self, index=None):
        self.msg("Starting downloads.  Good luck and Godspeed...")

        if index == None:
            # Download ALL files
            for i in range(0,len(self.file_url)):
                if self.file_url[i] != "NULL":
                    url = self.file_url[i]
                    filename = self.data_path + str(i) + self.format
                    print("+ Downloading " + str(i+1) + " of " + str(len(self.file_url)) + " from " + url)
                    file = requests.get(url)
                    print("  - Saving as " + filename)
                    open(filename, 'wb').write(file.content)
                else:
                    print("+ Skipping " + str(i+1) + " of " + str(len(file_url)))
        else:
            # Download just the file we need
            url = self.file_url[index]
            filename = self.data_path + str(index) + self.format
            print("+ Downloading " + str(index) + " from " + url)
            file = requests.get(url)
            print("  - Saving as " + filename)
            open(filename, 'wb').write(file.content)

        self.msg("Finished downloading.  You made it!!!")
        return

    def search_headers(self, search_criteria, index=None):
        self.msg("Searching for headers with the words " + str(search_criteria))

        if index == None:
            # Enumerate Headers to identify vulnerable files
            self.files_list  = []
            self.orgs_list   = []
            self.headers_list = []

            for i in range(0, len(self.organizations)):
                filename = self.data_path + str(i) + self.format
                if exists(filename):
                    with open(filename) as file:
                        headers = file.readline()
                        for term in search_criteria:
                            if term in headers.lower():
                                self.files_list.append(str(i) + self.format)
                                self.orgs_list.append(self.organizations[i])
                                self.headers_list.append(headers)
                                break
            self.tbl_headers = pandas.DataFrame({
                'Filename':self.files_list,
                'Organization':self.orgs_list,
                'Headers':self.headers_list,
                })
            self.tbl_headers.to_excel(self.index_writer, sheet_name = 'Matched_Headers', index=False)
            self.index_writer.save()
            return self.tbl_headers
        else:
            filename = self.data_path + str(index) + self.format
            if exists(filename):
                with open(filename) as file:
                    headers = file.readline().lower()
                    return headers

    def filter_headers(self, search_criteria, filter_criteria, index=None):
        self.msg("Extracting columns with these words: \n" + str(filter_criteria))
        def filter_headers_loop(i):
            old_file = self.data_path + str(i) + self.format
            new_file = self.data_path + str(i) + "_filtered" + self.format
            try:
                print("+ Searching '" + old_file + "'")
                df = pandas.read_csv(old_file, low_memory=False)
                has_names = False
                tbl_filtered = pandas.DataFrame()
                for column_name in df:
                    for word in search_criteria:
                        if word in column_name.lower():
                            has_names = True
                    for word in filter_criteria:
                        if word in column_name.lower():
                            tbl_filtered[column_name] = df[[column_name]].copy()
                            break
                if has_names == True:
                    print("  - Found data in '" + old_file + "'")
                    tbl_filtered.insert(0, "org_index", self.organizations[i])
                    tbl_filtered.to_csv(new_file, index=False)
                    print("  - Saving data at '" + new_file + "'")
                else:
                    print("  - No names found.")
            except FileNotFoundError:
                print("  - File '" + old_file + "' does not exist.")
        if index == None:
            # Generate smaller CSVs with just the data we need
            for i in range(0,len(self.organizations)):
                filter_headers_loop(i)
            self.msg("New files saved in the folder " + self.data_path)
            return
        else:
            filter_headers_loop(index)
            self.msg("New files saved in the folder " + self.data_path)
            return

##########################
#          MAIN          #
##########################

def main(argv):
    path = ""
    search_term = "salary"
    max_records = 5
    format = "csv"
    search_criteria = {"name"}
    download = False
    # customize as needed based on the columns you want to grab
    filter_criteria = {
        "name",
        "job",
        "title",
        "position"
        "agency",
        "dep"
    }

    help = """
    █▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀█
    █   ▄▄█▀▀▀█▄█                    ▀███▀▀▀██▄           ██            █
    █ ▄██▀     ▀█                      ██    ▀██▄         ██            █
    █ ██▀       ▀  ▄██▀██▄▀██▀   ▀██▀  ██     ▀██▄█▀██▄ ██████ ▄█▀██▄   █
    █ ██          ██▀   ▀██ ██   ▄█    ██      ███   ██   ██  ██   ██   █
    █ ██▄    ▀██████     ██  ██ ▄█     ██     ▄██▄█████   ██   ▄█████   █
    █ ▀██▄     ██ ██▄   ▄██   ███      ██    ▄██▀█   ██   ██  ██   ██   █
    █   ▀▀███████  ▀█████▀     █     ▄████████▀ ▀████▀██▄ ▀████████▀██▄ █
    █▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄█
    ███████ ▄▄▀██ ▄▄▄ ██ █████ █████ ▄▄▄██ ▄▄▀█▄▄ ▄▄██ ▄▄▄ ██ ▄▄▀████████
    ███████ █████ ███ ██ █████ █████ ▄▄▄██ ██████ ████ ███ ██ ▀▀▄████████
    ███████ ▀▀▄██ ▀▀▀ ██ ▀▀ ██ ▀▀ ██ ▀▀▀██ ▀▀▄███ ████ ▀▀▀ ██ ██ ████████
    ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
    \n""" + "Usage:  " + sys.argv[0] + " -p <path> -f <file_format> -r <max_records>\nAdd -d to download and analyze files"
    try:
        opts, args = getopt.getopt(argv,"hdp:f:r:")
    except getopt.GetoptError:
        print(help)
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print(help)
            sys.exit()
        elif opt == '-d':
            download = True
        elif opt in ("-p"):
            path = arg
            if path[-1:] != "/":
                path = path + "/"
        elif opt in ("-f"):
            format = arg
        elif opt in ("-r"):
            max_records = int(arg)
    print()
    print("#" * os.get_terminal_size()[0])
    print("Save directory is", path)
    print("Data will be stored at", path + "data/")
    print("Files will be saved as", format)
    print("Max records to download are", str(max_records))
    print("#" * os.get_terminal_size()[0])
    print()

    # test for GovDataCollector
    test = GovDataCollector(search_term, max_records, path)
    test.save_response()
    test.enumerate(format, download)
    if download == True:
        test.download() # this downloads ALL files
        test.search_headers(search_criteria)
        test.filter_headers(search_criteria, filter_criteria)

if __name__ == "__main__":
   main(sys.argv[1:])
