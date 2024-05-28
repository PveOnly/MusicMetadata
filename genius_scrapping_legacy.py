import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from utils import find_closest_match
import unicodedata
# from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By


def setup_driver():
    # Set options for headless mode
    options = Options()
    options.headless = True
    options.add_argument("--window-size=1920,1080")  # Define window size if needed
    options.add_argument(
        "--disable-gpu"
    )  # This option is often recommended to avoid bugs with headless scraping
    options.add_argument(
        "--no-sandbox"
    )  # This option is also recommended for running in a Docker container, if applicable
    options.add_argument(
        "--disable-dev-shm-usage"
    )  # Overcome limited resource problems
    options.add_argument("--headless=new")
    # options.add_argument("--disable-javascript")
    # prefs = {
    #     "profile.default_content_setting_values.stylesheets": 2,
    # }
    # options.add_experimental_option("prefs", prefs)
    # Set up Chrome driver with options
    # service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(options=options)
    return driver


def fetch_page_source(url):
    driver = setup_driver()
    driver.get(url)

    # Get the page source and print it
    page_source = driver.page_source
    driver.quit()  # Make sure to close the driver after the task is complete
    return page_source


def fetch_and_parse_url(url, mode="selenium"):
    # Define headers to mimic a browser's request
    if mode == "selenium":
        page_source_text = fetch_page_source(url)
    else:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59"
        }
        cookies = {"CONSENT": "YES+"}

        # Send GET request with custom headers
        response = requests.get(url, headers=headers, cookies=cookies)
        breakpoint()
        # response.raise_for_status()  # Raises an HTTPError for bad responses
        page_source_text = response.text

    # Use BeautifulSoup to parse the HTML content
    soup = BeautifulSoup(page_source_text, "html.parser")
    return soup


def get_all_links(soup):
    # Find all <a> tags and extract the 'href' attribute
    links = [a["href"] for a in soup.find_all("a") if a.has_attr("href")]
    return links


def save_to_file(content, filename):
    # Save the prettified HTML to a file
    with open(filename, "w", encoding="utf-8") as file:
        file.write(content)


def save_links_to_file(links, filename):
    # Save the extracted links to a file, one link per line
    with open(filename, "w", encoding="utf-8") as file:
        for link in links:
            file.write(link + "\n")


# Example usage
def main():
    name_music = "Ariana Grande - we can't be friends (wait for your love)"
    url = "https://genius.com/search?q=we%20can%27t%20be%20friends%20"
    try:
        # find closest music link
        soup_object = fetch_and_parse_url(url)
        list_link = get_all_links(soup_object)
        closest_url = find_closest_match(name_music, list_link)
        save_links_to_file(list_link, "extracted_links.txt")
        # two get page from this url
        soup_object = fetch_and_parse_url(closest_url)
        parsed_content = soup_object.prettify()
        save_to_file(parsed_content, "parsed_content.html")
        print("Content parsed and saved successfully.")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")


def extract_div_elements(url):
    driver = setup_driver()
    driver.get(url)

    # Use XPath with starts-with() to match elements
    xpath_expression = "//div[starts-with(@data-attrid, 'kc:/music/recording_cluster')]"

    # Find elements by XPath
    elements = driver.find_elements(By.XPATH, xpath_expression)

    # Extracting full HTML of the elements for demonstration; adjust as needed
    extracted_info = [element.text for element in elements]

    driver.quit()
    return extracted_info


def main_2():
    name_music = "Ariana Grande - we can't be friends (wait for your love)"
    url = f"https://www.google.com/search?q={name_music}"
    print(url)
    extracted_elements = extract_div_elements(url)
    good_element = sorted(extracted_elements, reverse=False)[:-1]
    dict_metadata = {}
    for elt in good_element:
        key, val = list(map(str.strip, elt.split(":")))
        dict_metadata[key] = val
    print(dict_metadata)





def get_metadata_music(music_name):
    url = f"https://www.google.com/search?q={music_name}"
    try:
        # find closest music link
        soup_object = fetch_and_parse_url(url, mode="request")
        # parsed_content = soup_object.prettify()
        data_to_find = {
            "Artist": "kc:/music/recording_cluster:artist",
            "Album": "kc:/music/recording_cluster:first album",
            "ReleaseDate": "kc:/music/recording_cluster:release date",
            "Genre":"kc:/music/recording_cluster:skos_genre"
        }
        dict_metadata={}
        for key,path in data_to_find.items():
            value=soup_object.find('div',attrs={'data-attrid':path}).text
            new_str = unicodedata.normalize("NFKD", value.strip())
            dict_metadata[key]=new_str.split(':')[-1].strip()
        # print(dict_metadata)
        # save_to_file(parsed_content, "parsed_content.html")
        # print("Content parsed and saved successfully.")
        return dict_metadata

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        
def test():
    name_music = "Ariana Grande - we can't be friends (wait for your love)"
    url = "https://genius.com/search?q=we%20can%27t%20be%20friends%20"
    try:
        # find closest music link
        soup_object = fetch_and_parse_url(url, mode="request")
        parsed_content = soup_object.prettify()
        save_to_file(parsed_content, "parsed_content.html")
        print("Content parsed and saved successfully.")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

def test_1():
    url="https://www.discogs.com/fr/release/30384242-Sokuu-Solanin"
    soup_object = fetch_and_parse_url(url, mode="request")
    parsed_content = soup_object.prettify()
    save_to_file(parsed_content, "parsed_content.html")
    print("Content parsed and saved successfully.")
test_1()
