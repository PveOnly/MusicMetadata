import json
from pathlib import Path
from pytube import YouTube
from src.utils import flatten_dict, sanitize_name,convert_mp4_to_mp3
from src.genius_scrapping import MetadataEYED

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
    assert video_stream is not None,'video_stream is None'
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
        output_path=output_path.as_posix(), filename=filename_mp4, timeout=10
    )  # type: ignore
    # breakpoint()
    # json.dump(yt.__dict__,open('test_yt.json','w'),cls=GlobalEncoder,indent=4,skipkeys=True)
    # json.dump(video_stream.__dict__,open('test_video_stream.json','w'),cls=JsonSafe,indent=4)
    print(f"Downloaded: {yt.title}")
    # video_metadata = extract_metadata(yt)
    # video_metadata=dict(filter(lambda key :True if isinstance(key[1],str) and len(key[1])<=100 else False,flatten_dict(yt.__dict__).items()))
    def filter_str(value):
        if isinstance(value, str) and len(value) >= 1000:
            return False
        else:
            return True

    # breakpoint()
    # video_metadata = {k: v for k, v in flatten_dict(yt.__dict__).items() if filter_str(v) }
    video_metadata = {attr: getattr(yt, attr) for attr in dir(yt) if filter_str(getattr(yt, attr))}
    video_metadata=flatten_dict(video_metadata)
    # video_metadata.update(all_attributes)

    json.dump(video_metadata,path_to_json.open(mode='w'),indent=4,default=str)
    return (path_to_mp4,video_metadata)

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
        path_to_video,video_metadata=download_video(youtube_url, output_dir,force=True)
        metadata_video_eyed3.from_dict_metadata_update_self_metadata(video_metadata,force_replace=False)
        # metadata_video_eyed3.is_metadata_complete()
        metadata_video_eyed3.show()
        # breakpoint()
        # break
        # def get maximun extra_data
        artist=metadata_video_eyed3.artist
        title=metadata_video_eyed3.title
        title_music=f"{artist} {title}"
        metadata_video_eyed3.get_metadata_google(title_music)
        if metadata_video_eyed3.is_metadata_complete():
            metadata_video_eyed3.get_metadata_google(f"{artist} {title} GENRE")
        if metadata_video_eyed3.is_metadata_complete():
            metadata_video_eyed3.get_metadata_disco(title_music)
        # metadata_video_eyed3.show()
        convert_mp4_to_mp3(path_to_video)
        metadata_video_eyed3.from_metadata_update_mp3_video(path_to_video)
        print("###")

if __name__ == "__main__":
    main()
