import re
import decimal
from typing import List, Union, Dict
from regexes import regexes
from categorise import get_accuracy, get_polarity, get_magnitude

endswith_precedent_threshold = 0.4

# [//:] Starting and Ending
common_terms = [
	'income',
	'taxes',
	'balance',
	'expenses',
	'activities',
	'other',
	'interest',
	'net',
	'depreciation',
	'amortisation',
	'less',
	'more',
	'total'
]

def get_attribs (values: List[str]) -> Dict[str, int]:
	return {
		'accuracy': get_accuracy(values),
		'polarity': get_polarity(values),
		'magnitude': get_magnitude(values)
	}

# [//:] Starting
start_qualifiers = [
	'attributable to',
	'of',
	'for',
	'before',
	'ratio',
	'per share',
	', shares'
]

def check_start_qualifiers(key: str, k: str) -> bool:
	follower = key[len(k):].strip()
	for q in start_qualifiers:
		if follower.startswith(q):
			return False
	args = re.split(regexes['spaces'], follower)
	if 'beginning' in args or 'end' in args:
		return False
	if follower.startswith('and'):
		if (len(follower[len('and'):].strip()) / len(key)) > endswith_precedent_threshold:
			return False
	return True

def valid_startswith(key: str, k: str) -> bool:
	if k in common_terms:
		return False
	if key in common_terms:
		return False
	if key.startswith(k):
		if check_start_qualifiers(key, k):
			return True
	if k.startswith(key):
		if check_start_qualifiers(k, key):
			return True
	return False

# [//:] Starting
end_qualifiers = [
	'accrued',
	'total'
]

def check_end_qualifiers(key: str, k: str) -> bool:
	precedent = key[:len(key) - len(k)].strip()
	for q in end_qualifiers:
		if precedent == q:
			return True
	for q in start_qualifiers:
		if q in precedent:
			return False
	if precedent.endswith('and'):
		if (len(precedent[:len(precedent) - len('and')].strip()) / len(key)) < endswith_precedent_threshold:
			return True
	return False

def valid_endswith(key: str, k: str) -> bool:
	if len(re.split(regexes['spaces'], key)) < 2:
		return False
	if len(re.split(regexes['spaces'], k)) < 2:
		return False
	if key.endswith(k):
		if check_end_qualifiers(key, k):
			return True
	if k.endswith(key):
		if check_end_qualifiers(k, key):
			return True
	return False

# [//:] Levenshtein
antonyms = [
	['beginning', 'end'],
	['derivative', 'warrant'],
	['financing', 'operating', 'investing'],
	['continuing', 'discontinued'],
	['net', 'gross'],
	['deficit', 'equity'],
	['assets', 'liabilities'],
	['increase', 'decrease']
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