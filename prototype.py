import re
from typing import List, Union
from regexes import regexes

def validate_dates(row: List[str]) -> bool:
	if all([re.match(regexes['year'], x) or not i for (i, x) in enumerate(row)]):
		return True
	if (
		row[0] == 'Category' and
		all([re.search(regexes['year'], x) or not i for (i, x) in enumerate(row)])
	):
		return True
	return False

def transform_data(value: str) -> Union[int, float, str]:
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

def sanitise(key: str) -> str:
	key = key.lower().strip()
	key = re.sub(regexes['brackets'], '', key)
	key = re.sub(regexes['spaces'], ' ', key)
	key = re.sub(regexes['date_spec'], '', key)
	key = re.split(regexes['currency_spec'], key)[0]
	key = key.replace(', shares', '')
	key = key.replace('\u00e2\u20ac\u201c', '-')
	key = key.replace('\u2019', '\'')
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