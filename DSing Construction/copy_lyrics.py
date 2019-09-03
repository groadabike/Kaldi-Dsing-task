from os import listdir, makedirs
from os.path import join, exists, dirname
from shutil import copy2
import argparse


def create_folder(fd):
    if not exists(fd):
        makedirs(fd)


def copy_lyrics_from(country, args):
    for suffix in ['Lyrics', 'ArrangementMeta']:
        src_path = join(args.database, country, country + suffix)
        dst_path = join(args.workspace, "data", country, country + suffix)
        list_annotations = [f for f in listdir(src_path)]

        create_folder(dst_path)
        for lyric in list_annotations:
            copy2(join(src_path, lyric), join(dst_path, lyric))


def get_countries(workspace_path):
    countries = []
    with open(join(workspace_path, 'countries.txt')) as cfl:
        for line in cfl:
            countries.append(line.replace("\n", ""))

    return countries


if __name__ == '__main__':
    """
    Script that copy the lyrics from the original DAMP and preprocess them to identify the word level annotations
    """
    parser = argparse.ArgumentParser(
        description='Copy the original lyrics to workspace to process them',
    )
    parser.add_argument('workspace', type=str,
                        help='Path to Workspace')
    parser.add_argument('database', type=str,
                        help='Path to DAMP300x30x2')
    parser.add_argument('--version', action='version',
                        version='%(prog)s 1.0')

    args = parser.parse_args()
    countries = get_countries(args.workspace)
    for country in countries:
        print("[English Subset] Copy lyrics of country {} to {}".
              format(country, join(args.workspace, "data", country, country + "Lyrics")))
        copy_lyrics_from(country, args)

