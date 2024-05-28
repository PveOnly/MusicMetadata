from difflib import get_close_matches
import re
def find_closest_match(string_ref, string_list):
    # The function returns a list of the best "close matches"
    # 'n' defines the number of results you want
    # 'cutoff' is a float between 0 and 1 that defines the threshold for a matched result
    # Here, n=1 ensures only the top match is returned, and cutoff=0.0 means even low similarity results are considered
    matches = get_close_matches(string_ref, string_list, n=1, cutoff=0.0)
    return matches[0] if matches else None



MAPPING_COMMON_NON_FRENCH_ASCII_CHAR = {
    "é": "e",
    "à": "a",
    "è": "e",
    "ç": "c",
    "ê": "e",
    "ë": "e",
    "â": "a",
    "î": "i",
    "ï": "i",
    "ô": "o",
    "û": "u",
    "ù": "u",
    "ü": "u",
    "É": "E",
    "À": "A",
    "È": "E",
    "Ç": "C",
    "Ê": "E",
    "Ë": "E",
    "Â": "A",
    "Î": "I",
    "Ï": "I",
    "Ô": "O",
    "Û": "U",
    "Ù": "U",
    "Ü": "U",
    "œ": "oe",
}


def remove_french_caracter(string):
    string = "".join(
        [
            char
            if char not in MAPPING_COMMON_NON_FRENCH_ASCII_CHAR
            else MAPPING_COMMON_NON_FRENCH_ASCII_CHAR[char]
            for char in string
        ]
    )
    return string


def sanitize_name(dir_name):
    # Replace spaces with underscores
    dir_name = dir_name.replace(" ", "").replace('\'','')

    # Remove special characters not allowed in directory names
    not_allowed = r'[\\/:*?"<>|]'
    dir_name = re.sub(not_allowed, "", dir_name)

    # Remove non-ASCII characters
    # isascii() has same effect
    dir_name = "".join(
        [
            char
            if char not in MAPPING_COMMON_NON_FRENCH_ASCII_CHAR
            else MAPPING_COMMON_NON_FRENCH_ASCII_CHAR[char]
            for char in dir_name
        ]
    )
    dir_name = "".join(char for char in dir_name if ord(char) < 128)

    return dir_name