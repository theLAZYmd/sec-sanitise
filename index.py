import os
from pathlib import Path
import traceback
import csv
import json

import pandas as pd
import re
# pylint: disable=no-member,no-name-in-module
from Levenshtein import distance
from typing import List, Union

from regexes import regexes
from prototype import sanitise, validate_dates
from comparisons import get_attribs, is_antonym, common_terms, valid_startswith, valid_endswith

use_attribs = False
begin_from_iteration = 0
max_iterations = None
sourceDir = 'U:\\Day Files\\Rodman, Ben\\EAS\\Quant\\CompanyData\\'
sec_codes = ['10K', '10Q']
sec_types = [
	'balance sheets',
	'statements of cash flows',
	'statements of operations and comprehensive income (loss)',
	'statements of stockholder\'s (deficit) equity'
]

def generate(sourceDir: str, extension='.csv') -> None:

	d = open('{}\\{}'.format(os.getcwd(), 'aliases.json'), 'r', encoding='utf-8')
	aliases = json.load(d)
	
	other = {}
	outputs = {}

	folders = os.listdir(sourceDir)
	for z, folder in enumerate(folders):
		if z < begin_from_iteration:
			continue
		output['status'] = {
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
							starts = {}
							ends = {}
							levs = {}
							obj = get_attribs(row[1:]) if use_attribs else {}
							for k in list(output[name].keys()):
								if k.startswith('_') or not k or 'other' in k:
									continue
								if valid_startswith(key, k):
									starts[k] = output[name][k]
								elif valid_endswith(key, k):
									ends[k] = output[name][k]
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
										if not 'aliases' in output[name][k]:
											output[name][k]['aliases'] = []
										output[name][k]['aliases'].append(key)
							# obj.update(aliases)
							output[name][key] = obj
						else:						
							pass
					else:
						output[name][key] = get_attribs(row[1:]) if use_attribs else {}
			except:
				traceback.print_exc()
		print('Completed: {}/{} companies.'.format(z + 1, len(folders)))
		if max_iterations and z >= max_iterations:
			break

		with open('./output.json', 'w', encoding='utf-8') as writeFile:
			writeFile.write(json.dumps(output, indent=4))

isTest = True
if isTest:
	sourceDir = './Samples'

generate(
	sourceDir=sourceDir,
	extension=''
)