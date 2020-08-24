import os
from pathlib import Path
import traceback
import csv
import json

import pandas as pd
import re

regexes = {
    'year': re.compile(r"(?:2\s?0|1\s?9)\s?[0-9]\s?[0-9]$"),
    'currency': re.compile(r"^[$£]$"),
	'brackets': re.compile(r"[\(\[].*?[\)\]]"),
	'spaces': re.compile(r"\s+")
}

def sanitise(key):
	key = re.sub(regexes['brackets'], '', key).lower().strip()
	key = re.sub(regexes['spaces'], ' ', key)
	return key

def validateKey(key, meta):
	key = sanitise(key)
	if meta['k'] == key:
		return True
	if 'startswith' in meta and key.startswith(meta['k']):
		return True
	if 'aliases' in meta:
		if key.lower() in meta['aliases']:
			return True
	if 'regex' in meta:
		if re.search(meta['regex'], key, re.IGNORECASE):
			return True
	return False

def validateDates(row):
	if all([re.match(regexes['year'], x) or not i for (i, x) in enumerate(row)]):
		return True
	if (
		row[0] == 'Category' and
		all([re.search(regexes['year'], x) or not i for (i, x) in enumerate(row)])
	):
		return True
	return False

def transformData(value):
	if not value:
		return None
	try:
		return int(value)
	except ValueError:
		try:
			return float(value)
		except:
			return value
	except:
		return value

def getSubstrings(sourceDir, extension='.csv'):

	d = open('{}\\{}'.format(os.getcwd(), 'config.json'), 'r', encoding='utf-8')
	config = json.load(d)

	aliases = { x: [] for (x, data) in config.items() }
	aliases.update({ '_other': [] })
	outputs = {}

	folders = os.listdir(sourceDir)
	for z, folder in enumerate(folders):
		if '.' in folder:
			continue
		files = os.listdir('\\'.join([sourceDir, folder]))
		for j, f in enumerate(files):
			if not folder.endswith(extension):
				continue
			try:
				csvfile = open('\\'.join([sourceDir, folder, f]))
				data = csv.reader(csvfile)
				dates = None
				body = []
				for row in data:
					if not dates and validateDates(row):
						dates = row
					else:
						body.append(row)
				if not dates:
					print('{}/{}'.format(folder, f))
					dates = []

				output = {}
				
				overHang = ''
				for row in body:

					for i in range(1, len(row)):
						key = row[0]
						if overHang and len(list(filter(None, [(row[0] == key) for row in body]))) >= 2:
							key = overHang
							overHang = ''
						if all([not x for x in row[1:]]):
							overHang = key
							continue
						
						located = False
						for k, meta in config.items():
							if k.startswith('_'):
								continue
							meta.update({ 'k': k })
							if not validateKey(key, meta):
								continue
							if not key in aliases[k]:
								aliases[k].append(key)
							
							if '(in shares)' in key.lower():
								key = '{} (in shares)'.format(k)
							else:
								key = k
							located = True
							break
						if not located and not key in aliases['_other']:
							aliases['_other'].append(key)
						date = dates[i] if i < len(dates) else str(i)
						if not date in output:
							output[date] = {}

						k = 0
						while key in output[date] and output[date][key] != transformData(row[i]):
							k += 1
							key = '{}_{}'.format(key, str(k))

						output[date][key] = transformData(row[i])

				if not folder in outputs:
					outputs[folder] = {}
				outputs[folder].update(output)
			except:
				traceback.print_exc()
			print('Completed: {}/{} companies. Converted: {}/{} files'.format(z + 1, len(folders), j + 1, len(files)))
		if z > 1:
			break

	with open('./aliases.json', 'w', encoding='utf-8') as writeFile:
		writeFile.write(json.dumps(aliases, indent=4))
	with open('./output.json', 'w', encoding='utf-8') as outputFile:
		outputFile.write(json.dumps(outputs, indent=4))

isTest = False
sourceDir = 'U:\\Day Files\\Rodman, Ben\\EAS\\Quant\\CompanyData\\'
if isTest:
	sourceDir = './Samples'

getSubstrings(
	sourceDir=sourceDir,
	extension=''
)