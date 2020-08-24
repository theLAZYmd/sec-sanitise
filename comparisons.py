import re
from typing import List, Union
from regexes import regexes

# [//:] Starting and Ending
common_terms = [
	'income',
	'taxes',
	'balance',
	'expenses',
	'activities',
	'other',
	'interest'
]

# [//:] Levenshtein
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