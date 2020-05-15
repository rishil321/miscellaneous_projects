#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Description of this module/script goes here
:param -f OR --first_parameter: The description of your first input parameter
:param -s OR --second_parameter: The description of your second input parameter 
:returns: Whatever your script returns when called
:raises Exception if any issues are encountered
"""

# Put all your imports here, one per line. However multiple imports from the same lib are allowed on a line.
# Python standard imports
import sys
import logging
import os
from datetime import datetime
from pathlib import Path

# Third party imports (from PyPi/The Cheese Shop)
import requests
import pandas as pd

# Local module imports (stored on the local machine)
from setuplogging import setuplogging
from scholarly.Scholarly import get_scholarly_instance

# Put your constants here. These should be named in CAPS.
KEYWORDS = ('Expi293', 'expiCHO')
GOOGLE_SCHOLAR_RESULTS_CSV_DIR_NAME = 'google_scholar_results'
LOWER_DATE_BOUNDARY_YEAR_FOR_RESULTS = '2017'

# Put your global variables here.

# Put your class definitions here. These should use the CapWords convention.

# Put your function definitions here. These should be lowercase, separated by underscores.


def scrape_google_scholar():
    """
    Uses the scholarly module to query Google Scholar for the keywords specified in KEYWORDS
    """
    # set up a list to store all of the articles/publications returned by the search
    processed_search_results = []
    for word in KEYWORDS:
        logging.debug("Now searching Google Scholar for keyword: "+word)
        # set up a dict to hold our results
        google_scholar_results = {}
        # use the API to perform the search
        scholarly = get_scholarly_instance(
            use_proxy=True, use_selenium=True, browser='chrome')
        search_bibs = []
        search_result = scholarly.search_pubs_query(word)
        # set an index value to limit our number of results
        index = 0
        while(index < 50):
            # get the next result, or set the result to 'end' if no result is found
            generated_result = next(search_result, 'end')
            if generated_result == 'end':
                break
            search_bibs.append(generated_result.bib)
            index += 1
        for bib in search_bibs:
            # in each raw result, create a dict to store the processed search output
            processed_search_result = {}
            # get the year of publication
            try:
                # set defaults for the year and title of this publication
                bib.setdefault('year', None)
                bib.setdefault('title', None)
                # check if a year was parsed
                if bib['year'] and bib['title']:
                    logging.debug("Year found for article " +
                                  bib['title']+". Proceeding.")
                    search_result_date = datetime.strptime(
                        bib['year'], '%Y')
                    if search_result_date >= datetime.strptime(LOWER_DATE_BOUNDARY_YEAR_FOR_RESULTS, '%Y'):
                        # continue with processing if the year of publication is higher than our lower boundary
                        logging.debug(
                            "Date for "+bib['title']+" is "+bib['year'] + ". Adding.")
                        # set the required parameters that we are interested in
                        required_result_keys = (
                            'title', 'url', 'author', 'eprint', 'year')
                        # get the parameters from the result object
                        for result_key in required_result_keys:
                            bib.setdefault(result_key, None)
                            processed_search_result[result_key] = bib[result_key]
                        # add the matching keyword that we used for the query
                        processed_search_result['keyword_matched'] = word
                        # add the dict to the larger list
                        processed_search_results.append(
                            processed_search_result)
                    else:
                        # else don't process this publication
                        logging.debug(
                            "Date for "+bib['title']+" is "+bib['year'] + ". Not adding.")
                else:
                    logging.error(
                        "Year and title for publication could not be parsed. Not continuing.")
            except ValueError:
                logging.error("Could not get date for " +
                              bib['title'] + ". Not adding.")
    # create a pandas dataframe from the list of search results to return
    dataframe = pd.DataFrame(processed_search_results)
    return(dataframe)


def write_dataframe_csv(dataframe, directory_path, filename_prefix):
    # create the dir if it does not exist already
    Path(directory_path).mkdir(parents=True, exist_ok=True)
    # try to create a csv file the dataframe sent in
    csv_filename = filename_prefix+"_" + \
        datetime.now().strftime("%Y-%m-%d-%H-%M-%S")+".csv"
    csv_full_path = os.path.join(directory_path, csv_filename)
    # check if this csv file already exists
    try:
        with open(csv_full_path, 'x') as csv_file:
            # if we don't throw an error, the file does not exist
            # so write the dataframe to this new file
            dataframe.to_csv(csv_file, index=False, header=True)
            logging.info("Successfully created file "+csv_filename)
    except OSError as exc:
        # error thrown if file exists
        # if this file already exists, we don't need to recreate as the reports are immutable
        logging.error("Could not create csv file " +
                      csv_filename+".")
        raise


def main():
    """Each function should have a docstring description as well"""
    setuplogging(logfilestandardname='scrape_pubmed_articles',
                 logginglevel='logging.DEBUG', stdoutenabled=True)
    # get the current directory of this script
    currentdir = os.path.dirname(os.path.realpath(__file__))
    # create the output directory to write csv files to
    output_csv_dir = os.path.join(
        currentdir, GOOGLE_SCHOLAR_RESULTS_CSV_DIR_NAME)
    # run the search for the KEYWORDS using google scholar
    result_dataframe = scrape_google_scholar()
    # create the output csv
    write_dataframe_csv(dataframe=result_dataframe, directory_path=output_csv_dir,
                        filename_prefix="google_scholar_results")
    # Use 0 for normal exits, 1 for general errors and 2 for syntax errors (eg. bad input parameters)
    sys.exit(0)


if __name__ == "__main__":
    main()
