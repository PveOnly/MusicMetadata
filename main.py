import json
import re
import shutil
from pathlib import Path

from pytube import YouTube

import src.genius_scrapping
from src.genius_scrapping import MetadataEYED
from src.utils import convert_mp4_to_mp3, flatten_dict, sanitize_name


def download_video(url, output_path: Path, filename: str | None = None, force=False):
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
    assert video_stream is not None, "video_stream is None"
    # video_stream = yt.streams.filter(progressive=True)
    # print(video_stream)
    # Download the video
    if filename is None:
        filename = sanitize_name(yt.title)
        filename_mp4 = filename + ".mp4"
        filename_json = filename + "_extract_metadata_pytube.json"

    path_to_json = output_path / f"{filename_json}"
    path_to_mp4 = output_path / f"{filename_mp4}"
    if path_to_json.exists() and force is False:
        print("Skipping video, already treated")
        return (path_to_mp4, json.load(path_to_json.open(mode="r")))

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
    video_metadata = {
        attr: getattr(yt, attr) for attr in dir(yt) if filter_str(getattr(yt, attr))
    }
    video_metadata = flatten_dict(video_metadata)
    # video_metadata.update(all_attributes)

    json.dump(video_metadata, path_to_json.open(mode="w"), indent=4, default=str)
    return (path_to_mp4, video_metadata)


def read_youtube_file_link(file):
    with open(file, "r") as f:
        data = f.readlines()
    return [l.strip().replace('"', "").replace(",", "") for l in data]


def main():
    # Example usage
    mode = "dict_python"
    if mode == "file":
        list_youtube_url = read_youtube_file_link("youtube_list_link.txt")
    else:
        list_youtube_url = [
            "https://www.youtube.com/watch?v=ZWWjjLY2KPo",
            "https://www.youtube.com/watch?v=KNtJGQkC-WI",  # Replace with your YouTube URL,
            "https://www.youtube.com/watch?v=0a1juREe4YQ",
            "https://www.youtube.com/watch?v=d3Un6waXXxE",
            "https://www.youtube.com/watch?v=hHBd9DNOLBg",
            "https://www.youtube.com/watch?v=tTq3h8pfPT0",
            "https://www.youtube.com/watch?v=a5InofcZEHQ",
            "https://www.youtube.com/watch?v=Q7yppe2b6II",
        ]
    DUMP_JSON = False
    REMOVE_MP4 = True
    for youtube_url in list_youtube_url:
        output_dir = Path("mp3_file")
        output_dir.mkdir(exist_ok=True)
        metadata_video_eyed3 = MetadataEYED(output_dir, dump_json=DUMP_JSON)
        path_to_video, video_metadata = download_video(
            youtube_url, output_dir, force=False
        )
        metadata_video_eyed3.from_dict_metadata_update_self_metadata(
            video_metadata, force_replace=False
        )
        artist = metadata_video_eyed3.artist
        title = metadata_video_eyed3.title
        title_music = f"{artist} {title}"
        print(f"{youtube_url} {title_music}")

        if not metadata_video_eyed3.is_metadata_complete(minimal_key=True):
            metadata_video_eyed3.get_metadata_google(f"{artist} GENRE")
        if not metadata_video_eyed3.is_metadata_complete(minimal_key=True):
            metadata_video_eyed3.get_metadata_google(title_music)
        if not metadata_video_eyed3.is_metadata_complete(minimal_key=True):
            metadata_video_eyed3.get_metadata_google(f"{title_music} GENRE")

        if not metadata_video_eyed3.is_metadata_complete(minimal_key=True):
            metadata_video_eyed3.get_metadata_disco(title_music)
        # metadata_video_eyed3.show()
        convert_mp4_to_mp3(path_to_video)
        if REMOVE_MP4:
            if path_to_video.exists():
                path_to_video.unlink()
        metadata_video_eyed3.from_metadata_update_mp3_video(path_to_video)
        print("###")
        # break


def test_2():
    url = "https://www.google.com/search?q=theodort+wayeh+%2B+GENRE"
    # dict_val=MetadataEYED()
    # breakpoint()
    soup_object = src.genius_scrapping.fetch_and_parse_url(url)
    pattern = re.compile(r"kc:/music.*")

    def match_pattern(tag):
        return (
            tag.name == "div"
            and tag.has_attr("data-attrid")
            and pattern.match(tag["data-attrid"])
        )

    # Use the function with find_all to get matching divs
    matching_divs = soup_object.find_all(match_pattern)  # type: ignore
    dict_metadata = {}
    for div in matching_divs:
        data_attrid = div["data-attrid"]
        dict_metadata[data_attrid] = div.text
    print(dict_metadata)


if __name__ == "__main__":
    main()
    # test_2()
