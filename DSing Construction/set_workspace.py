from os import makedirs
from os.path import exists, join
import argparse


def create_folder(fd):
    """
    Create a directory
    :param fd:
    :return:
    """
    if not exists(fd):
        makedirs(fd)


def create_db_accents(args):
    """
    Create file countries.txt, in directory $workspace/countries.txt',
    based-on the name of the dataset (DSing1, DSing3 or DSing30).
    :param args:
    :return:
    """
    # List of countries by set size
    accent = {
        'DSing1': ['GB'],
        'DSing3': ['GB', 'US', 'AU'],
        'DSing30': ['AE', 'AR', 'AU', 'BR', 'CL', 'CN', 'DE', 'ES', 'FR', 'GB',
                 'HU', 'ID', 'IN', 'IQ', 'IR', 'IT', 'JP', 'KR', 'MX', 'MY',
                 'NO', 'PH', 'PT', 'RU', 'SA', 'SG', 'TH', 'US', 'VN', 'ZA']
    }

    countries = accent[args.db]
    # create countries.txt file with the ids of the countries in the selected database
    with open(join(args.workspace, 'countries.txt'), 'w') as fl:
        for country in countries:
            fl.write(country + "\n")


if __name__ == '__main__':
    """
    Function that set the environment and parameters for the construction of the Damp_English.
    GB = Great Britain Accent
    GB+ = GB plus US and Australia
    GB++ = GB+ plus all other English interpretations 
    """
    db_options = ['DSing1', 'DSing3', 'DSing30']
    parser = argparse.ArgumentParser(
        description='Script creates the DSing Preconstructed directory'
        )
    parser.add_argument('workspace', type=str,
                        help='Path where the DB will be saves')
    parser.add_argument('--db', type=str,
                        help='Version of the database to construct [sing1, sing3, sing30] depending on the accent selection')
    parser.add_argument('--version', action='version',
                        version='%(prog)s 1.0')

    args = parser.parse_args()
    print("[English Subset] Creating directory {}".format(args.workspace))
    create_folder(args.workspace)  # create directory

    print("[English Subset] Countries version selected: {}".format(args.db))
    create_db_accents(args)  # create countries.txt

