from os import listdir, makedirs
from os.path import join, isfile, exists, dirname
import argparse
import math


class SetGraph:
    def __init__(self):
        self.arrangements = []
        self.singers = []

    def len(self):
        return len(self.singers)

    # Append one element to singers and arrangements lists
    def add_singer(self, sing):
        self.singers.append(sing)
        self.singers = list(set(self.singers))

    def add_arrangement(self, arrang):
        self.arrangements.append(arrang)
        self.arrangements = list(set(self.arrangements))

    # Append a list of new elements to singers and arrangements lists
    def add_singers_from_list(self, spk):
        self.singers += spk
        self.singers = list(set(self.singers))

    def add_arrangement_from_list(self, arrang):
        self.arrangements += arrang
        self.arrangements = list(set(self.arrangements))

    # Get lists
    def get_singers(self):
        return self.singers

    def get_arrangements(self):
        return self.arrangements


class Interpretation:
    def __init__(self):
        self.singers = []
        self.arrangements = []
        self.arrangements_count = []

    def new_interpretation(self, interpretation, train, dev, test):
        singer = interpretation.split('-')[-3] + "-" + interpretation.split('-')[-2]
        arrangement = interpretation.split('-')[0]

        if singer not in self.singers:
            self.singers.append(singer)
            self.arrangements.append([[], [], [], []])
            self.arrangements_count.append([0, 0, 0, 0])

        if arrangement in train.arrangements:
            index = self.singers.index(singer)
            self.arrangements_count[index][0] += 1
            self.arrangements[index][0].append(arrangement)

        elif arrangement in dev.arrangements:
            index = self.singers.index(singer)
            self.arrangements_count[index][1] += 1
            self.arrangements[index][1].append(arrangement)

        elif arrangement in test.arrangements:
            index = self.singers.index(singer)
            self.arrangements_count[index][2] += 1
            self.arrangements[index][2].append(arrangement)

        else:
            index = self.singers.index(singer)
            self.arrangements_count[index][3] += 1
            self.arrangements[index][3].append(arrangement)


class Kaldi_Set:
    def __init__(self, type, data_path):
        self.spk2gender = []
        self.textfile = []
        self.wavscp = []
        self.utt2spk = []
        self.path = join(data_path, type)
        create_folder(self.path)

    def add_utterance(self, data):
        if "{} {}".format(data["speaker"], data["gender"]) not in self.spk2gender:
            self.spk2gender.append("{} {}".format(data["speaker"], data["gender"]))
        self.textfile.append("{} {}".format(data["track_id"], data["lyrics"].upper()))
        # wav.scp list
        self.wavscp.append("{} wav/{}".format(data["track_id"], data["track_segment"]))
        # utt2spk list
        self.utt2spk.append("{} {}".format(data["track_id"], data["speaker"]))

    def save_files(self):
        list2file(join(self.path, "spk2gender"), sorted(self.spk2gender))
        list2file(join(self.path, "text"), sorted(self.textfile))
        list2file(join(self.path, "wav.scp"), sorted(self.wavscp))
        list2file(join(self.path, "utt2spk"), sorted(self.utt2spk))


def list2file(outfile, list_data):
    """
    Saves a list into a file
    :param list_data: list
    :param outfile: path to output file
    """
    create_folder(dirname(outfile))
    with open(outfile, "w") as f:
        for line in list_data:
            f.write("{}\n".format(line))


def create_folder(fd):
    if not exists(fd):
        makedirs(fd)


def get_countries(workspace_path):
    countries = []
    with open(join(workspace_path, 'countries.txt')) as cfl:
        for line in cfl:
            countries.append(line.replace('\n', ''))

    return countries


def split_train_test_dev_set_GB(workspace, countries, factor):
    """
    Function that split the singer of country GB into Train, Test, and Development sets
    This split is used as a reference. If more countries are used in the Acoustic, this three sets
    are keep un-variable and the other countries will be used to increase each of these sets.

    :param workspace: path to working directory
    :param countries: List of countries, by default is 'GB' but was added as a list in case of future variations
    :param factor: float, percentage of speakers to select to test. same value is used to validation
    :return: Three returns. The train, development and test which are objects of SetGraph class
    """
    base_path = join(workspace, "data")
    test = SetGraph()
    train = SetGraph()
    dev = SetGraph()

    interpretations = []
    singers = []
    #  Interpretations and singers GB only
    for country in countries:
        interpretations = list(sorted(set([f for f in listdir(join(base_path, country, country + "Vocals"))
                                           if f.endswith("wav")])))
        singers = list(sorted(set([f.split(".")[0].split("-")[-3] + "-" + f.split(".")[0].split("-")[-2]
                                   for f in interpretations])))

    sev_test_size = myRound(len(singers), factor)

    while True:
        for gender in ['M', 'F']:
            if test.len() < sev_test_size:
                gender_singer = sorted(list(filter(lambda x: gender in x, singers)))[-1]
                singers_from_one = get_singers(gender_singer, interpretations, singers)
                test.add_singers_from_list(singers_from_one)
                for sfo in singers_from_one:
                    singers.remove(sfo)

        for gender in ['M', 'F']:
            if dev.len() < sev_test_size:
                gender_singer = sorted(list(filter(lambda x: gender in x, singers)))[-1]
                singers_from_one = get_singers(gender_singer, interpretations, singers)
                dev.add_singers_from_list(singers_from_one)
                for sfo in singers_from_one:
                    singers.remove(sfo)

        if test.len() > sev_test_size and dev.len() > sev_test_size:
            break

    train.add_singers_from_list(singers)

    for spk in train.get_singers():
        train.add_arrangement_from_list(get_arrangement_per_singer(spk, interpretations))

    for spk in dev.get_singers():
        dev.add_arrangement_from_list(get_arrangement_per_singer(spk, interpretations))

    for spk in test.get_singers():
        test.add_arrangement_from_list(get_arrangement_per_singer(spk, interpretations))

    return train, dev, test


def split_train_test_dev_set_increase(workspace, countries, train, dev, test):
    """
    Function that split the singer of each country into Train, Test, and Validation set
    :param workspace: path to working directory
    :param factor: float, percentage of speakers to select to test. same value is used to validation
    :return: 3 list, train, val, test
    """
    base_path = join(workspace, "data")

    interpretations = []

    for country in countries:
        interpretations += [f.split('.', 1)[0] for f in listdir(join(base_path, country, country + "Vocals"))
                            if f.endswith("wav")]
    interpretations = list(sorted(set(interpretations)))

    new_interpretations = Interpretation()

    for interpretation in interpretations:
        new_interpretations.new_interpretation(interpretation, train, dev, test)

    index_new_singers = []
    for index, narrag in enumerate(new_interpretations.arrangements_count):
        #  If only intersect with train
        if narrag[0] == sum(narrag):
            train.add_singer(new_interpretations.singers[index])
            train.add_arrangement_from_list(new_interpretations.arrangements[index][0])

        elif narrag[1] == sum(narrag):
            dev.add_singer(new_interpretations.singers[index])
            dev.add_arrangement_from_list(new_interpretations.arrangements[index][1])

        elif narrag[2] == sum(narrag):
            test.add_singer(new_interpretations.singers[index])
            test.add_arrangement_from_list(new_interpretations.arrangements[index][2])
        else:
            index_new_singers.append(index)

    to_train, to_dev, to_test = split_new_singers(new_interpretations, index_new_singers)

    for index in to_train:
        train.add_singer(new_interpretations.singers[index])
        train.add_arrangement_from_list(new_interpretations.arrangements[index][0])
        train.add_arrangement_from_list(new_interpretations.arrangements[index][3])

    for index in to_dev:
        dev.add_singer(new_interpretations.singers[index])
        dev.add_arrangement_from_list(new_interpretations.arrangements[index][1])

    for index in to_test:
        test.add_singer(new_interpretations.singers[index])
        test.add_arrangement_from_list(new_interpretations.arrangements[index][2])

    return train, dev, test


def split_new_singers(new_interpretations, index):
    """
    Distribute new singers - naive bipartite graph cut
    New_arrangements to train.
    Cut is made to:
    1- Priority assign singer to set where has more arrangements
    2- If has same number of arrangement in different sets:
        a- priority train
        b- second dev
        c- third test

    :param new_interpretations:
    :param index:
    :return:
    """
    to_train = []
    to_dev = []
    to_test = []

    for i in index:
        current = new_interpretations.arrangements_count[i]
        if current[3] == sum(current):
            to_train.append(i)
        else:
            maxi_val = max(current)

            if current[3] == maxi_val or current[0] == maxi_val:
                to_train.append(i)
            elif current[1] == maxi_val:
                to_dev.append(i)
            elif current[2] == maxi_val:
                to_test.append(i)

    return to_train, to_dev, to_test


def get_singers_per_arrangement(arrangement, interpretations, singers):
    singer_per_arr = list(set([f.split(".")[0].split("-")[-3] + "-" + f.split(".")[0].split("-")[-2]
                   for f in interpretations if arrangement in f
                   and f.split(".")[0].split("-")[-3] + "-" + f.split(".")[0].split("-")[-2]
                   in singers]))
    return singer_per_arr


def get_arrangement_per_singer(singer, interpretations):
    arrangement = list(set([f.split('-')[0] for f in interpretations if singer in f]))
    return arrangement


def get_singers(singer_input, interpretations_wl, singers_wl):
    result = [singer_input]
    while True:
        current_size_result = len(result)
        for singer in result:
            arrangements = get_arrangement_per_singer(singer, interpretations_wl)
            for arrangement in arrangements:
                singers = get_singers_per_arrangement(arrangement, interpretations_wl, singers_wl)
                for sing in singers:
                    if sing not in result:
                        result.append(sing)
        result = list(set(result))
        if len(result) == current_size_result:
                break
    return result


def myRound(n, factor=1):
    """
    Function that returns the closest even integer value
    :param n: Value to round
    :param factor: Percentage to multiply n value (Default: 1)
    :return: integer
    """

    if n < 8:
        return 0
    elif n < 10:
        return 2
    else:
        answer = math.floor(n * factor)
        if not answer % 2:
            return answer
        if abs(answer-1-n) < abs(answer+1-n):
            return answer - 1
        else:
            return answer + 1


def file2list(path):
    """
    Funtion that read a file and returned as a list.
    :param path: full path to the file
    :return: list
    """

    data = []
    with open(path) as file:
        for line in file:
            data.append(line.replace("\n", ""))
    return data


def main(args):
    """
    Main Function
    :param workspace: path to working space
    :param wav_dir_name: directory name for wav files in workspace
    :return:
    """
    workspace = args.workspace

    # Get Countries
    countries = get_countries(workspace)

    test_size_factor = 0.1
    train, dev, test = split_train_test_dev_set_GB(workspace, ['GB'], test_size_factor)

    if len(countries) > 1:
        countries.remove('GB')
        countries.remove('US')
        countries.remove('AU')
        train, dev, test = split_train_test_dev_set_increase(workspace, ['US', 'AU'], train, dev, test)

    if len(countries) > 1:
        train, dev, test = split_train_test_dev_set_increase(workspace, countries, train, dev, test)

    list2file(join(workspace, "kaldi", "input", "train_spk"), train.get_singers())
    list2file(join(workspace, "kaldi", "input", "dev_spk"), dev.get_singers())
    list2file(join(workspace, "kaldi", "input", "test_spk"), test.get_singers())

    list2file(join(workspace, "kaldi", "input", "train_arr"), train.get_arrangements())
    list2file(join(workspace, "kaldi", "input", "dev_arr"), dev.get_arrangements())
    list2file(join(workspace, "kaldi", "input", "test_arr"), test.get_arrangements())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("workspace", type=str, help="Path where the output files will be saved")

    args = parser.parse_args()
    main(args)
