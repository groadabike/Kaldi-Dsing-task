from bs4 import BeautifulSoup
import requests
from os.path import join, dirname, exists
from os import listdir, makedirs
import argparse
from user_agent import generate_user_agent
import json


def get_countries(workspace_path):
    countries = []
    with open(join(workspace_path, 'countries.txt')) as cfl:
        for line in cfl:
            countries.append(line.replace('\n', ''))
    return countries


def download_lyrics(args):
    """
    Function that transfrom the one word/syllable annotation to sentence level
    :param args:
    :return:
    """
    print("[English Subset] Downloading sentence-level annotation of lyrics listed on file word_level.txt")
    workspace = args.workspace
    countries = get_countries(args.workspace)

    metadata_with_errors = []

    for country in countries:
        print("[English Subset] Recovering from country {}".format(country))
        word_level_list = file2list(join(workspace, "data", country, "word_level.txt"))
        path_downloaded_lyrics = join(workspace, "DownloadLyric")
        create_folder(path_downloaded_lyrics)
        recovered_lyrics = [f for f in listdir(path_downloaded_lyrics) if f.endswith('.txt')]

        for word_level in word_level_list:
            headers = {'User-Agent': generate_user_agent(device_type="desktop", os=('mac', 'linux'))}
            # Arrangement ID
            arrangement = word_level.split('.')[0]

            # Just download the lyrics on the first occurrence, no per country
            if arrangement + ".txt" not in recovered_lyrics:
                # Metadata file path
                metadata_path = join(workspace, 'data', country, country + "ArrangementMeta", arrangement + ".txt")

                # Read metadata file for current word_level prompt
                try:
                    metadata = dict(map(str, x.split(':', 1)) for x in file2list(metadata_path))
                except ValueError:
                    # Metadata file has format errors
                    # create empty dict
                    if arrangement not in metadata_with_errors:
                        metadata_with_errors.append(arrangement)
                    metadata = {}

                # Catch error if title is not in Metadata
                try:
                    title = format_text(metadata['Arrangement title'].lstrip())
                except KeyError:
                    if arrangement not in metadata_with_errors:
                        metadata_with_errors.append(arrangement)
                    title = ""

                # Catch error if artist is not in Metadata
                try:
                    artist = format_text(metadata['Arrangement artist'].lstrip())
                except KeyError:
                    if arrangement not in metadata_with_errors:
                        metadata_with_errors.append(arrangement)
                    artist = ""

                url = 'https://www.smule.com/song/{}-{}-karaoke-lyrics/{}/arrangement'.\
                    format(artist, title, arrangement)

                # try to get the lyrics several time in case of errors from the network connection
                attempts = 5
                while attempts > 0:
                    response = requests.get(url, timeout=5, headers=headers)
                    html = response.content
                    soup = BeautifulSoup(html, "html.parser")
                    mydiv = soup.find_all("script")#, {"class": "_1frabae"})
                    if len(mydiv) < 1:
                        attempts -= 1
                    else:
                        attempts = 0

                if len(mydiv) < 1:
                    mydiv = soup.find_all("div", {"class": "column error-gone"})
                    print("[WARNING] can't find {}".format(url))
                    for div in mydiv:
                        path_to_error_download = join(workspace, "data", country, "error_download.txt")
                        with open(path_to_error_download, "a") as error_file:
                            error_file.write("arrangement: {}\terror: {}\tdetails: {}".format(
                                arrangement, div.h1.get_text(), div.p.get_text()
                            ))
                else:
                    for div in mydiv:
                        lyric_text = div.get_text()#.replace("\n","")#.split("\n")
                        if "<p>" in lyric_text:
                            lyric = lyric_text[lyric_text.find("<p>")+3:lyric_text.find("</p>")-4].split("<br>")
                            path_new_lyric = join(path_downloaded_lyrics,
                                                  arrangement + ".txt")
                            print("[Recover lyric] url {} - > save in {}".format(url, path_new_lyric))
                            list2file(path_new_lyric, lyric)
                            break



def format_text(text):
    text = text.lower()
    symbols2dash = [" ", ",", ".", "!"]
    symbols2none = ["'", "&", "(", ")", "?"]
    for symbol in symbols2none:
        text = text.replace(symbol, "")
    text = text.lstrip().rstrip()
    for symbol in symbols2dash:
        text = text.replace(symbol, "-")
    text = text.replace("--", "-")

    return text


def create_folder(fd):
    if not exists(fd):
        makedirs(fd)


def clean_text(text):
    if "&#39;" in text:
        text = text.replace("&#39;", "'")
    if "&quot;" in text:
        text = text.replace("&quot;", '"')
    return(text)


def list2file(path, data):
    create_folder(dirname(path))
    with open(path, "w") as file:
        for item in data:
            file.write("{}\n".format(clean_text(item)))


def file2list(filepath):
    """
    Read a file and return a list
    :param file:
    :return:
    """
    outlist = []
    with open(filepath) as file:
        for line in file:
            outlist.append(line.replace('\n', ''))
    return outlist


if __name__ == '__main__':
    """
       Script that attempts to recover sentence-level lyrics from Smule website
    """
    parser = argparse.ArgumentParser(
        description='From the list of word-level prompts lyrics tray'
                    ' to recover the lyrics as appears in the Smule website'
    )

    parser.add_argument("workspace", type=str, help="Path to Workspace")
    parser.add_argument('--version', action='version',
                        version='%(prog)s 1.0')

    args = parser.parse_args()

    # Download the lyrics
    download_lyrics(args)
