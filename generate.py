import os
from pathlib import Path
import traceback
import csv
import json
import datetime

import pandas as pd
import re
# pylint: disable=no-member,no-name-in-module
from Levenshtein import distance
from typing import List, Union, Dict

from regexes import regexes
from prototype import sanitise, validate_dates, validate_key, transform_data
from comparisons import get_attribs, is_antonym, common_terms, valid_startswith, valid_endswith

# [//]: Settings

# Output a list of attributes to the aliases.json sheet produced.
# Deprecated since the factors used (polarity, magnitude etc) vary wildly on a per company basis.
use_attribs = False

# Fill the entire A column with company names in the output.csv
# If false, just outputs for the first one
fill_company_names = False

# Use to resume computation halfway
begin_from_iteration = 0

# For testing purposes
max_iterations = None

sourceDir = 'U:\\Day Files\\Rodman, Ben\\EAS\\Quant\\CompanyData\\'
sec_codes = ['10K', '10Q']
sec_types = [
	'balance sheets',
	'statements of cash flows',
	'statements of operations and comprehensive income (loss)',
	'statements of stockholder\'s (deficit) equity'
]

# [//]: Source

def generate(sourceDir: str, extension='.csv') -> None:
	now = datetime.datetime.now()

	aliases = {}
	try:
		f = open('./aliases.json')
		aliases = json.load(f)
		if not aliases:
			aliases = {}
	except:
		aliases = {}

	try:
		f = open('./output.json')
		outputs = json.loads(f)
	except:
		outputs = {}

	missed_codes = []
	missed_types = []

	folders = os.listdir(sourceDir)
	for z, folder in enumerate(folders):
		if z < begin_from_iteration:
			continue
		aliases['status'] = {
			'iteration': z
		}
		
		if '.' in folder:
			continue
		files = os.listdir(os.path.join(sourceDir, folder))
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

				csvfile = open(os.path.join(sourceDir, folder, f))
				data = csv.reader(csvfile)
				dates = []
				body = []

				output = {}
				for row in data:
					if not dates and validate_dates(row):
						dates = row
					else:
						body.append(row)

				if not name in aliases:
					aliases[name] = {}				
				pre_mutation = aliases[name].copy()
				
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
						if not '_other' in aliases[name]:
							aliases[name]['_other'] = []
						aliases[name]['_other'].append(key)
						continue
					if len(pre_mutation):
						if not key in aliases[name]:
							starts = {}
							ends = {}
							levs = {}
							obj = get_attribs(row[1:]) if use_attribs else {}
							for k in list(aliases[name].keys()):
								if k.startswith('_') or not k or 'other' in k:
									continue
								if valid_startswith(key, k):
									starts[k] = aliases[name][k]
								elif valid_endswith(key, k):
									ends[k] = aliases[name][k]
								else:
									if not is_antonym(k, key):
										chars = distance(k, key)
										percent = chars / len(key)
										if len(k) > 4 and len(key) > 4:
											if chars < 3 or percent < 0.2:
												levs[k] = '{}-{:.0%}'.format(chars, percent)
							aliases = {}
							if len(starts):
								aliases['starts'] = starts
							if len(ends):
								aliases['ends'] = ends
							if len(levs):
								aliases['levs'] = levs
							if len(aliases):
								for crit in aliases:
									for k in aliases[crit]:
										if not 'aliases' in aliases[name][k]:
											aliases[name][k]['aliases'] = []
										aliases[name][k]['aliases'].append(key)
							# obj.update(aliases)
							aliases[name][key] = obj
						else:						
							pass
					else:
						aliases[name][key] = get_attribs(row[1:]) if use_attribs else {}

					output.update(output_row(
						row=row,
						body=body,
						dates=dates,
						config=aliases[name],
						parsed=output
					))
				
				if not folder in outputs:
					outputs[folder] = {}
				outputs[folder].update(output)

			except:
				traceback.print_exc()

		if folder in outputs:
			write_to_csv(outputs[folder], folder)
		print('Completed: {}/{} companies.'.format(z + 1, len(folders)))
		if max_iterations and z >= max_iterations:
			break

		with open('./aliases.json', 'w', encoding='utf-8') as writeFile:
			aliases['status'].update({
				'codes': missed_codes,
				'types': missed_types
			})
			writeFile.write(json.dumps(aliases, indent=4))
		with open('./output.json', 'w', encoding='utf-8') as writeFile:
			writeFile.write(json.dumps(outputs, indent=4))
		

	entries = sum([sum([len(y) for y in x.values()]) for x in outputs.values()])
	elapsed = (datetime.datetime.now() - now).seconds
	print('Processed {} entries in {} seconds.'.format(entries, elapsed))

overHang = ''
def output_row(
	row: List[str],
	body: List[List[str]] = [],
	config: Dict[str, dict] = {},
	dates: List[str] = [],
	parsed = {}
):
	global overHang
	for i in range(1, len(row)):
		key = sanitise(row[0])
		if overHang and len(list(filter(None, [(row[0] == key) for row in body]))) >= 2:
			key = overHang
			overHang = ''
		if all([not x for x in row[1:]]):
			overHang = key
			continue
		
		for k, c in config.items():
			meta = c.copy()
			meta.update({ 'k': k })
			if not validate_key(key, meta):
				continue

			if '(in shares)' in row[0].lower():
				key = '{} (in shares)'.format(k)
			else:
				key = k
			break
		date = dates[i] if i < len(dates) else 'Stocks, {}'.format(str(i))
		if not date in parsed:
			parsed[date] = {}

		if key in parsed[date] and parsed[date][key] != transform_data(row[i]):
			k = 1
			while '{}_{}'.format(key, str(k)) in parsed[date] and parsed[date][key] != transform_data(row[i]):
				k += 1
			key = '{}_{}'.format(key, str(k))

		parsed[date][key] = transform_data(row[i])
	return parsed

try:
	old_file = open('./output.csv')
	old = csv.reader(old_file)
except:
	old = []

headers = ['Company Name', 'Date']
rows = []

if begin_from_iteration:
	headers = old[0]
	rows = old[1:]

def write_to_csv(output: Dict[str, Dict[str, float]], folder: str):
	global headers
	global rows
	has_printed_name = False

	for date, data in output.items():
		row = []
		if not has_printed_name or fill_company_names:
			row.append(folder)
			has_printed_name = True
		else:
			row.append(None)
		
		row.append(date)
		
		for key, value in data.items():
			if not key in headers:
				headers.append(key)
			index = headers.index(key)
			if len(row) <= index:
				row += [None for i in range(0, index - len(row) + 1)]
			row[index] = value
		
		rows.append(row)
	for row in rows:
		if len(row) < len(headers):
			row += [None for i in range(0, len(headers) - len(row))]
	df = pd.DataFrame(rows, columns=headers)
	df.to_csv('./output.csv', index=False)

isTest = True
if isTest:
	sourceDir = './Samples'

generate(
	sourceDir=sourceDir,
	extension=''
)
