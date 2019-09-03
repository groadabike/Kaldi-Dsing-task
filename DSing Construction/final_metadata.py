from os import listdir
from os.path import join
import argparse
import json
import csv
import hashlib


class Metadata():
    def __init__(self, db_path, type):
        self.utterance = []
        self.type = type
        self.db_path = db_path

    def add_utterance(self, utt, corrector):
        new_utt = {}
        text = utt.get("transcription", utt["lyric"]).upper().strip()
        if text == "":
            return

        if self.type != "wrong":
            # Add train element in utterance_level
            wavfile = hashlib.md5(open(join(self.db_path, utt["wavfile"]), 'rb').read()).hexdigest()
            #wavfile = hashlib.md5(utt["wavfile"].split("/")[-1].encode('utf-8')).hexdigest()
            new_utt["wavfile"] = wavfile
            new_utt["index"] = utt["index"]
            new_utt["start"] = float("{0:.3f}".format(float(utt["start"])))
            new_utt["end"] = float("{0:.3f}".format(float(utt["end"])))
            new_utt["text"] = text
            new_utt["gender"] = utt["gender"]

            if "train" not in self.type:
                for correct_item in corrector:
                    if utt["wavfile"].split("/")[-1] == correct_item["performance"]:
                        if int(correct_item["selected"]) == 1:
                            new_utt["gender"] = correct_item["true_gender"].lower()
                            break
                        else:
                            return
        self.utterance.append(new_utt)

    def add_raw_utterance(self, utt):
        self.utterance.append(utt)

    def save_metadata(self, filepath):
        with open(join(filepath, self.type + ".json"), 'w') as outfile:
            json.dump(self.utterance, outfile, indent=4)

    def save2csv(self, filepath, fieldsname=[]):
        fnames = self.utterance[0].keys() if len(fieldsname) == 0 else fieldsname
        utt = []
        for item in self.utterance:
            utt.append(",".join(str(e) for e in list(item.values())))
        utt = list(set(utt))
        with open(join(filepath, self.type + ".csv"), 'w') as outfile:
            outfile.write(",".join(list(fnames)) + "\n")
            for line in utt:
                outfile.write(line + "\n")


            #outfile.writelines(",".join(list(set([list(d.values()) for d in self.utterance]))))

        #     w = csv.DictWriter(outfile, fieldnames=fnames)
        #     w.writeheader()
        #     w.writerows(self.utterance)


def read_json(filepath):
    try:  # Read the json
        with open(filepath) as data_file:
            data = json.load(data_file)
    except json.decoder.JSONDecodeError:  # Json has an extra first line. Error when was created
        data = []

    return data


def csv2json(path):
    with open(path, 'r') as f:
        reader = csv.DictReader(f)
        return json.loads(json.dumps([row for row in reader]))


def main(args):
    db_path = args.db_path
    workspace = args.workspace
    metadata_path = args.metadata
    devgold_path = args.devgold
    testgold_path = args.testgold
    corrector_path = args.corrector

    metadata = read_json(metadata_path)
    devgold = read_json(devgold_path)
    testgold = read_json(testgold_path)
    corrector = csv2json(corrector_path)

    train1 = Metadata(db_path, "train1")
    train3 = Metadata(db_path, "train3")
    train30 = Metadata(db_path, "train30")
    dev = Metadata(db_path, "dev")
    test = Metadata(db_path, "test")
    wrong = Metadata(db_path, "wrong")
    res_dev = Metadata(db_path, "res_dev")
    res_test = Metadata(db_path, "res_test")

    extended_fieldnames = ["arrangement", "country", "data_set", "end", "gender", "gold", "index", "lyric",
        "old_track_id", "performance", "reason_discarded", "speaker", "start",  "track_id", "track_segment",
        "transcription", "utt_selected", "wavfile", "wrong"]
    for item in metadata:

        if item['data_set'] == 'train':
            if item["country"] == "GB":
                train1.add_utterance(item, corrector)
                train3.add_utterance(item, corrector)
            elif item["country"] in ["US", "AU"]:
                train3.add_utterance(item, corrector)
            train30.add_utterance(item, corrector)

        elif item['data_set'] == 'dev':
            gold = False
            good_sentence = True
            new_item = item
            for dg in devgold:
                if dg["old_track_id"] == new_item["track_id"]:
                    # tg["old_track_id"] is a track id with the same structure than rec_id
                    # track_id start with <gender><spk>...
                    if "selected" in dg:
                        if dg["selected"]:
                            gold = True
                            new_item = dg

                    if "wrong" in dg:
                        if dg["wrong"]:
                            good_sentence = False
                            wrong.add_raw_utterance(new_item)
                            break
                    else:
                        break

            if gold:
                dev.add_utterance(new_item, corrector)
            elif good_sentence:
                res_dev.add_raw_utterance(item)

        elif item['data_set'] == 'test':
            gold = False
            good_sentence = True
            new_item = item
            for tg in testgold:
                if tg["old_track_id"] == new_item["track_id"]:
                    # tg["old_track_id"] is a track id with the same structure than rec_id
                    # track_id start with <gender><spk>...
                    if "selected" in tg:
                        if tg["selected"]:
                            gold = True
                            new_item = tg

                    if "wrong" in tg:
                        if tg["wrong"]:
                            good_sentence = False
                            wrong.add_raw_utterance(new_item)
                            break
                    else:
                        break

            if gold:
                test.add_utterance(new_item, corrector)
            elif good_sentence:
                res_test.add_raw_utterance(item)

    train1.save_metadata(workspace)
    train1.save2csv(workspace)

    train3.save_metadata(workspace)
    train3.save2csv(workspace)

    train30.save_metadata(workspace)
    train30.save2csv(workspace)

    dev.save_metadata(workspace)
    dev.save2csv(workspace)

    test.save_metadata(workspace)
    test.save2csv(workspace)

    wrong.save_metadata(workspace)
    wrong.save2csv(workspace, extended_fieldnames)

    res_dev.save_metadata(workspace)
    res_dev.save2csv(workspace, extended_fieldnames)

    res_test.save_metadata(workspace)
    res_test.save2csv(workspace, extended_fieldnames)


if __name__ == '__main__':
    """
    db_path = Path to DAMP Sing300x30x2 database, should be the path to the countries directories
    workspace = where the output will be saved
    metadata = file created by create_metadata.py
    devgold = the annotated file for the gold dev
    textgold = the annotated file for the test gold
    corrector = manually created file with the discarded songs and corrected gender for test and dev 
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("workspace", type=str, help="Path where the output files will be saved")
    parser.add_argument("db_path", type=str, help="Path to DAMP 300x30x2 database")
    parser.add_argument('metadata', type=str, help='Path to full metadata')
    parser.add_argument('devgold', type=str, help='Path to dev gold json')
    parser.add_argument('testgold', type=str, help='Path to test gold json')
    parser.add_argument('corrector', type=str, help="Path to the correct gender for test and dev")

    args = parser.parse_args()
    main(args)

# use python final_metadata.py /media/gerardo/SoloSinging/DAMP/sing_300x30x2
# /media/gerardo/SoloSinging/DAMP/sing_300x30x2
# /media/gerardo/SoloSinging/DSing1
# /media/gerardo/SoloSinging/DSing1/metadata.json
# /media/gerardo/SoloSinging/DSing/Gold/dev_gold.json
# /media/gerardo/SoloSinging/DSing/Gold/test_gold.json
# /media/gerardo/SoloSinging/DSing/Clean_DAMP/performances.csv