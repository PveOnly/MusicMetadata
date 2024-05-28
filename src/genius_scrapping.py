import json
import unicodedata

import eyed3
import requests
from bs4 import BeautifulSoup

from src.utils import (
    convert_path_to_mp3_path,
    download_image_to_memory,
    flatten_dict,
    get_close_matches,
    is_dict_has_none_key,
)


class MetadataEYED:
    # Mapping of base keys and their aliases
    MAPPING_KEYS = {
        'artist': ['artist','Artist', 'author','releaseOf.byArtist[0].name','_vid_info.videoDetails.author'],
        'album': ['album','Album','releaseOf.name'],
        'genre': ['genre','Genre','genre[0]'],
        'release_date': ['release_date','Release_date','releaseOf.datePublished','_publish_date','publish_date'],
        'title': ['title','Title','_title'],
        'internet_radio_url': ['internet_radio_url','Internet_radio_url','watch_url'],
        'images':['thumbnail_url'],
        # 'thumbnail_url':['thumbnail_url']
    }
    METADATA_TEMPLATE={
        'artist':None ,
        'album':None ,
        'genre':None ,
        'release_date':None ,
        'title':None ,
        'internet_radio_url':None ,
        'images':None,
    }
    KEYS_TO_SKIP=['images']

    def __init__(self) -> None:
        self._metadata=MetadataEYED.METADATA_TEMPLATE.copy()

    def show(self,only_none=False):
        for key,val in self.metadata.items():
            if only_none:
                if val is None:
                    print(f'{key} : {val}')
            else:
                print(f'{key} : {val}')
    @property
    def artist(self):
        val= self.metadata['artist']
        assert val is not None
        return val
    
    @property
    def title(self):
        val= self.metadata['title']
        assert val is not None
        return val
    
    def is_metadata_complete(self) ->bool:
        # self.show(only_none=True)
        return is_dict_has_none_key(self.metadata)
    
    @property
    def metadata(self) -> dict:
        return self._metadata
    
    @metadata.setter
    def metadata(self, value):
        """Set the metadata dictionary."""
        if not isinstance(value, dict):
            raise ValueError("Metadata must be a dictionary")
        # Additional checks or transformations could be added here
        self._metadata = value

    def from_dict_metadata_update_self_metadata(self,dict_metadata,force_replace=False):
        for key_metadata,val_metadata in dict_metadata.items():
            if val_metadata is None:
                continue
            for key_eyed,list_other_possible_key_name in MetadataEYED.MAPPING_KEYS.items():
                if key_metadata in list_other_possible_key_name:
                    val_metadata=str(val_metadata).strip()
                    if key_eyed not in ['internet_radio_url','images']:
                        val_metadata=val_metadata.lower()
                    if self.metadata[key_eyed] is None or force_replace:
                        self.metadata[key_eyed]=val_metadata
                    else:
                        if val_metadata!=self.metadata[key_eyed]:
                            print(f"Strange {val_metadata} is different than current value {self.metadata[key_eyed]}")

    def normalize(self,dict_metadata):
        self.from_dict_metadata_update_self_metadata(dict_metadata,force_replace=False)
        return dict_metadata
    
    # @normalize
    def get_metadata_google(self,name_music):
        dict_metadata=get_metadata_music(name_music)
        dict_metadata=flatten_dict(dict_metadata)
        self.normalize(dict_metadata)
        return dict_metadata
    
    # @normalize(self)
    def get_metadata_disco(self,name_music):
        dict_metadata=get_metadata_discogs(name_music)
        dict_metadata=flatten_dict(dict_metadata)
        self.normalize(dict_metadata)
        # discogs_metadata=['releaseOf.byArtist[0].name','releaseOf.name','genre[0]','releaseOf.datePublished']
        # eyed3_metadata=  ['artist','album','genre','release_date']
        # dict_release_mapped_to_eyed3=from_two_list_create_new_dict(eyed3_metadata,discogs_metadata,dict_metadata)
        return dict_metadata
    
    @staticmethod
    def normalize_dict(dict_to_normalize):
        print('pass')

    def from_metadata_update_mp3_video(self,input_path):
        # mapping_metadata=['author','Album','Genre','publish_date','title','watch_url']
        # eyed3_metadata=  ['artist','album','genre','release_date','title','internet_radio_url']
        # mapping_data={key:val for key,val in zip(eyed3_metadata,mapping_metadata,strict=True)}
        path_mp3=convert_path_to_mp3_path(input_path)
        audiofile = eyed3.load(path_mp3)
        assert audiofile is not None,'AudioFile is None'
        assert audiofile.tag is not None,'AudioFile.tag is None'
        audiofile.initTag(version=(2, 3, 0))  # version is important
        if audiofile is None:
            raise Exception('Error wrong conversion to mp3')
        # breakpoint()
        for key, val in self.metadata.items():
            if key in MetadataEYED.KEYS_TO_SKIP:
                continue
            setattr(audiofile.tag, key, val)
        
        thumbnail_url=self.metadata['images']
        imagedata=download_image_to_memory(thumbnail_url)
        audiofile.tag.images.set(3, imagedata, "image/jpeg", "cover")
        audiofile.tag.save()
        print("Updated Metadata")

def fetch_and_parse_url(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59"
    }
    cookies = {"CONSENT": "YES+"}

    # Send GET request with custom headers
    response = requests.get(url, headers=headers, cookies=cookies,timeout=4)
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
            "artist": "kc:/music/recording_cluster:artist",
            "album": "kc:/music/recording_cluster:first album",
            "release_date": "kc:/music/recording_cluster:release date",
            "genre": "kc:/music/recording_cluster:skos_genre",
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

def get_all_links(soup):
    # Find all <a> tags and extract the 'href' attribute
    links = [a["href"] for a in soup.find_all("a") if a.has_attr("href")]
    return links

def save_content(soup):
    parsed_content = soup.prettify()
    save_to_file(parsed_content, "parsed_content.html")
    print("Content parsed and saved successfully.")

def from_two_list_create_new_dict(key_ref:list[str],key_val:list[str],dict_key_val:dict):
    dict_with_new_value={}
    mapping_data={key:val for key,val in zip(key_ref,key_val,strict=True)}
    for key_tag, key_metadata in mapping_data.items():
        new_val=dict_key_val[key_metadata]
        dict_with_new_value[key_tag]=new_val
    return dict_with_new_value


def get_metadata_discogs(music_name):
    keywords="discogs"
    url = f"https://www.google.com/search?q={music_name}+{keywords}"
    # print(url)
    soup_object = fetch_and_parse_url(url)
    # save_content(soup_object)
    link_usefull=get_all_links(soup_object)
    closest=get_close_matches(f'{keywords} {music_name}',link_usefull,cutoff=0.1)
    # print(closest)
    good_url=None
    for url in closest:
        if 'release' in url:
            good_url=url
            break
    assert good_url is not None,'Dit not found good url for discogs'

    soup_object = fetch_and_parse_url(good_url.replace('https','http'))
    # breakpoint()
    value_soup=soup_object.find(id="release_schema")
    assert value_soup is not None,'Error value soup is none'
    value_soup=value_soup.text
    return json.loads(value_soup)

def test():
    music_name = "Sokuu BRIZEL'KHEUR"
    keywords="discogs"
    url = f"https://www.google.com/search?q={music_name}+{keywords}"
    # print(url)
    soup_object = fetch_and_parse_url(url)
    # save_content(soup_object)
    link_usefull=get_all_links(soup_object)
    closest=get_close_matches(f'{keywords} {music_name}',link_usefull,cutoff=0.1)

def test_2():
    name_music="Sokuu BRIZEL'KHEUR"
    dict_val=MetadataEYED()
    # breakpoint()
    dict_val.get_metadata_google(name_music)
    dict_val.get_metadata_disco(name_music)
    dict_val.show()

if __name__ == "__main__":
    test_2()
