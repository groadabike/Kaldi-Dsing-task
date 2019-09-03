from os.path import join, isfile, exists
from os import listdir, makedirs
import argparse
import subprocess
import json


def get_countries(workspace_path):
    countries = []
    with open(join(workspace_path, 'countries.txt')) as cfl:
        for line in cfl:
            countries.append(line.replace('\n', ''))

    return countries


def create_folder(fd):
    if not exists(fd):
        makedirs(fd)


def extract(segment, infilenm, out_root, left_padding=0.0, right_padding=0.0, samplerate=16000):
    """Use sox to extract segment from wav file.

    infilenm - path for unsegmented audio files
    out_root - root directory for output audio segments
    """

    outtemplate = '{}/{}-{:03d}.wav'
    outfilenm = outtemplate.format(out_root,
                                   infilenm.split('/')[-1].split(".")[0],
                                   segment['index'])
    subprocess.call(['sox', "-v", "0.95", "-G", infilenm, outfilenm,
                        'trim',
                      str(segment['start'] - left_padding),
                      '=' + str(segment['end'] + right_padding),
                      'rate', str(samplerate), 'remix', '1',
                     ])


def extract_utterances(args):
    """

    :param args:
    :return:
    """
    workspace = args.workspace
    database_path = args.database_path
    samplerate = args.sr
    countries = get_countries(args.workspace)
    left_pad = 0.04
    right_pad = 0.04

    for country in countries:
        output_sentences_path = join(workspace, "data", country, country + "Vocals")
        create_folder(output_sentences_path)

        database_vocal_path = join(database_path, country, country + 'Vocals')
        interpretations = [f for f in listdir(database_vocal_path)]

        refined_lyrics_path = join(workspace, "data", country, country + "LyricsRefined")
        refined_lyrics = [f for f in listdir(refined_lyrics_path)]
        for lyric in refined_lyrics:
            performances_full_id = lyric.split(".")[0]  # arrangement_id-performance_id-country_id-gender-user_id
            performances = [s for s in interpretations if performances_full_id in s]   # Should return only one result
            if len(performances) > 0:
                #  Read the annotations
                with open(join(refined_lyrics_path, lyric)) as infile:
                    json_string = infile.read()
                segments = json.loads(json_string)

                for i, segment in enumerate(segments):
                    #  We only keep utterances longer than one second as
                    #  shorter utterances cannot have more than one sound (vowel/consonant/coughing)
                    if segment['end'] - segment['start'] >= 1.0:
                        for performance in performances:
                            extract(segment, join(database_vocal_path, performance), output_sentences_path,
                                    left_pad, right_pad, samplerate)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("workspace", type=str, help="Path where the output files will be saved")
    parser.add_argument("database_path", type=str, help="Path to the directory where the Countries are listed")
    parser.add_argument("--sr", type=int, help="Target samplerate", default=16000)

    args = parser.parse_args()
    extract_utterances(args)
