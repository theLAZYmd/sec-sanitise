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

antonyms = [
	['beginning', 'end'],
	['derivative', 'warrant'],
	['financing', 'operating', 'investing'],
	['continuing', 'discontinued'],
	['net', 'gross'],
	['deficit', 'equity'],
	['assets', 'liabilities']
]

def is_antonym(a: str, b: str) -> bool:
	for pair in antonyms:
		res = [
			find_index(pair, a),
			find_index(pair, b)
		]
		if res[0] >= 0 and res[1] >= 0 and res[0] != res[1]:
			return True

	res = [
		re.search(regexes['negative'], a),
		re.search(regexes['negative'], b)
	]
	if len(list(filter(None, res))) == 1:
		return True

	return False

def find_index(substrings: List[str], s: str) -> int:
	for i, sub in enumerate(substrings):
		if sub in s:
			return i
	return -1