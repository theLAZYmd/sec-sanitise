import os
from pathlib import Path
import traceback
import csv
import json

import pandas as pd
import re

# pylint: disable=no-member,no-name-in-module
from Levenshtein import distance
from regexes import regexes
from prototype import validate_dates
from comparisons import is_antonym, common_terms

sec_codes = ['10K', '10Q']
sec_types = [
	'balance sheets',
	'statements of cash flows',
	'statements of operations and comprehensive income (loss)',
	'statements of stockholder\'s (deficit) equity'
]

def sanitise(key):
	key = key.lower().strip()
	key = re.sub(regexes['brackets'], '', key)
	key = re.sub(regexes['spaces'], ' ', key)
	key = re.sub(regexes['date_spec'], '', key)
	key = re.split(regexes['currency_spec'], key)[0]
	key = key.replace(', shares', '')
	key = key.replace('\u00e2\u20ac\u201c', '-')
	if ':' in key:
		key = key.split(':')[0]
	if key.endswith('respectively'):
		key = key.split(',')[0]		
	if key.endswith('par value'):
		key = key.split(',')[0:-1].join(',')
	if re.search(regexes['year'], key):
		key = key.split(',')[0]
	if re.search(regexes['loss'], key):
		key = key.replace('loss', 'income')
	return key.strip()

def generate(sourceDir, extension='.csv'):

	output = {}
	missed_codes = []
	missed_types = []

	folders = os.listdir(sourceDir)
	for z, folder in enumerate(folders):
		output['status'] = {
			'iteration': z
		}
		
		if '.' in folder:
			continue
		files = os.listdir('\\'.join([sourceDir, folder]))
		for f in files:
			if not folder.endswith(extension):
				continue
			try:
				[code, _datestring, sec_type] = f.split('_')
				sec_type = sec_type.replace('Consolidated ', '').lower()
				name = '{}_{}'.format(code, sec_type)
				if code not in sec_codes and code not in missed_codes:
					missed_codes.append(code)
				if sec_type not in sec_types and name not in missed_types:
					missed_types.append(sec_type)

				csvfile = open('\\'.join([sourceDir, folder, f]))
				data = csv.reader(csvfile)
				dates = None
				body = []
				for row in data:
					if not dates and validate_dates(row):
						dates = row
					else:
						body.append(row)

				if not name in output:
					output[name] = {}				
				pre_mutation = output[name].copy()
				
				overHang = ''
				for row in body:
					key = sanitise(row[0])
					if key == 'category':
						continue
					if overHang and len(list(filter(None, [(row[0] == key) for row in body]))) >= 2:
						key = overHang
						overHang = ''
					if all([not x for x in row[1:]]):
						overHang = key
						continue

					if re.search(regexes['year'][0:-1], key):
						if not '_other' in output[name]:
							output[name]['_other'] = []
						output[name]['_other'].append(key)
						continue
					if len(pre_mutation):
						if not key in output[name]:
							starts = []
							ends = []
							levs = {}
							for k in list(output[name].keys()):
								if k.startswith('_') or not k or 'other' in k:
									continue
								if key.startswith(k) or k.startswith(key) and not k in common_terms and not key in common_terms:
									starts.append(k)
								elif key.endswith(k) or k.endswith(key) and not k in common_terms and not key in common_terms:
									ends.append(k)
								else:
									if not is_antonym(k, key):
										chars = distance(k, key)
										percent = chars / len(key)
										if chars < 3 or percent < 0.2:
											levs[k] = '{}-{:.0%}'.format(chars, percent)
											if not 'aliases' in output[name][k]:
												output[name][k]['aliases'] = []
											output[name][k]['aliases'].append(key)
							obj = {}
							if len(starts):
								obj['starts'] = starts
							if len(ends):
								obj['ends'] = ends
							if len(levs):
								obj['levs'] = levs
							output[name][key] = obj
						else:						
							pass
					else:
						output[name][key] = {}
			except:
				traceback.print_exc()
		print('Completed: {}/{} companies.'.format(z + 1, len(folders)))
		if z > 5:
			break

		with open('./aliases.json', 'w', encoding='utf-8') as writeFile:
			output['status'].update({
				'codes': missed_codes,
				'types': missed_types
			})
			writeFile.write(json.dumps(output, indent=4))

isTest = False
sourceDir = 'U:\\Day Files\\Rodman, Ben\\EAS\\Quant\\CompanyData\\'
if isTest:
	sourceDir = './Samples'

generate(
	sourceDir=sourceDir,
	extension=''
)