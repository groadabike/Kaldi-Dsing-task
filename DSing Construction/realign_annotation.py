from os.path import join, dirname, exists
from os import listdir, makedirs
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
import json
import argparse
import gc


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


def realign_lyrics(args):
    db_path = args.database_path
    workspace = args.workspace
    pad2ann = args.pad
    #  List of countries in Dataset
    countries = get_countries(args.workspace)

    for country in countries:
        error_list = []
        print("[English Subset] Processing country {}".format(country))
        #  List of English Lyrics per country based on the lyrics saved in workspace
        country_lyrics_path = join(workspace, "data", country, country + "Prompts")
        lyrics = [f for f in listdir(country_lyrics_path) if f.endswith('.json')]

        #  Path with the vocal tracks in current country
        country_vocal_path = join(db_path, country, country + 'Vocals')

        for lyric in lyrics:
            gc.collect()
            #  Iterpretations of current song
            song_id = lyric.split('.')[0]
            songs = [join(country_vocal_path, f) for f in listdir(country_vocal_path) if song_id in f]

            #  Iterate by songs to create refine start-end time per utterance
            for track_path in songs:
                #  Non Silence (assumed singing) in track
                singing_segments = [[x / 1000, y / 1000] for x, y in
                                    detect_voice(track_path, min_silence_len=20, silence_thresh=-40)] # good between 32 and 40

                #  Original Activation Annotation
                with open(join(country_lyrics_path, lyric), 'r') as infile:
                    json_string = infile.read()
                try:
                    activation_segments = json.loads(json_string)
                except json.decoder.JSONDecodeError:
                    continue

                # Get refined utterance - lyrics
                refined = refine_activation(activation_segments, singing_segments, track_path.split('/')[-1].split('.')[0])
                if len(refined) > 0:
                    json_target_path = join(workspace, "data", country, country + "LyricsRefined", track_path.split('/')[-1].split('.')[0] + '.json')
                    create_folder(dirname(json_target_path))
                    json_target = MyJsonFile(json_target_path)
                    for id, line in enumerate(refined):
                        if id + 1 < len(refined):
                            json_target.write_line(line[0], line[1], line[3], line[2].replace('\n', ''))
                        else:
                            json_target.write_line(line[0], line[1], line[3], line[2].replace('\n', ''), last=True)
                    json_target.close_json()
                else:
                    error_list.append(track_path)
        print("...error on {} tracks".format(len(error_list)))
        list2file(error_list, join(workspace, "data", country, "realign_error_list.txt"))
    return True


def create_folder(fd):
    if not exists(fd):
        makedirs(fd)


def list2file(list_data, outfile):
    """
    Saves a list into a file
    :param list_data: list
    :param outfile: path to output file
    """
    create_folder(dirname(outfile))
    with open(outfile, "w") as f:
        for line in list_data:
            f.write("{}\n".format(line))


def file2list(filepath):
    """
    Read a file and return a list
    :param file:
    :return:
    """
    outlist = []
    with open(filepath) as file:
        for line in file:
            outlist.append(line.replace('\n',''))
    return outlist


def match_target_amplitude(sound, target_dBFS):
    change_in_dBFS = target_dBFS - sound.dBFS
    return sound.apply_gain(change_in_dBFS)


def detect_voice(audio_track, min_silence_len=10, silence_thresh=-40):
    song = AudioSegment.from_file(audio_track)

    #  11th March add this normalization to -25 dBFS
    song = match_target_amplitude(song, -25.0)

    not_silence_ranges = detect_nonsilent(song, min_silence_len=min_silence_len, silence_thresh=silence_thresh)
    not_silence = [[a, b] for a, b in not_silence_ranges if b-a >= 100]
    return not_silence


def refine_activation(activation, singing, track, pad2ann=0.0):
    refined = overlap(activation, singing, track, pad2ann)
    return refined


def overlap(annotation_dict, singing, track, pad2ann=0.0):
    annotation = [[item['start'], item['end'], item['index'], item['lyric'].replace('\n', '')] for item in
                  annotation_dict]

    it_ann = iter(annotation)
    it_sing = iter(singing)
    try:
        ann, sing = next(it_ann), next(it_sing)
    except StopIteration:
        return []

    sing_fix = sing
    ann_fix = ann
    refined = []
    safe_counter = 0

    try:
        while True:
            safe_counter += 1
            if ann_fix[1] < sing_fix[0]:
                # Annotation without utterance counterpart
                # Skip this sentence
                ann = next(it_ann)
                ann_fix = ann

            # End of utterance is lower that start of sentences
            # Join sentences in one utterance
            elif sing_fix[1] < ann_fix[0]:
                sing = next(it_sing)
                sing_fix = sing

            #
            else:
                if ann_fix[0] < sing_fix[0]:

                    if ann_fix[1] < sing_fix[1]:
                        # The annotation and the singing are translated
                        ann = next(it_ann)
                        sing = next(it_sing)
                        if sing[0] > sing_fix[1] + 300:
                            sing_fix[1] += 200

                        refined = add_annotation(ann_fix, sing_fix, refined, 1)
                        ann_fix = ann
                        sing_fix = sing
                    else:
                        sing_fix = sing
                        ann_fix = ann
                        sing = next(it_sing)
                        while True:
                            if ann_fix[1] > sing[1]:
                                # The singing is fully contained into the annotation
                                sing_fix[1] = sing[1]
                                sing = next(it_sing)
                            elif ann_fix[1] > sing[0]:
                                if ann_fix[1] > sing[1]:
                                    sing_fix[1] = sing[1]
                                    sing = next(it_sing)
                                    refined = add_annotation(ann_fix, sing_fix, refined, 1)
                                    #ann_fix = ann
                                    sing_fix = sing
                                    break
                                else:
                                    ann = next(it_ann)
                                    ann_fix[1] = ann[1]
                                    ann_fix[3] += " " + ann[3]
                            else:
                                if ann_fix[0] > sing_fix[0]:
                                    ann = next(it_ann)
                                    ann_fix[1] = ann[1]
                                    ann_fix[3] += " " + ann[3]
                                else:
                                    refined = add_annotation(ann_fix, sing_fix, refined, 1)
                                    ann = next(it_ann)
                                    ann_fix = ann
                                    sing_fix = sing
                                    break

                        #refined = add_annotation(ann_fix, sing_fix, refined, 1)
                else:
                    # Sing is before prompt by a max of 500ms
                    if ann_fix[0] - sing_fix[0] <= 0.5:
                        # change prompt to 10ms before sing value
                        # we need it a bit lower, not equal
                        ann_fix[0] = sing_fix[0]-0.00001
                    else:
                        # This sentences is discarded
                        ann = next(it_ann)
                        ann_fix = ann

            if safe_counter > 200:
                return refined
    except StopIteration:
        refined = add_annotation(ann_fix, sing_fix, refined, 1)
        return refined


def add_annotation(annotation, singing, annotation_list, case):
    cases = {
        1: {"start": singing[0], "end": singing[1], "lyric": annotation[3], "index": annotation[2]},
        2: {"start": annotation[0], "end": annotation[1], "lyric": annotation[3], "index": annotation[2]}

    }

    annotation_list.append([cases[case]["start"],
                            cases[case]["end"],
                            cases[case]["lyric"],
                            cases[case]["index"]])
    return annotation_list


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("workspace", type=str,
                        help="Path where the output files will be saved")
    parser.add_argument("database_path", type=str,
                        help="Path to the directory where the Countries are listed")
    parser.add_argument("--pad", type=float, default=0.0,
                        help="Path where the output files will be saved")
    parser.add_argument('--version', action='version',
                        version='%(prog)s 1.0')

    args = parser.parse_args()

    realign_lyrics(args)
