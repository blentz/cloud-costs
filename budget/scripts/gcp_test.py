#!/usr/bin/env python
''' Script to ingest GCP billing data into a DB '''

import logging
import os
import re
import sys

from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse as parse_date

from httplib2 import Http

import transaction

from apiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials

from sqlalchemy import engine_from_config
from sqlalchemy.sql import functions

from pyramid.paster import get_appsettings, setup_logging

from pyramid.scripts.common import parse_vars

from ..models import (DBSession,
                      GcpLineItem)

from ..util.fileloader import load_json, save_json

COMMIT_THRESHOLD = 10000
LOG = None

def usage(argv):
    ''' cli usage '''
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri> [rundate=YYYY-MM-DD]\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)

def run(settings, options):
    ''' do things '''

    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = settings['creds.dir'] + \
                                                    "/" + \
                                                    settings['creds.gcp.json']
    scopes = ['https://www.googleapis.com/auth/cloud-platform']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(settings['creds.dir'] + \
                                                    "/" + \
                                                    settings['creds.gcp.json'], scopes)

    http_auth = credentials.authorize(Http())

    # The apiclient.discovery.build() function returns an instance of an API service
    # object that can be used to make API calls. The object is constructed with
    # methods specific to the books API. The arguments provided are:
    #   name of the API ('cloudbilling')
    #   version of the API you are using ('v1')
    #   API key
    service = build('cloudbilling', 'v1', http=http_auth,
                    cache_discovery=False)
    request = service.billingAccounts().projects().list(name='billingAccounts/0085BB-6B96B9-89FD9F')
    response = request.execute()
    LOG.debug(response)

def main(argv):
    ''' main script entry point '''
    if len(argv) < 2:
        usage(argv)

    config_uri = argv[1]
    options = parse_vars(argv[2:])

    setup_logging(config_uri)
    global LOG
    LOG = logging.getLogger(__name__)

    settings = get_appsettings(config_uri, options=options)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)

    run(settings, options)

if '__main__' in __name__:
    try:
        main(sys.argv)
    except KeyboardInterrupt:
        print "Ctrl+C detected. Exiting..."
