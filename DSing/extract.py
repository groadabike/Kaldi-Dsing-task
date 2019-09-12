#!/usr/bin/env python

# Copyright (C) 2019 Gerardo Roa


from __future__ import print_function
from __future__ import division

import os
import subprocess
import librosa
import time
import argparse
from argparse import RawTextHelpFormatter

import warnings
import logging

logging.captureWarnings(True)
warnings.simplefilter(action='ignore', category=FutureWarning)

__author__ = 'Gerardo Roa - University of Sheffield'


def beattracking_dynamicprograming(data_dir, outpath, log_file, seg_file, mode):
    """
    This function assumed that the directories data_dir and bt_dir, and the directory for the file log_file exists.

    :param data_dir: Path to the data set. e.g data/train
    :param bt_dir:   Path where the features will be save. e.g. bt_feats
    :param log_file: Path to the log file. e.g. bt_feats/log/bt_feats.1.txt
    :param seg_file: Path to the segment file when mode=segment. e.g. bt_feats/temp/segment.1
    :param mode:     Mode in which the data is split. options = [segment when segment file is used, or wavscp when no segment is used]
    :param mono:     Parameter for librosa.load(wav, sr=sr, mono=mono)
    :param sr:       Parameter for librosa.load(wav, sr=sr, mono=mono)
    :param nj:       Number of jobs
    :param fillgap:  True will attempt to add beat at beginning and end based on average distance of founded beats
    :return:
    """

    logging.basicConfig(filename=log_file, level=logging.INFO, filemode='w',
                        format="%(asctime)s [%(pathname)s:%(lineno)s - %(funcName)s - %(levelname)s ] %(message)s")

    features_list = []

    # head of log file
    current_time = "{}-{}-{} {}:{}:{}".format(
        time.localtime().tm_year, time.localtime().tm_mon, time.localtime().tm_mday,
        time.localtime().tm_hour, time.localtime().tm_min, time.localtime().tm_sec)
    logging.info('# {}'.format(current_time))
    logging.info('# Starting beat-tracking extraction')
    logging.info('# Using dynamic programing')
    logging.info('# ')

    # when segment file exist
    if mode == 'segment':
        wavscp = [f.rstrip() for f in open(os.path.join(data_dir, "wav.scp"))]
        segments = [f.rstrip() for f in open(seg_file)]
        recordings = []
        for segment in segments:
            utt_id, rec_id, start, end = segment.split(" ")
            _, ext_filename = [f for f in wavscp if rec_id in f][0].split(" ", 1)
            recordings.append('{}, {} sox -t wav - -t wav {}/{}.wav trim {} {}'.format(
                    utt_id, ext_filename, outpath, utt_id, start, float(end)-float(start)))

    # No segment file exist, use wav.scp
    else:
        # TODO implement when no segment file is provided
        recordings = [f.rstrip() for f in open(os.path.join(data_dir, "wav.scp"))]
        print(recordings)

    for record in recordings:
        if os.path.exists(os.path.join(data_dir, 'segments')):
            # running sox command when segment exist
            # subprocess.call in python 2.7
            # subprocess.run in python 3.5 or above
            print(os.path.join(outpath, record.split(',', 1)[0] + ".wav"))
            if not os.path.exists(os.path.join(outpath, record.split(',', 1)[0] + ".wav")):
                subprocess.call(record.split(',', 1)[1], shell=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Usage: %(prog)s <data-dir> [<log-dir> [<btfeat-dir>]]\n'
                    'e.g.: %(prog)s data/train exp/make_bt/train bt_feat\n'
                    'Note: <log-dir> defaults to <data-dir>/log, and  <btfeat-dir> defaults to <data-dir>/beat\n'
                    'Options:\n'
                    '--mono               # Convert the audio to mono'
                    '--mode               # Specify if use segment or wav.scp files'
                    '                     # values are [segment, wavscp]'
                    '--segfile            # path to segment file'
                    '                     # this is a mandatory file when --mode=segment'
                    '--sr                 # Sample rate, default=16000',
        formatter_class=RawTextHelpFormatter
    )
    parser.add_argument("datadir", type=str, help="Path to the <data-dir>")

    parser.add_argument("logfile", type=str, help="Path to <log-file>",
                        nargs='?', default="")

    parser.add_argument("outpath", type=str, help="Path to <btfeat-dir>",
                        nargs='?', default="")


    parser.add_argument("--mode", type=str, help="Path to the Workspace directory",
                        choices=['segment', 'wavscp'], default='segment')

    parser.add_argument("--segfile", type=str, help="Path to <segment-file>",
                        default="")


    parser.add_argument('--version', action='version',
                        version='%(prog)s 0.1')

    args = parser.parse_args()

    if args.mode == 'segment' and args.segfile == "":
        parser.error("--mode=segment requires --segfile=<segment-file>.")

    datadir = args.datadir
    logfile = os.path.join(datadir, "log") if args.logfile == "" else args.logfile
    outpath = os.path.join(datadir, "wav") if args.outpath == "" else args.outpath


    mode = args.mode
    segfile = args.segfile

    #nj = logfile.split(".")[-2]

    beattracking_dynamicprograming(datadir, outpath, logfile, segfile, mode)


if __name__ != '__main__':
    raise ImportError('This script can only be run, and can\'t be imported')


