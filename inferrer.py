#!/usr/bin/env python3

##########################
#   ADMINISTRATIVE DATA  #
##########################
__title__       = "GovDataInference"
__description__ = '''This module ingests datasets from Data.Gov and infers sensitive data fields.'''
__example__     = "First Name, Last Name, and Domain = rjamison6@gatech.edu"
__author__      = "Robert G. Jamison"
__copyright__   = "Copyright 2021"

__license__     = '''"MIT License" - Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions: The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.  THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.'''
__version__     = "1.0.1"
__status__      = "Production"

############################
#        LIBRARIES         #
############################

import pandas
import os
import sys
import getopt
import string

############################
#          CLASSES         #
############################
class GovDataInferrer:
    # Initialize the pandas dataframe and quantile values
    def __init__(self, input_csv, domain_csv, domain):
        # import the list of salary data
        self.input = pandas.read_csv(input_csv)

        # import MX Domains list
        if domain_csv != "":
            self.domains = pandas.read_csv(domain_csv)
            self.domains.columns = ['Org','Domain']
        else:
            self.domain = domain

        self.output = pandas.DataFrame()
        return

    def show_headings(self, df):
        print("[#] : Dataframe Headings")
        print("------------------------------")
        # iterate through column headers
        for i in range(0, len(df.columns.values)):
            # print as "[0]: <header>"
            print('[' + str(i) + '] : ' + df.columns.values[i])
        print("------------------------------")

    # clean up the input table
    def clean_input(self, df):
        print("##################################")
        print("Please wait.  Building new table.")
        print("##################################")
        # initialize variables
        new_df = pandas.DataFrame()
        for i in range(0,len(df)):
            new_df = new_df.append({"Last_Name":[""], "First_Name":[""], "Middle_Name":[""]}, ignore_index=True)
        more = ""
        # initialize fields.
        last_name = "NULL"
        first_name = "NULL"
        middle_name = "NULL"
        # show the headings
        self.show_headings(df)
        # how many name fields?
        name_fields = int(input("How many columns are used for a person's full name? "))
        # if there is only one field for the names
        if name_fields == 1:
            # prompt the user
            col = int(input("Which [#] above contains the full names? "))
            for i in range(0, len(df)):
                full_name = df[df.columns.values[col]][i].split(" ")
                if len(full_name) < 2:
                    print("ERROR: Could not parse the name structure correctly.")
                    exit(2)
                elif "," in full_name[0]:
                    last_name = full_name[0].replace(',',"")
                    first_name = full_name[1].replace(',',"")
                    if len(full_name) == 3:
                        middle_name = full_name [2].replace(',',"")
                else:
                    first_name = full_name[0]
                    if len(full_name) == 3:
                        middle_name = full_name[1]
                        last_name = full_name[2]
                    else:
                        last_name = full_name[1]

                new_df["Last_Name"][i] = last_name
                new_df["First_Name"][i] = first_name
                new_df["Middle_Name"][i] = middle_name

        # if there are more than one field for the names
        else:
            # Save the last name column to the new dataframe
            col = int(input("Which [#] above contains the last names? "))
            for i in range(0,len(df)):
                last_name = df[df.columns.values[col]][i]
                last_name = last_name.translate(str.maketrans('', '', string.punctuation))
                new_df["Last_Name"][i] = last_name.split(" ")[0]
            # Save the first name column to the new dataframe
            col = int(input("Which [#] above contains the first names? "))
            for i in range(0,len(df)):
                first_name = df[df.columns.values[col]][i]
                first_name = first_name.translate(str.maketrans('', '', string.punctuation))
                first_name = first_name.split(" ")
                new_df["First_Name"][i] = first_name[0]

            # if there are only two fields for names
            if name_fields == 3:
                # Save the middle name column to the new dataframe
                col = int(input("Which [#] above contains the middle names / initials? "))
                for i in range(0,len(df)):
                    middle_name = df[df.columns.values[col]][i]
                    middle_name = middle_name.translate(str.maketrans('', '', string.punctuation))
                    new_df["Middle_Name"][i] = middle_name.split(" ")[0]

        # Save the org column to the new dataframe
        col = int(input("Which [#] above contains the organizations? "))
        new_df["Org"] = df[df.columns.values[col]]
        # Save the salary column to the new dataframe
        col = int(input("Which [#] above contains the wage totals? "))
        new_df["Salary"] = df[df.columns.values[col]]
        print()
        more = input("Do you have another field you want to keep? (y/n) ")
        # if there is more to add...
        while more == "y":
            # Save additional fields
            col = int(input("Which field do you want to keep? "))
            new_df[df.columns.values[col]] = df[df.columns.values[col]]
            # ask the user if they have more to add
            more = input("Do you have another field you want to keep? (y/n) ")

        print(new_df.head(10))
        print()
        correct = input("Does what we printed above look correct? (y/n) ")
        print()
        if correct == "n":
            self.clean_input(df)
        # return the new dataframe
        return new_df

    # Assign a value to the output dataframe
    def put_value(self, row, column, value):
        self.output.at[row, column] = value
        return

    def save_file(self, output_file):
        if "csv" in output_file[-3:].lower():
            self.output.to_csv(output_file)
        elif "json" in output_file[-4:].lower():
            self.output.to_json(output_file)
        else:
            print("Output filetype must be 'csv' or 'json'.")
            return
        print("##################################")
        print("Results saved at", output_file)
        print("##################################")
        print()
        return

    # PAY: ATTACK TYPE METHOD
    def infer_attack(self, salary):
        # Got poverty line from https://www.census.gov/data/tables/time-series/demo/income-poverty/historical-poverty-thresholds.html
        self.poverty_line = 13171
        # Calculate 90% quantile of Salaries
        self.wealth_line = self.output['Salary'].quantile(.9)
        # if worker salary is below poverty line:
        if salary <= self.poverty_line:
            # Append "Attrition" to Attack Type column
            return "Attrition"

        # if worker is a top 10% salary earner
        elif salary >= self.wealth_line:
            # Append "Whaling" to Attack Type columns
            return "Whaling"

        # else:
        else:
            # Append "Phishing" to Attack Type columns
            return "Phishing"

    # DOMAIN: Use the organization value to determine the domain to assign
    def infer_domain(self, org):
        if self.domain == "":
            # iterate through length of the dataframe
            for i in range(0,len(self.domains)):
                # if MX Domains List item contained in the org:
                if org in self.domains['Org'][i]:
                    # Append MX Domain List item to Domain
                    return self.domains['Domain'][i]
        else:
            return self.domain

    # NAME:  ACCOUNT METHOD
    def infer_usernames(self):
        self.username_format = 1
        # create examples
        username_examples = [
            "Albus.W.Dumbledore",
            "Albus.Dumbledore",
            "AlbusDumbledore",
            "A.Dumbledore",
            "ADumbledore",
            "ADumbledor",
            "ADumbledo",
            "ADumbled",
            "ADumble",
            ]
        # present format choices
        print("[#] : Albus Wulfric Dumbledore")
        print("------------------------------")
        # iterate through column headers
        for i in range(0, len(username_examples)):
            # print as "[0]: <header>"
            print('[' + str(i) + '] : ' + username_examples[i])
        print("------------------------------")
        # read username_format
        self.username_format = int(input("Which of the above formats would you like to try? "))

    def get_username(self, last, first, middle):
        if self.username_format == 0:
            # "Albus.W.Dumbledore"
            return (first + "." + middle[:1] + "." + last).lower()
        elif self.username_format == 1:
            # "Albus.Dumbledore"
            return (first + "." + last).lower()
        elif self.username_format == 2:
            # "AlbusDumbledore"
            return (first + last).lower()
        elif self.username_format == 3:
            # "A.Dumbledore"
            return (first[:1] + "." + last).lower()
        elif self.username_format == 4:
        # "ADumbledore"
            return (first[:1] + last).lower()
        elif self.username_format == 5:
        # "ADumbledor"
            return (first[:1] + last[:9]).lower()
        elif self.username_format == 6:
        # "ADumbledo"
            return (first[:1] + last[:8]).lower()
        elif self.username_format == 7:
        # "ADumbled"
            return (first[:1] + last[:7]).lower()
        elif self.username_format == 8:
        # "ADumble"
            return (first[:1] + last[:6]).lower()
        else:
            print("Error - Selected number is out of range")
            return "ERROR"

    # E-MAIL METHOD
    def infer_email(self, username, org):
        # run get_domain function
        domain = self.infer_domain(org)
        # Concatenate username with email domain
        email = str(username) + "@" + str(domain)
        # Append email to Email column
        return email

def main(argv):
    dataset_csv = ""
    domain_csv = ""
    domain = ""
    output_file = ""
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
    █████████████▄ ▄██ ▀██ ██ ▄▄▄██ ▄▄▄██ ▄▄▀██ ▄▄▀██ ▄▄▄██ ▄▄▀██████████
    ██████████████ ███ █ █ ██ ▄▄███ ▄▄▄██ ▀▀▄██ ▀▀▄██ ▄▄▄██ ▀▀▄██████████
    █████████████▀ ▀██ ██▄ ██ █████ ▀▀▀██ ██ ██ ██ ██ ▀▀▀██ ██ ██████████
    ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
    \n""" + sys.argv[0] + " -i <input_csv> -d <domain_csv or domain> -o <output_file>"
    try:
        opts, args = getopt.getopt(argv,"hi:d:o:")
    except getopt.GetoptError:
        print(help)
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print(help)
            sys.exit()
        elif opt in ("-i"):
            input_csv = arg
        elif opt in ("-d"):
            if arg[-4:] == ".csv":
                domain_csv = arg
            else:
                domain = arg
        elif opt in ("-o"):
            output_file = arg
    print()
    print("##################################")
    print("Input file is", input_csv)
    if domain_csv != "":
        print("Domain file is", domain_csv)
    else:
        print("Domain is", domain)
    print("Output file is", output_file)
    print("##################################")
    print()

    # test for domains
    test = GovDataInferrer(input_csv, domain_csv, domain)
    test.output = test.clean_input(test.input)
    test.infer_usernames()

    # test for salary data
    for i in range(0, len(test.output)):
        # get the last name
        last_name = test.output["Last_Name"][i]
        # get the first name
        first_name = test.output["First_Name"][i]
        # get the middle name
        middle_name = test.output["Middle_Name"][i]
        # get the organization
        org = test.output["Org"][i]
        # get their salary
        salary = test.output['Salary'][i]
        # get the account and add it to output
        username = test.get_username(last_name, first_name, middle_name)
        test.put_value(i, "Account", username)
        # get email address and add it to output
        email = test.infer_email(username, org)
        test.put_value(i, "Email", email)
        # get the attack type and add it to output
        attack = test.infer_attack(salary)
        test.put_value(i, "Attack_Type", attack)
    # show the top five rows of the new dataset
    print("RESULTS PREVIEW:")
    print()
    print(test.output.head(5))
    print()
    # save to csv file
    test.save_file(output_file)

if __name__ == "__main__":
   main(sys.argv[1:])
