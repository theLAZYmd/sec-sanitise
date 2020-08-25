import re

regexes = {
    'year': r"(?:2\s?0|1\s?9)\s?[0-9]\s?[0-9]$",
    'currency': r"^[$£]$",
	'brackets': r"(?:\s+/\s+)?[\(\[].*?[\)\]](?:\s+/\s+)?",
	'spaces': r"\s+",
	'date_spec': r"\s+at\s+[a-z]{3}\.?\s+[0-9]{1,2},?\s+(?:2\s?0|1\s?9)\s?[0-9]\s?[0-9]",
	'loss': r"(?:net|other).*loss",
	'negative': r"\s*(?:\s+un|no(?:t|n)?)-?\s*",
	'currency_spec': r"\s+of\s+[^\w]*[0-9]+"
}