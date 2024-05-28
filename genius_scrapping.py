import unicodedata
import requests
from bs4 import BeautifulSoup


def fetch_and_parse_url(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59"
    }
    cookies = {"CONSENT": "YES+"}

    # Send GET request with custom headers
    response = requests.get(url, headers=headers, cookies=cookies)
    # response.raise_for_status()  # Raises an HTTPError for bad responses
    page_source_text = response.text

    # Use BeautifulSoup to parse the HTML content
    soup = BeautifulSoup(page_source_text, "html.parser")
    return soup

def save_to_file(content, filename):
    # Save the prettified HTML to a file
    with open(filename, "w", encoding="utf-8") as file:
        file.write(content)

def get_metadata_music(music_name):
    url = f"https://www.google.com/search?q={music_name}"
    # print(url)
    dict_metadata = {}
    try:
        # find closest music link
        soup_object = fetch_and_parse_url(url)
        data_to_find = {
            "Artist": "kc:/music/recording_cluster:artist",
            "Album": "kc:/music/recording_cluster:first album",
            "ReleaseDate": "kc:/music/recording_cluster:release date",
            "Genre": "kc:/music/recording_cluster:skos_genre",
        }
        for key, path in data_to_find.items():
            value = soup_object.find_all("div", attrs={"data-attrid": path})
            if not value:
                dict_metadata[key] = None
                continue
            value=value[-1]
            value=value.text
            new_str = unicodedata.normalize("NFKD", value.strip())
            dict_metadata[key] = new_str.split(":")[-1].strip()
        # print(dict_metadata)
        # print(dict_metadata)
        # parsed_content = soup_object.prettify()
        # save_to_file(parsed_content, "parsed_content.html")
        # print("Content parsed and saved successfully.")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
    # print(dict_metadata)
    return dict_metadata


def test():
    name_music = "BRIZEL'KHEUR"
    metadata = get_metadata_music(name_music)
    print(metadata)


if __name__ == "__main__":
    test()
