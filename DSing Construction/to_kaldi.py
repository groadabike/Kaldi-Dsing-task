from os import makedirs
from os.path import join, exists, dirname
import argparse
import json
import subprocess
import re


class Kaldi_Set:
    def __init__(self, type, data_path, wavscp_version=0):
        self.wavscp_version = wavscp_version
        self.type = type
        self.spk2gender = []
        self.textfile = []
        self.wavscp = []
        self.segments = []
        self.utt2spk = []
        self.path = join(data_path, self.type)
        create_folder(self.path)

    def add_utterance(self, data):
        insensitive_none = re.compile(re.escape('none'), re.IGNORECASE)
        correct_sentence = 0
        if 'wrong' not in data:
            correct_sentence = 1

        elif not data['wrong']:
            correct_sentence = 1

        if data.get("transcription", data["lyric"]).strip() == "":
            correct_sentence = 0

        if correct_sentence > 0:
            #  Add New Speaker
            s2g = "{} {}".format(insensitive_none.sub('', data["speaker"]),
                                 insensitive_none.sub('', data["gender"]))
            if s2g not in self.spk2gender:
                self.spk2gender.append(s2g)

            # Get Transcription or lyrics if not exist
            self.textfile.append("{} {}".format(insensitive_none.sub('', data["track_id"]),
                                                data.get("transcription", data["lyric"]).upper().strip()))

            # wav.scp list
            wavfile = join("wav", data["wavfile"].split('sing_300x30x2/')[-1])
            wavfile_id = data["wavfile"].split('/')[-1].split('.')[0]
            if self.wavscp_version == 0:
                #  Each sentence is already a WAV file
                self.wavscp.append("{} wav/{}".format(insensitive_none.sub('', data["track_id"]),
                                                      insensitive_none.sub('', data["track_segment"])))

            elif self.wavscp_version == 1:
                #  Use sox in wav_scp
                self.wavscp.append("{} sox {} -G -t wav -r 16000 -c 1 - remix 1 | ".format(
                    insensitive_none.sub('', wavfile_id), wavfile))

            else:
                #  use ffmpeg version
                self.wavscp.append("{} ffmpeg -loglevel quiet -i wav/{} -f wav -ar 16000 -acodec pcm_s16le -ac 1 - | ".
                                   format(insensitive_none.sub('', wavfile_id), wavfile))

            if self.wavscp_version > 0:
                self.segments.append("{} {} {} {}".format(insensitive_none.sub('', data["track_id"]),
                                                          insensitive_none.sub('', wavfile_id),
                                                          data["start"], data["end"]))

            # utt2spk list
            self.utt2spk.append("{} {}".format(insensitive_none.sub('', data["track_id"]),
                                               insensitive_none.sub('', data["speaker"])))

    def save_files(self):
        list2file(join(self.path, "spk2gender"), sorted(self.spk2gender))
        list2file(join(self.path, "text"), sorted(self.textfile))
        list2file(join(self.path, "wav.scp"), sorted(self.wavscp))
        list2file(join(self.path, "utt2spk"), sorted(self.utt2spk))
        if self.wavscp_version > 0:
            list2file(join(self.path, "segments"), sorted(self.segments))


def list2file(outfile, list_data):
    '''
    Saves a list into a file
    :param list_data: list
    :param outfile: path to output file
    '''
    create_folder(dirname(outfile))
    list_data = list(set(list_data))
    with open(outfile, "w") as f:
        for line in list_data:
            f.write("{}\n".format(line))


def create_folder(fd):
    if not exists(fd):
        makedirs(fd)


def read_json(filepath):
    try:  # Read the json
        with open(filepath) as data_file:
            data = json.load(data_file)
    except json.decoder.JSONDecodeError:  # Json has an extra first line. Error when was created
        print(filepath)
        subprocess.call(['sed', '-i', '/.*found extra tempo event at beginning of file.*/d', filepath])
        with open(filepath) as data_file:
            try:
                data = json.load(data_file)
            except:
                data = []
                pass

    return data


def to_kaldi(workspace, metadatafile, type, setname):
    """
    Preparing spk2gender wav.scp text utt2spk
    :param workspace:
    :param metadatafile:
    :return:
    """
    # Read metadata
    metadata = read_json(join(workspace, metadatafile))

    # This variable just validate that data with the selected type exist in the file
    # Is a flag to create the object of Kaldi_Set class
    control_data_exist = 0
    for data in metadata:
        # spk2gender list
        try:
            if data["data_set"] == type:
                if control_data_exist == 0:
                    # wavscp_version == 0 -> each utterance already in independent file
                    # wavscp_version == 1 -> wavscp use sox and segment file is created
                    # wavscp_version == 2 -> wavscp use ffmpeg and segment file is created
                    data_set = Kaldi_Set(setname, join(workspace, "kaldi", "data"), wavscp_version=1)
                    control_data_exist = 1
                # Add utterance
                data_set.add_utterance(data)
        except KeyError:
            print("Error in segment {}".format(data['track_id']))

    if control_data_exist == 1:
        # save files
        data_set.save_files()
    else:
        print('No utterance of type {} was found in file {}'.format(type, dirname(metadatafile)))


def main(args):
    """
    Main Function
    :param workspace: path to working space
    :param wav_dir_name: directory name for wav files in workspace
    :return:
    """
    workspace = args.workspace
    metadatafile = args.metadatafile
    type = args.type
    setname = args.setname
    # Set test set

    to_kaldi(workspace, metadatafile, type, setname)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("workspace", type=str, help="Path where the output files will be saved")
    parser.add_argument("metadatafile", type=str, help="Path to Metadata file")
    parser.add_argument("type", type=str, help="Type name options: train, dev or test")
    parser.add_argument("setname", type=str, help="Name to save the set")

    args = parser.parse_args()
    main(args)
