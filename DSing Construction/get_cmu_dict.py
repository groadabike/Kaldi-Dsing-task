"""
File to download CMUdict and create a list with words.
the list is saves as a txt file.
"""
import subprocess
from os.path import join, exists, dirname
from os import makedirs
import re
import argparse


def down_cmudict(cmu_path):
    subprocess.call(['svn', 'co', 'https://svn.code.sf.net/p/cmusphinx/code/trunk/cmudict',
                    cmu_path])


def create_list_of_words(cmu_path, cmu_version='0.7a'):
    def special_match(strg, search=re.compile(r'[^A-Z]').search):
        return not bool(search(strg))

    regex = r'\([^)]*\)'
    list_of_words = []
    cmudict = join(cmu_path, 'cmudict.' + cmu_version)
    with open(cmudict) as cmu:
        for line in cmu:
            if special_match(line[0]):
                word = re.sub(regex, '', line.split(" ")[0])
                list_of_words.append(word)
    return sorted(list(set(list_of_words)))


def write_list_word(word_list_path, words):
    with open(word_list_path, "w") as file:
        for word in words:
            file.write(word + '\n')


def create_folder(fd):
    if not exists(fd):
        makedirs(fd)


def get_cmu_dict(args):
    workspace = args.workspace
    print("[English Subset] Downloading CMUDict")

    cmu_path = join(workspace, 'cmudict')
    word_list_path = join(workspace, "dict.txt")

    # Validate if CMU exists so don't download every time
    if exists(cmu_path):
        print("CMUDict already exist - skipping this stage")
        exit()

    down_cmudict(cmu_path)  # down CMU dict

    words = create_list_of_words(cmu_path)  # create a list with dictionary

    create_folder(dirname(word_list_path))  # check if directory exists
    write_list_word(word_list_path, words)  # save dict file
    return True


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='Script downloads the CMUDict nad create file dict.txt with the vocabulary without pronunciation.'
    )
    parser.add_argument("workspace", type=str, help="Path to the Workspace directory")
    parser.add_argument('--version', action='version',
                        version='%(prog)s 1.0')
    args = parser.parse_args()
    get_cmu_dict(args)
