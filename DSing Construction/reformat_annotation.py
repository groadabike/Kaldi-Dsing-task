import argparse
from os.path import join, dirname, exists
from os import makedirs
import json
import re


class MyJsonFile:

    def __init__(self, path):
        self._path_ = path
        self.start_json()

    def write_line(self, start, end, index, sentence, last=False):
        with open(self._path_, 'a') as target_file:
            target_file.write(" " * 4 + "{\n")
            target_file.write(" " * 8 + "\"start\": {},\n".format(start))
            target_file.write(" " * 8 + "\"end\": {},\n".format(end))
            target_file.write(" " * 8 + "\"index\": {},\n".format(index))
            target_file.write(" " * 8 + "\"lyric\": \"{}\"\n".format(sentence.replace('"', '')))
            if last:
                target_file.write(" " * 4 + "}\n")
            else:
                target_file.write(" " * 4 + "},\n")

    def start_json(self):
        with open(self._path_, 'w') as target_file:
            target_file.write("[" + "\n")

    def close_json(self):
        with open(self._path_, 'a') as target_file:
            target_file.write("\n" + "]")


def get_countries(workspace_path):
    countries = []
    with open(join(workspace_path, 'countries.txt')) as cfl:
        for line in cfl:
            countries.append(line.replace('\n', ''))

    return countries


def create_folder(fd):
    if not exists(fd):
        makedirs(fd)


def reformat_annotation(args):
    """

    :param args:
    :return:
    """
    workspace = args.workspace
    print("[English Subset] Reformatting promp lyrics format of English spoken list")
    countries = get_countries(args.workspace)

    for i, country in enumerate(countries, 1):
        print("[English Subset] Processing country {}".format(country))
        with open(join(workspace, 'data', country, "english.txt")) as f:
            songs = f.read().splitlines()

        for song in songs:
            json_target_path = join(workspace, "data", country, country + "Prompts", song.split('/')[-1])
            create_folder(dirname(json_target_path))
            json_target = MyJsonFile(json_target_path)
            process_success, comment = damp_lyrics_transform(song, json_target)
            if not process_success:
                print(song, ' - ', comment)


def damp_lyrics_transform(filepath, json_writer):
    """
    Function to transform the annotation of DAMP 300x30x2 to Chime3 style.


    :param filepath: Path to annotation file
    :param json_writer: An JsonFile object.
    :return: True if annotations transform / False if error.
    """

    # Open :filepath: file
    with open(filepath, 'r') as data_file:
        try:
            data = json.load(data_file)

            # Test if is not an empty file
            if len(data) > 1:
                t0 = data[0]['t']  # Start time first element
                utt = data[0]['l']  # Utterance first element
                utt = re.sub("[\[\<].*?[\>\]]", "", utt)   # Delete comments in [] and <>
                # Iteration from item index 1 to len(data)
                for i in range(1, len(data)):
                    t1 = data[i]['t']  # --> Start time next utterance == End time current utterance
                    if t1 > t0:
                        if i == len(data) - 1:  # --> Check if is the last utterance to write
                            json_writer.write_line(t0, t1, i, utt, False)
                            json_writer.write_line(t1, t1 + 10, i + 1, data[i]['l'], True)
                        else:  # --> It is not the last utterance
                            json_writer.write_line(t0, t1, i, utt, False)

                        t0 = t1
                        utt = data[i]['l']
                        utt = re.sub("[\[\<].*?[\>\]]", "", utt)
            else:
                return False, 'empty'  # --> Error, original file is empty

            json_writer.close_json()
        except json.decoder.JSONDecodeError:
            # catch error when json has unknown characters and close the json_writer
            json_writer.close_json()
            return False, 'Unknown string'  # --> Error, Unknown character, decoder error

        return True, 'Success'  # --> Success, Nice job


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Convert DAMP prompts format to Chime3 annotation format'
    )

    parser.add_argument("workspace", type=str, help="Path where the output files will be saved")
    parser.add_argument('--version', action='version',
                        version='%(prog)s 1.0')

    args = parser.parse_args()

    reformat_annotation(args)

