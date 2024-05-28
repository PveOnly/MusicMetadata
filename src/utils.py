import re
import subprocess
from difflib import get_close_matches
from pathlib import Path

import requests

# from pil import Image

def find_closest_match(string_ref, string_list):
    # The function returns a list of the best "close matches"
    # 'n' defines the number of results you want
    # 'cutoff' is a float between 0 and 1 that defines the threshold for a matched result
    # Here, n=1 ensures only the top match is returned, and cutoff=0.0 means even low similarity results are considered
    matches = get_close_matches(string_ref, string_list, n=1, cutoff=0.0)
    return matches[0] if matches else None

def convert_mp4_to_mp3(input_file:Path):
    output_file=convert_path_to_mp3_path(input_file)
    cmd_ffmpeg=["ffmpeg","-hide_banner","-loglevel","error","-y" ,"-i"]
    # if output_file.exists():
    #     cmd_ffmpeg.append('-y')
    if output_file.exists():
        return 0
    cmd_ffmpeg.extend([input_file.as_posix(), output_file.as_posix()])
    exit_code=subprocess.run(cmd_ffmpeg,check=False)
    print(exit_code)

# def resize_image_to_jpeg_bytes(input_path):
#     # Open an image file
#     with Image.open(input_path) as img:
#         # Resize the image
#         img = img.resize((32, 32), Image.Resampling.LANCZOS)  # LANCZOS is recommended for high-quality downsampling

#         # Save the resized image to a BytesIO object in memory as JPEG
#         img_byte_arr = io.BytesIO()
#         img.save(img_byte_arr, format='JPEG', quality=85)  # You can adjust the quality level from 1 to 95

#         # Return image data as a byte array
#         return img_byte_arr.getvalue()

def download_image_to_memory(image_url):
    # Send an HTTP GET request to the image URL
    response = requests.get(image_url)
    response.raise_for_status()  # Check for HTTP errors
    with open('test.jpg','wb') as f:
        f.write(response.content)
    return response.content

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

def flatten_dict(d, parent_key='', sep='.'):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            for i, item in enumerate(v):
                if isinstance(item, dict):
                    items.extend(flatten_dict(item, f"{new_key}[{i}]", sep=sep).items())
                else:
                    items.append((f"{new_key}[{i}]", item))
        else:
            items.append((new_key, v))
    return dict(items)

def is_dict_has_none_key(dict_metadata: dict) -> bool:
        return None in dict_metadata.keys()

def convert_path_to_mp3_path(input_path:Path) -> Path:
    return input_path.parent/f'{input_path.stem}.mp3'