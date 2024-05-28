import json
import re
import unicodedata
from pathlib import Path

import eyed3
import requests
from bs4 import BeautifulSoup

from src.utils import (
    convert_path_to_mp3_path,
    download_image_to_memory,
    flatten_dict,
    get_close_matches,
    is_dict_has_none_key,
    sanitize_name,
)


class MetadataEYED:
    # Mapping of base keys and their aliases
    MAPPING_KEYS = {
        'artist': ['artist','Artist', 'author','releaseOf.byArtist[0].name','_vid_info.videoDetails.author',"kc:/music/recording_cluster:artist"],
        'album': ['album','Album','releaseOf.name',"kc:/music/recording_cluster:first album"],
        'genre': ['genre','Genre','genre[0]',"kc:/music/recording_cluster:skos_genre","kc:/music/album:skos genre","kc:/music/artist:skos genre"],
        'release_date': ['release_date','Release_date','releaseOf.datePublished','_publish_date','publish_date',"kc:/music/recording_cluster:release date"],
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
    METADATA_MINIMA_KEYS_TO_BE_SET=["artist","album","release_date","title","genre"]
    KEYS_TO_SKIP_TO_SET_EYED3=['images']

    def __init__(self,output_path:Path|None=None,dump_json=True) -> None:
        self._metadata=MetadataEYED.METADATA_TEMPLATE.copy()
        self.output_path=output_path
        self.dump_json=dump_json

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
        for val_remove in ['(clip officiel)',self.artist]:
            val=val.replace(val_remove,'')
        return val
    
    def is_metadata_complete(self,minimal_key=True) ->bool:
        # self.show(only_none=True)
        if minimal_key:
            values_list=[]
            for key in self.METADATA_MINIMA_KEYS_TO_BE_SET:
                val=self.metadata[key]
                values_list.append(val)
            if None in values_list:
                return False
            else:
                return True
        else:
            return None not in self.metadata.values()
    
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

    def from_dict_metadata_update_self_metadata(self,dict_metadata,force_replace=False,mute=True):
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
                            if not mute:
                                print(f"Strange {val_metadata} is different than current value {self.metadata[key_eyed]}")

    def normalize(self,dict_metadata):
        self.from_dict_metadata_update_self_metadata(dict_metadata,force_replace=False)
        return dict_metadata
    
    # @normalize
    def get_metadata_google(self,name_music):
        dict_metadata=get_metadata_music(name_music)
        dict_metadata=flatten_dict(dict_metadata)
        filename_music=sanitize_name(name_music)
        self.save_dict(dict_metadata,f'{filename_music}_extract_metadata_google.json')
        self.normalize(dict_metadata)
        return dict_metadata
    
    # @normalize(self)
    def get_metadata_disco(self,name_music):
        dict_metadata=get_metadata_discogs(name_music)
        dict_metadata=flatten_dict(dict_metadata)
        filename_music=sanitize_name(name_music)
        self.save_dict(dict_metadata,f'{filename_music}_extract_metadata_disco.json')
        self.normalize(dict_metadata)
        # discogs_metadata=['releaseOf.byArtist[0].name','releaseOf.name','genre[0]','releaseOf.datePublished']
        # eyed3_metadata=  ['artist','album','genre','release_date']
        # dict_release_mapped_to_eyed3=from_two_list_create_new_dict(eyed3_metadata,discogs_metadata,dict_metadata)
        return dict_metadata
    
    def save_dict(self,dict_metadata,filename):
        if self.dump_json:
            filepath=self.output_path/filename
            json.dump(dict_metadata,open(filepath,'w',encoding='utf-8'),indent=4,default=str)

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
            if key in MetadataEYED.KEYS_TO_SKIP_TO_SET_EYED3:
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
        # data_to_find = {
        #     "artist": "kc:/music/recording_cluster:artist",
        #     "album": "kc:/music/recording_cluster:first album",
        #     "release_date": "kc:/music/recording_cluster:release date",
        #     "genre": "kc:/music/recording_cluster:skos_genre",
        # }
        pattern = re.compile(r'kc:/music.*')
        def match_pattern(tag):
            return tag.name == 'div' and tag.has_attr('data-attrid') and pattern.match(tag['data-attrid'])
        # Use the function with find_all to get matching divs
        matching_divs = soup_object.find_all(match_pattern) # type: ignore
        dict_metadata={}
        for div in matching_divs:
            data_attrid=div['data-attrid']
            value=unicodedata.normalize("NFKD", div.text.strip())
            # only split if we kniow there is only one : in the string
            if value.count(':')==1:
                value=value.split(':')[1].strip()
            dict_metadata[data_attrid]=value

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


def get_metadata_discogs(music_name,raise_error=False):
    keywords="discogs"
    url_ori = f"https://www.google.com/search?q={music_name}+{keywords}"
    # print(url)
    soup_object = fetch_and_parse_url(url_ori)
    save_content(soup_object)
    link_usefull=[url for url in get_all_links(soup_object) if keywords in url and 'http' in url]
    closest=get_close_matches(f'{music_name}',link_usefull,cutoff=0.3)
    # breakpoint()
    # print(closest)
    good_url=None
    for url in closest:
        if 'release' in url:
            good_url=url
            break
        
    if good_url is None:
        if raise_error:
            raise AssertionError(f'Did not find a good URL for Discogs: {url_ori} with {closest}')
        else:
            print(f'Did not find a good URL for Discogs: {url_ori} with {closest}')
            return {}

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
    url="https://www.google.com/search?q=theodort+wayeh+%2B+GENRE"
    dict_val=MetadataEYED()
    # breakpoint()
    soup_object = fetch_and_parse_url(url)
    # dict_val.get_metadata_google(name_music)
    # Compile a regex that matches 'kc:/music' followed by anything
    pattern = re.compile(r'kc:/music.*')
    # Define a function that checks if 'data-attrid' matches the pattern
    def match_pattern(tag):
        return tag.name == 'div' and tag.has_attr('data-attrid') and pattern.match(tag['data-attrid'])
    # Use the function with find_all to get matching divs
    matching_divs = soup_object.find_all(match_pattern) # type: ignore

    # Print the matching divs
    for div in matching_divs:
        print(div)

if __name__ == "__main__":
    test_2()
