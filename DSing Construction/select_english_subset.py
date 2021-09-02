import argparse
from os.path import join, exists, dirname
from os import makedirs, listdir
import subprocess
import json
import pycld2
from polyglot.detect import Detector, base
import logging
# To silence the logger.warnings from polyglot module
logger = logging.getLogger("polyglot")
# only log really bad events
logger.setLevel(logging.ERROR)


def get_countries(workspace_path):
    countries = []
    with open(join(workspace_path, 'countries.txt')) as cfl:
        for line in cfl:
            countries.append(line.replace('\n', ''))

    return countries


def list2file(path, data):
    create_folder(dirname(path))
    with open(path, "w") as file:
        for item in data:
            file.write("{}\n".format(item))


def create_folder(fd):
    if not exists(fd):
        makedirs(fd)


def check_english_language(filepath):
    subprocess.call(['sed', '-i', '/.*un-termimated note on.*/d', filepath])
    subprocess.call(['sed', '-i', '/.*found extra tempo event at beginning of file.*/d', filepath])
    tolerance = 0
    noteng = 0
    one_word = 0
    total_words = 0
    try:
        with open(filepath) as data_file:
            data = json.load(data_file)
            for i in range(0, len(data)):
                try:
                    utterance = data[i]['l']
                    if len(utterance) > 0:
                        if len(utterance.split()) > 1:
                            total_words += len(utterance.split())
                            detector = Detector(utterance, quiet=True)
                            if detector.languages[0].code in ['en']:
                                tolerance += 1
                            else:
                                noteng += 1
                        else:
                            one_word += 1
                except pycld2.error:
                    noteng += 1
                    one_word += 1
                except base.UnknownLanguage:
                    noteng += 1
                    one_word += 1

    except json.decoder.JSONDecodeError:
        return False, False

    if tolerance > noteng and tolerance >= noteng * 1.3:
        return True, False
    else:
        if one_word >= total_words * .5:
            return False, True
        else:
            return False, False


def classify_songs(path):
    english = []
    nonenglish = []
    one_word = []
    songs = [f for f in listdir(path)]
    for song in songs:
        song_path = join(path, song)
        eng, one = check_english_language(song_path)
        if eng:
            english.append(song_path)
        else:
            if one:
                one_word.append(song_path)
            else:
                nonenglish.append(song_path)
    return english, nonenglish, one_word


def select_english_subset(args):
    """
    Process Damp Sing!300x30x2 database and select an English subset to be used in
    Lyrics Transcription on monophonic singing
    :param args: list of arguments
    :return:
    """
    print("[English Subset] Starting separate arrangements by country...")
    workspace = args.workspace
    countries = get_countries(args.workspace)

    for country in countries:
        english, nonenglish, one_word = classify_songs(join(workspace, "data", country, country + 'Lyrics'))
        list2file(join(workspace, "data", country, "nonenglish.txt"), nonenglish)
        list2file(join(workspace, "data", country, "english.txt"), english)
        list2file(join(workspace, "data", country, "one_word_error.txt"), one_word)
        print("[English Subset] {} - English = {}, Non-English = {}, One Word = {}".
              format(country, len(english), len(nonenglish), len(one_word)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("workspace", type=str, help="Path where the output files will be saved")

    args = parser.parse_args()
    select_english_subset(args)
