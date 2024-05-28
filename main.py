from pathlib import Path
from pytube import YouTube
import numpy as np
import json
from global_jsonencoder import GlobalEncoder
from genius_scrapping import get_metadata_music,get_metadata_discogs
import eyed3
import subprocess
from utils import sanitize_name
import requests
from PIL import Image
from io import BytesIO
from eyed3.id3.frames import ImageFrame
from eyed3.id3.tag import ImagesAccessor
from PIL import Image
import io
from genius_scrapping import MetadataEYED

def download_image_to_memory(image_url):
    # Send an HTTP GET request to the image URL
    response = requests.get(image_url)
    response.raise_for_status()  # Check for HTTP errors

    # Use BytesIO to create a buffer from the binary data returned by the request
    # image_buffer = BytesIO(response.content)

    # Open the image as a PIL Image object
    # image = Image.open(image_buffer)
    with open('test.jpg','wb') as f:
        f.write(response.content)
    return response.content

def resize_image_to_jpeg_bytes(input_path):
    # Open an image file
    with Image.open(input_path) as img:
        # Resize the image
        img = img.resize((32, 32), Image.Resampling.LANCZOS)  # LANCZOS is recommended for high-quality downsampling

        # Save the resized image to a BytesIO object in memory as JPEG
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG', quality=85)  # You can adjust the quality level from 1 to 95

        # Return image data as a byte array
        return img_byte_arr.getvalue()

def from_metadata_update_mp3_video(input_path, metadata_dict):
    mapping_metadata=['author','Album','Genre','publish_date','title','watch_url']
    eyed3_metadata=  ['artist','album','genre','release_date','title','internet_radio_url']
    mapping_data={key:val for key,val in zip(eyed3_metadata,mapping_metadata,strict=True)}
    path_mp3=convert_path_to_mp3_path(input_path)
    audiofile = eyed3.load(path_mp3)
    assert audiofile is not None,'AudioFile is None'
    assert audiofile.tag is not None,'AudioFile.tag is None'
    audiofile.initTag(version=(2, 3, 0))  # version is important
    if audiofile is None:
        raise Exception('Error wrong conversion to mp3')
    # breakpoint()
    for key_tag, key_metadata in mapping_data.items():
        val=metadata_dict[key_metadata]
        setattr(audiofile.tag, key_tag, val)
    # breakpoint()
    # print(thumbnail_url)
    thumbnail_url=metadata_dict['thumbnail_url']
    imagedata=download_image_to_memory(thumbnail_url)
    # audiofile.tag.images.set(type_=3, img_data=None, mime_type="image/png", description=u"you can put a description here", img_url=thumbnail_url)
    # img_data=requests.get(thumbnail_url).text
    # imagedata = open("test.jpg","rb").read()
    # icon=resize_image_to_jpeg_bytes("test.jpg")
    # audiofile.tag.images[0].img_data=imagedata
    # # audiofile.tag.images[0].img_data=imagedata
    audiofile.tag.images.set(3, imagedata, "image/jpeg", u"cover")
    # audiofile.tag.images=ImagesAccessor(fs=[])
    # for i in range(0,21):
    #     audiofile.tag.images.set(i, imagedata, "image/jpeg", u"random")
    # audiofile.tag.images.set(ImageFrame.BACK_COVER, imagedata, "image/jpeg", u"random")
    # audiofile.tag.images.set(ImageFrame.ICON, icon, "image/jpeg", u"random")
    # audiofile.tag.images.set(ImageFrame.OTHER_ICON, icon, "image/jpeg", u"cover")
    # audiofile.tag.images.set(ImageFrame.OTHER_ICON, icon, "image/jpeg", "Cover Image")
    # audiofile.tag.images.set(3, imagedata, "image/jpeg", "APIC")
    # breakpoint()
    # with open('test.jpg','w') as f:
    #     f.write(img_data)
    # breakpoint()
    audiofile.tag.save()
    print("Updated Metadata")


def extract_metadata(yt):
    dict_metadata = {
        "author": None,
        "publish_date": None,
        "title": None,
        "thumbnail_url": None,
        "watch_url": None,
    }
    # vid_info=yt.__dict__['_vid_info']
    for key in dict_metadata.keys():
        val = getattr(yt, key)
        print(f"{key} : {val}")
        dict_metadata[key] = val
    return dict_metadata


def download_video(url, output_path:Path,filename: str|None=None,force=False):
    # Create YouTube object
    yt = YouTube(url)
    print("Starting video_stream")
    # Select the highest resolution stream that contains only video
    video_stream = (
        yt.streams.filter(progressive=True, file_extension="mp4")
        .order_by("resolution")
        .desc()
        .first()
    )
    # video_stream = yt.streams.filter(progressive=True)
    # print(video_stream)
    # Download the video
    if filename is None:
        filename=sanitize_name(yt.title)
        filename_mp4=filename+'.mp4'
        filename_json=filename+"_extract_metadata.json"
    
    path_to_json=output_path/f'{filename_json}'
    path_to_mp4=output_path/f'{filename_mp4}'
    if path_to_json.exists() and force is False:
        print("Skipping video, already treated")
        return (path_to_mp4,json.load(path_to_json.open(mode='r')))
    video_stream.download(
        output_path=output_path, filename=filename_mp4, timeout=10
    )  # type: ignore
    # breakpoint()
    # json.dump(yt.__dict__,open('test_yt.json','w'),cls=GlobalEncoder,indent=4,skipkeys=True)
    # json.dump(video_stream.__dict__,open('test_video_stream.json','w'),cls=JsonSafe,indent=4)
    print(f"Downloaded: {yt.title}")
    video_metadata = extract_metadata(yt)
    json.dump(video_metadata,path_to_json.open(mode='w'),indent=4,default=str)
    video_metadata['publish_date']=str(video_metadata['publish_date'])
    return (path_to_mp4,video_metadata)


def convert_mp4_to_mp3(input_file:Path):
    output_file=convert_path_to_mp3_path(input_file)
    cmd_ffmpeg=["ffmpeg","-y" ,"-i"]
    # if output_file.exists():
    #     cmd_ffmpeg.append('-y')
    if output_file.exists():
        return 0
    cmd_ffmpeg.extend([input_file.as_posix(), output_file.as_posix()])
    exit_code=subprocess.run(cmd_ffmpeg)
    print(exit_code)

def convert_path_to_mp3_path(input_path:Path) -> Path:
    return input_path.parent/f'{input_path.stem}.mp3'

def is_dict_has_none_key(dict_metadata: dict) -> bool:
    return None in dict_metadata.keys()

def main():
    # Example usage
    list_youtube_url = [
        "https://www.youtube.com/watch?v=KNtJGQkC-WI",  # Replace with your YouTube URL,
         "https://www.youtube.com/watch?v=0a1juREe4YQ",
         "https://www.youtube.com/watch?v=d3Un6waXXxE",
         "https://www.youtube.com/watch?v=hHBd9DNOLBg",
         "https://www.youtube.com/watch?v=ZWWjjLY2KPo",
         "https://www.youtube.com/watch?v=tTq3h8pfPT0",
         "https://www.youtube.com/watch?v=a5InofcZEHQ",
         "https://www.youtube.com/watch?v=Q7yppe2b6II"
    ]
    for youtube_url in list_youtube_url:
        metadata_video_eyed3=MetadataEYED()
        print(f"{youtube_url}")
        output_dir=Path('mp3_file')
        output_dir.mkdir(exist_ok=True)
        path_to_video,video_metadata=download_video(youtube_url, output_dir)
        metadata_video_eyed3.from_dict_metadata_update_self_metadata(video_metadata,force_replace=False)
        # def get maximun extra_data
        author=video_metadata['author']
        title=video_metadata['title']
        assert title is not None, 'Careful title is None'
        assert author is not None,'Carefull author is None'
        title_music=f"{author} {title}"
        metadata_video_eyed3.get_metadata_google(title_music)
        
        if metadata_video_eyed3.is_metadata_complete():
            metadata_video_eyed3.get_metadata_google(f"{author} {title} GENRE")

        if metadata_video_eyed3.is_metadata_complete():
            metadata_video_eyed3.get_metadata_disco(title_music)

        convert_mp4_to_mp3(path_to_video)
        from_metadata_update_mp3_video(path_to_video, video_metadata)
        print("###")

if __name__ == "__main__":
    main()
