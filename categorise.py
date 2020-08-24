from typing import List, Union

def polarity(arr: List[Union[int, float]]) -> Union(-1, 0, 1):
	is_positive = True
	is_negative = True
	for a in arr:
		if a > 0:
			is_negative = False 
		elif a < 0:
			is_positive = False
	if is_positive:
		return 1
	if is_negative:
		return -1
	return 0