from os import listdir, makedirs
from os.path import join, isfile, exists, dirname
import argparse
import json
import string
from num2words import num2words


def get_countries(workspace_path):
    countries = []
    with open(join(workspace_path, 'countries.txt')) as cfl:
        for line in cfl:
            countries.append(line.replace('\n', ''))

    return countries


def clean_text(text):
    punctuation = [x for x in string.punctuation if x != "'"]
    table = str.maketrans({key: " " for key in punctuation})
    text = "".join(text).replace("’", "'")
    text = text.translate(table)
    text = " ".join(text.split())
    text = "".join([x if ord(x) < 128 else ' ' for x in text])
    text2 = []
    for char in text:
        try:
            if char.isdigit():
                text2.append(num2words(char))
            else:
                text2.append(char)
        except TypeError:
            text2.append(" ")

    return text.upper()


def file2list(path):
    """
    Funtion that read a file and returned as a list.
    :param path: full path to the file
    :return: list
    """

    data = []
    with open(path) as file:
        for line in file:
            data.append(line.replace("\n", ""))
    return data


def create_metadata(workspace, database, wav_dir_name, metadatafile):
    """
    Function that create a JSON file with the metadata of each utterance.
    :param workspace: directory of work space
    :param wav_dir_name: suffix of the wav directory
    :param metadatafile: name of the metadata file
    :return:
    """

    # Read files with list of singers for train, test and val
    # and save it into a dict
    spk2set = {}
    for spk in ["train", "test", "dev"]:
        set = file2list(join(workspace, "kaldi", "input", spk + "_spk"))
        for item in set:
            spk2set[item.split('-')[-1]] = spk
    # path to the English subset and read countries
    processed_damp_path = join(workspace, "data")
    countries = get_countries(args.workspace)
    output_json = []

    # Read utterance per country and generate the metadata
    for country in countries:
        lyricsrefined = [f for f in listdir(join(workspace, "data", country, country + "LyricsRefined"))]
        for lrefined in lyricsrefined:

            split_utt_dash = lrefined.split("-")
            arrangement = split_utt_dash[0]
            performance_id = split_utt_dash[1]
            gender = split_utt_dash[3]

            speaker = split_utt_dash[4].split('.')[0]

            with open(join(workspace, "data", country, country + "LyricsRefined", lrefined)) as lyric_file:
                json_string = lyric_file.read()

                json_string = json.loads(json_string)
                for item in json_string:
                    index = int(item["index"])
                    segment_lyric = clean_text(item["lyric"])
                    start = item["start"]
                    end = item["end"]
                    utt = "{}-{}-{}-{}-{}-{:03d}.wav".format(arrangement, performance_id, country, gender,speaker, index)
                    try:
                        if end - start >= 1:
                            output_json.append({"wavfile" : "{}/{}/{}Vocals/{}-{}-{}-{}-{}.m4a".format(database, country, country, arrangement, performance_id, country, gender, speaker),
                                                "track_segment": join(country, country + wav_dir_name, utt),
                                                "track_id": "{}-{}-{}-{}-{}-{:03}".format(speaker, arrangement, performance_id, country, gender, index),
                                                "arrangement": arrangement,
                                                "performance": performance_id,
                                                "country": country,
                                                "gender": gender.lower(),
                                                "speaker": speaker,
                                                "data_set": spk2set[speaker],
                                                "start": start,
                                                "end": end,
                                                "index": int(index),
                                                "lyric": segment_lyric.replace("\n", "")})
                    except KeyError:
                        pass

    save_json(join(workspace, metadatafile), output_json)
    return output_json


def create_metadata_old(workspace, database, wav_dir_name, metadatafile):
    """
    Function that create a JSON file with the metadata of each utterance.
    :param workspace: directory of work space
    :param wav_dir_name: suffix of the wav directory
    :param metadatafile: name of the metadata file
    :return:
    """

    # Read files with list of singers for train, test and val
    # and save it into a dict
    spk2set = {}
    for spk in ["train", "test", "dev"]:
        set = file2list(join(workspace, "kaldi", "input", spk + "_spk"))
        for item in set:
            spk2set[item.split('-')[-1]] = spk
    # path to the English subset and read countries
    processed_damp_path = join(workspace, "data")
    countries = get_countries(args.workspace)
    output_json = []

    # Read utterance per country and generate the metadata
    for country in countries:
        utterances = [f for f in listdir(join(processed_damp_path, country, country + wav_dir_name))
                      if f.split(".")[-1] == "wav"]
        for utt in utterances:
            split_utt_dash = utt.split("-")
            arrangement = split_utt_dash[0]
            performance_id = split_utt_dash[1].replace('None', '')
            gender = split_utt_dash[3].replace('None', '')

            speaker = split_utt_dash[4]
            segment = split_utt_dash[5].split(".")[0]  # Exclude  extension .wav

            with open(join(workspace, "data", country, country + "LyricsRefined", "{}-{}-{}-{}-{}.json".format(
                                    arrangement, performance_id, country, gender, speaker))) as lyric_file:
                json_string = lyric_file.read()

                json_string = json.loads(json_string)
                for item in json_string:
                    if item["index"] == int(segment):
                        segment_lyric = clean_text(item["lyric"])
                        start = item["start"]
                        end = item["end"]
                        break

            if end-start > 1:
                output_json.append({"wavfile" : "{}/{}Vocals/{}-{}-{}-{}-{}.m4a".format(country, country, arrangement, performance_id, country, gender, speaker),
                                    "track_segment": join(workspace, 'data', country, country + wav_dir_name, utt),
                                    "track_id": "{}-{}-{}-{}-{}-{}".format(speaker, arrangement, performance_id, country, gender, segment.zfill(3)),
                                    "arrangement": arrangement,
                                    "performance": performance_id,
                                    "country": country,
                                    "gender": gender.lower(),
                                    "speaker": speaker,
                                    "data_set": spk2set[speaker],
                                    "start": start,
                                    "end": end,
                                    "index": int(segment),
                                    "lyric": segment_lyric.replace("\n", "")})

    save_json(join(workspace, metadatafile), output_json)
    return output_json


def save_json(filepath, content):
    with open(filepath, 'w') as outfile:
        json.dump(content, outfile, indent=4)


def main(args):
    """
    Main Function
    :param workspace: path to working space
    :param wav_dir_name: directory name for wav files in workspace
    :return:
    """
    workspace = args.workspace
    database = args.database

    if not isfile(join(workspace, "metadata.json")):
        _ = create_metadata(workspace, database, "Vocals", "metadata.json")
    else:
        print("Metadata {} exist, skipping step".format(join(workspace, "metadata.json")))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("workspace", type=str, help="Path where the output files will be saved")
    parser.add_argument('database', type=str,
                        help='Path to the original DAMP300x30x2')

    args = parser.parse_args()
    main(args)
