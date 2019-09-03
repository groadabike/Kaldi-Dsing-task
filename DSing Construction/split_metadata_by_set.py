import argparse
import json
from os.path import join, exists


def read_json(filepath):
    try:  # Read the json
        with open(filepath) as data_file:
            data = json.load(data_file)
    except json.decoder.JSONDecodeError:  # Json has an extra first line. Error when was created
        data = []

    return data


def save_json(filepath, content):
    with open(filepath, 'w') as outfile:
        json.dump(content, outfile, indent=4)


def read_gold_list(workspace, set):
    goldpath = join(workspace, "kaldi", "data", set + ".gold")
    gold_list = []
    if exists(goldpath):
        with open(goldpath) as f:
            for line in f:
                gold_list.append(line.replace('\n', ''))

    return gold_list


def main(args):
    """
    Split the metadata.json file by dataset
    :param args:
    :return:
    """
    workspace = args.workspace
    metadata_name = args.metadata_name
    metadata = read_json(join(workspace, metadata_name))

    sets = ['train', 'dev', 'test']
    for set in sets:
        output_json = []
        metadatafile = "metadata_{}.json".format(set)
        gold_list = read_gold_list(workspace, set)

        for item in metadata:
            if item["data_set"] == set:
                if item["track_id"] in gold_list:
                    item["gold"] = 1
                else:
                    item["gold"] = 0

                try:
                    if item["old_track_id"] in gold_list:
                        item["gold"] = 1
                    else:
                        item["gold"] = 0
                except KeyError:
                    pass

                if len(output_json) == 0:
                    output_json.append(item)
                exist = 0

                for out in output_json:
                    if item["track_id"] == out["track_id"]:
                        exist = 1
                    try:
                        if item["old_track_id"] in out["track_id"]:
                            exist = 1
                    except KeyError:
                        pass

                    if exist == 1:
                        break
                if exist == 0:
                    output_json.append(item)

        save_json(join(workspace, metadatafile), output_json)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("workspace", type=str, help="Path where the output files will be saved")
    parser.add_argument("metadata_name", type=str, help="Path where the output files will be saved")

    args = parser.parse_args()
    main(args)