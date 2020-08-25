import decimal
import math
from typing import List, Union
from prototype import transform_data

# We use median number of decimal places
def get_accuracy(values: List[str]) -> int:
	places = [decimal.Decimal(v).as_tuple().exponent if v else 0 for v in values]
	places.sort()
	return int(math.fabs(places[int(len(places) / 2)]))

# We use the modal magnitude for this comparison
def get_magnitude(values: List[str]) -> int:
	arr = [transform_data(x) for x in values]
	size_dict = {}
	for x in arr:
		size = math.ceil(math.log10(math.fabs(x))) if x else 0
		s = str(size)
		if not s in size_dict:
			size_dict[s] = 0
		size_dict[s] += 1
	sorted = list(size_dict.items())
	sorted.sort(reverse=True)
	if not sorted[0]:
		return None
	return int(sorted[0][0])

# We check if negative (-1), positive (+1), or mixed (0)
def get_polarity(values: List[str]) -> Union[int]:
	arr = [transform_data(x) for x in values]
	is_positive = True
	is_negative = True
	for a in arr:
		if not a:
			continue
		if a > 0:
			is_negative = False 
		elif a < 0:
			is_positive = False
	if is_positive:
		return 1
	if is_negative:
		return -1
	return 0