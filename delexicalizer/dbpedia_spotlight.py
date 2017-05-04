__author__ = 'thiagocastroferreira'

"""
Author: Thiago Castro Ferreira
Date: 04/05/2017
Description:
    This script aims to wikify all texts from WebNLG, using DBpedia spotlight
"""

import json
import urllib
import urllib2

url = 'http://model.dbpedia-spotlight.org/en/annotate'
values = {'text' : ('Adolfo Suárez Madrid-Barajas Airport has an elevation of 610.0 metres above sea level.').encode('utf-8'),
          'confidence' : 0.2,
          'support' : 20 }

headers = { 'Accept': 'application/json' }

data = urllib.urlencode(values)
req = urllib2.Request(url, data, headers)
response = urllib2.urlopen(req)
# result = json.loads(response.read())

# print result['Resources']

result = response.read()
print result