import json
import argparse
from os.path import join, exists
import subprocess
from os import makedirs, listdir
import re
import hashlib


class DataSet:
    def __init__(self, name, workspace, db_path):
        self.sentences = []
        self.spk2gender = []
        self.text = []
        self.workspace = join(workspace, name)
        self.db_path = db_path

    def add_utterance(self, utt, recording):

        text = utt["text"]
        arrangement, performance, country, gender, user = recording[:-4].split("-")

        # the following mapping is necessary for errors in gender in country IN
        insensitive_none = re.compile(re.escape('none'), re.IGNORECASE)

        gender = insensitive_none.sub('', utt["gender"])
        spk = "{}{}".format(insensitive_none.sub('', gender).upper(), insensitive_none.sub('', user))

        rec_id = recording[:-4]
        utt_id = "{}-{}-{}-{}-{}-{:03}".format(spk, arrangement, performance, country, gender.upper(), utt["index"])

        start = utt["start"]
        end = utt["end"]

        self._add_sentences(country, rec_id, utt_id, start, end)
        self._add_spk2gender(spk, gender)
        self._add_text(utt_id, text)

    def _add_sentences(self, country, rec_id, utt_id, start, end):

        self.sentences.append("sox {}/{}/{}Vocals/{}.m4a -G -t wav -r 16000 -c 1 - remix 1 | "
                              "sox - {}/audio/{}.wav trim {:.3f} ={:.3f} ".format(
            self.db_path, country, country, rec_id,
            self.workspace, utt_id,
            start, end))

    def _add_spk2gender(self, spk, gender):
        self.spk2gender.append("{} {}".format(spk, gender))

    def _add_text(self, utt_id, text):
        self.text.append("{} {}".format(utt_id, text))

    def _list2file(self, outfile, list_data):
        list_data = list(set(list_data))
        with open(outfile, "w") as f:
            for line in list_data:
                f.write("{}\n".format(line))

    def save(self):
        if not exists(self.workspace):
            makedirs(self.workspace)
        self._list2file(join(self.workspace, "spk2gender"), sorted(self.spk2gender))
        self._list2file(join(self.workspace, "text"), sorted(self.text))

        if not exists(join(self.workspace, "audio")):
            makedirs(join(self.workspace, "audio"))
        for s in self.sentences:
            a = subprocess.run(s, capture_output=True, shell=True)
            warnings = 1
            if 'WARN' in str(a.stderr):
                print("WARNING {}".format(warnings))
                print(s)
                print(str(a.stderr))
                print("\n-------\n")
                warnings += 1


def read_json(filepath):
    try:  # Read the json
        with open(filepath) as data_file:
            data = json.load(data_file)
    except json.decoder.JSONDecodeError:  # Json has an extra first line. Error when was created
        data = []

    return data


def map_rec2chec(db_path, countries):
    """
    Method read all the original audio tracks and create a dict  {<checksum>: <recording>}
    :param db_path: string, path to root of DAMP Sing!
    :return: dict
    """
    rec2chec = {}
    for country in countries:
        recordings = [f for f in listdir(join(db_path, country, country + "Vocals")) if f.endswith(".m4a")]
        for record in recordings:
            rec2chec[hashlib.md5(open(join(db_path, country, country + "Vocals", record), 'rb').read()).hexdigest()] = record

    return rec2chec


def main(args):
    db_path = args.db_path
    workspace = args.workspace
    dset = args.dset
    utts_path = "../DSing Kaldi Recipe/dsing/s5/conf/{}.json".format(dset)

    countries = ["GB"]
    countries += ["US", "AU"] if dset in ["train3", "train30"] else []
    countries += ['AE', 'AR', 'BR', 'CL', 'CN', 'DE', 'ES', 'FR', 'HU',
                  'ID', 'IN', 'IQ', 'IR', 'IT', 'JP', 'KR', 'MX', 'MY',
                  'NO', 'PH', 'PT', 'RU', 'SA', 'SG', 'TH', 'VN', 'ZA'] if dset in ["train30"] else []

    performances = map_rec2chec(db_path, countries)
    utterances = read_json(utts_path)
    dataset = DataSet(dset, workspace, db_path)

    for utt in utterances:
        dataset.add_utterance(utt, performances[utt["wavfile"]])

    dataset.save()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace", type=str, help="Path where the output files will be saved")
    parser.add_argument("db_path", type=str, help="Path to DAMP 300x30x2 database")
    parser.add_argument("dset", type=str, help="Name of the dataset")

    args = parser.parse_args()
    main(args)

# python prepare_data.py /media/gerardo/SoloSinging/savedata /media/gerardo/SoloSinging/DAMP/sing_300x30x2/ train30
