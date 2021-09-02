#!/usr/bin/env python
""" refine.py

Curses GUI to refine the annotations (start/end points and transcriptions)

Usage:
  refine.py  <db_path> <segfilenm> [<outsegfilenm>]
  refine.py --help

Options:
  <db_path>         Path to DAMP DB
  <segfilenm>      Name of the segmentation file
  <outsegfilenm>   Name of the output segmentation file. Defaults to overwriting the input segmentation file.
  --help         print this help screen

"""

from __future__ import print_function
import curses
import os
import npyscreen
import json
import subprocess
import docopt
import logging
import sys

__author__ = 'rmarxer'


def play_params(start=0, end=None, length=None, tempo=1.0):
    return ['trim',
            '{}'.format(start),
            '={}'.format(end) if end is not None else '{}'.format(length),
            'tempo',
            '-s',
            '{}'.format(tempo),
            'gain',
            '-3']


def play(wav_filenm, start=0, end=None, length=None, tempo=1.0):
    command = ['play',
               '-q', '-V1',
               wav_filenm]

    command += play_params(start=start, end=end, length=length, tempo=tempo)

    logging.debug('Play command: {}'.format(command))

    return subprocess.Popen(command)


class Model:
    def __init__(self, seg_filenm, out_seg_filenm, db_path):
        self.db_path = db_path

        self.seg_filenm = seg_filenm
        self.out_seg_filenm = out_seg_filenm

        self.segments = self.load_segments()

        self.current_tempo = 1.0

        self.time_delta = 0.1
        self.tempo_delta = 0.1

        self.start_end_length = 1.0

        self.current_player = None

    def stop(self):
        logging.debug('Play: self.current_player={}'.format(self.current_player))
        if self.current_player is not None:
            self.current_player.kill()

    def play(self, record_id, start_offset=0, length=None, tempo=None):
        self.stop()

        start = self.segments[record_id]['start'] + start_offset
        length = length or (self.segments[record_id]['end'] - start)

        wav_filename = os.path.join('{}/{}'.format(self.db_path, self.segments[record_id]['wavfile']))

        self.current_player = play(wav_filename, start=start, length=length, tempo=tempo or self.current_tempo)

    def play_start(self, record_id):
        self.play(record_id, length=self.start_end_length,
                  tempo=1.0)

    def play_end(self, record_id):
        self.play(record_id, start_offset=(self.segments[record_id]['end']
                                           - self.segments[record_id]['start']
                                           - self.start_end_length),
                  tempo=1.0)

    def add_to_all(self, **kwargs):
        for segment in self.segments:
            for k, v in kwargs.items():
                segment[k] += v

        self.save_segments()

    def update(self, index, **kwargs):
        self.segments[index].update(kwargs)
        self.save_segments()

    def list_all_records(self):
        return list(enumerate(self.segments))

    def get_record(self, index):
        return index, self.segments[index]

    def load_segments(self):
        with open(self.seg_filenm, 'r') as f:
            return json.load(f)

    def save_segments(self):
        with open(self.out_seg_filenm, 'w') as f:
            json.dump(self.segments, f, indent=4, sort_keys=True)


class RecordList(npyscreen.MultiLineAction):
    def __init__(self, *args, **keywords):
        super(RecordList, self).__init__(*args, **keywords)

    def display_value(self, vl):
        index, record = vl
        lyric = record['lyric']
        transcription = record.get('transcription', record['lyric'])
        label = ''
        label += 'S' if record.get('selected', False) else ' '
        label += 'W' if record.get('wrong', False) else ' '
        label += 'M' if transcription != lyric else ' '
        return "[{:3s}] [{:3d}] {:8.2f} - {:8.2f} :: {}".format(label,
                                                                       record['index'],
                                                                       record['start'],
                                                                       record['end'],
                                                                       transcription.replace('\n', ''))

    def modify_start(self, index, record, direction):
        self.parent.parentApp.db.update(index,
                                        start=record['start'] + direction * self.parent.parentApp.db.time_delta)
        self.parent.parentApp.db.play_start(index)

    def modify_end(self, index, record, direction):
        self.parent.parentApp.db.update(index,
                                        end=record['end'] + direction * self.parent.parentApp.db.time_delta)
        self.parent.parentApp.db.play_end(index)

    def actionHighlighted(self, act_on_this, keypress):
        index, record = act_on_this
        logging.debug('{} --> {}'.format(index, keypress))

        if keypress in {curses.ascii.NL, curses.ascii.CR}:
            logging.debug('Edit transcripiton')
            self.parent.parentApp.getForm('EDITRECORDFM').value = index
            self.parent.parentApp.switchForm('EDITRECORDFM')
            self.parent.parentApp.db.play(index)

        elif keypress == ord('1'):
            logging.debug('Decrease start')
            self.modify_start(index, record, -1)

        elif keypress == ord('2'):
            logging.debug('Increase start')
            self.modify_start(index, record, 1)

        elif keypress == ord('3'):
            logging.debug('Play start')
            self.parent.parentApp.db.play_start(index)

        elif keypress == ord('8'):
            logging.debug('Play end')
            self.parent.parentApp.db.play_end(index)

        elif keypress == ord('9'):
            logging.debug('Decrease end')
            self.modify_end(index, record, -1)

        elif keypress == ord('0'):
            logging.debug('Increase end')
            self.modify_end(index, record, 1)

        elif keypress == ord('s'):
            logging.debug('Mark Select')
            self.parent.parentApp.db.update(index, selected=not record.get('selected', False))
            self.h_cursor_line_down(0)

        elif keypress == ord('w'):
            logging.debug('Mark Wrong')
            self.parent.parentApp.db.update(index, wrong=not record.get('wrong', False))
            self.h_cursor_line_down(0)

        elif keypress == curses.ascii.SP:
            logging.debug('Play')
            self.parent.parentApp.db.play(index)

        elif keypress == ord('z'):
            logging.debug('Decrease start all')
            self.parent.parentApp.db.add_to_all(start=-self.parent.parentApp.db.time_delta)
            self.update()
            self.parent.parentApp.db.play_start(index)

        elif keypress == ord('x'):
            logging.debug('Increase start all')
            self.parent.parentApp.db.add_to_all(start=+self.parent.parentApp.db.time_delta)
            self.update()
            self.parent.parentApp.db.play_start(index)

        elif keypress == ord('n'):
            logging.debug('Decrease end all')
            self.parent.parentApp.db.add_to_all(end=-self.parent.parentApp.db.time_delta)
            self.update()
            self.parent.parentApp.db.play_end(index)

        elif keypress == ord('m'):
            logging.debug('Increase end all')
            self.parent.parentApp.db.add_to_all(end=+self.parent.parentApp.db.time_delta)
            self.update()
            self.parent.parentApp.db.play_end(index)

        elif keypress == ord('-'):
            logging.debug('Decrease tempo')
            self.parent.parentApp.db.current_tempo = max(self.parent.parentApp.db.current_tempo
                                                         - self.parent.parentApp.db.tempo_delta,
                                                         0.3)
            self.parent.wStatus2.value = 'Playback speed: {}x'.format(self.parent.parentApp.db.current_tempo)
            self.parent.wStatus2.update()
            self.parent.parentApp.db.play(index)

        elif keypress == ord('+'):
            logging.debug('Increase tempo')
            self.parent.parentApp.db.current_tempo = min(self.parent.parentApp.db.current_tempo
                                                         + self.parent.parentApp.db.tempo_delta,
                                                         3.0)
            self.parent.wStatus2.value = 'Playback speed: {}x'.format(self.parent.parentApp.db.current_tempo)
            self.parent.wStatus2.update()
            self.parent.parentApp.db.play(index)
        elif keypress == ord('/'):
            self.parent.parentApp.db.stop()
            
        elif keypress == ord('q'):
            #quit()
            sys.exit("Refine process ended")

        self.update()

    def set_up_handlers(self):
        super(RecordList, self).set_up_handlers()
        self.handlers.update({
            curses.ascii.NL:    self.h_act_on_highlighted,
            curses.ascii.CR:    self.h_act_on_highlighted,
            curses.ascii.SP:    self.h_act_on_highlighted,
            ord('1'): self.h_act_on_highlighted,
            ord('2'): self.h_act_on_highlighted,
            ord('3'): self.h_act_on_highlighted,
            ord('8'): self.h_act_on_highlighted,
            ord('9'): self.h_act_on_highlighted,
            ord('0'): self.h_act_on_highlighted,
            ord('s'): self.h_act_on_highlighted,
            ord('w'): self.h_act_on_highlighted,
            ord('z'): self.h_act_on_highlighted,
            ord('x'): self.h_act_on_highlighted,
            ord('n'): self.h_act_on_highlighted,
            ord('m'): self.h_act_on_highlighted,
            ord('-'): self.h_act_on_highlighted,
            ord('+'): self.h_act_on_highlighted,
            ord('/'): self.h_act_on_highlighted,
            ord('q'): self.h_act_on_highlighted,
            })


class RecordListDisplay(npyscreen.FormMutt):
    MAIN_WIDGET_CLASS = RecordList

    def __init__(self, *args, **keywords):
        super(RecordListDisplay, self).__init__(*args, **keywords)
        self.how_exited_handers[npyscreen.wgwidget.EXITED_ESCAPE] = self.exit_application

    def beforeEditing(self):
        self.update_list()

    def update_list(self):
        self.wMain.values = self.parentApp.db.list_all_records()
        self.wMain.display()

    def exit_application(self):
        self.parentApp.db.stop()
        self.parentApp.db.save_segments()
        self.parentApp.setNextForm(None)
        self.editing = False


class EditRecord(npyscreen.ActionFormMinimal):
    def __init__(self, *args, **keywords):
        super(EditRecord, self).__init__(*args, **keywords)
        self.how_exited_handers[npyscreen.wgwidget.EXITED_ESCAPE] = self.on_cancel

    def create(self):
        self.value = None
        self.wgIndex = self.add(npyscreen.TitleText, name="Index:", editable=False)
        self.wgStart = self.add(npyscreen.TitleText, name="Start:", editable=False)
        self.wgEnd = self.add(npyscreen.TitleText, name="End:", editable=False)
        self.wgLyric = self.add(npyscreen.TitleText, name="Lyric:", editable=False)
        self.wgTranscription = self.add(npyscreen.TitleText, name="Transcription:")

    def beforeEditing(self):
        if self.value is not None:
            record_id, record = self.parentApp.db.get_record(self.value)

            self.record_id = record_id
            self.name = "Record id : {}".format(self.record_id)

            self.wgIndex.value = '{}'.format(record['index'])
            self.wgStart.value = '{}'.format(record['start'])
            self.wgEnd.value = '{}'.format(record['end'])
            self.wgLyric.value = record['lyric']
            self.wgTranscription.value = record.get('transcription', record['lyric'])

    def on_ok(self):
        if self.record_id is not None:  # We are editing an existing record
            self.parentApp.db.update(self.record_id,
                                     start=float(self.wgStart.value),
                                     end=float(self.wgEnd.value),
                                     transcription=self.wgTranscription.value,
                                     )

        self.parentApp.db.stop()
        self.parentApp.switchFormPrevious()

    def on_cancel(self):
        self.parentApp.db.stop()
        self.parentApp.switchFormPrevious()


class TranscriberApplication(npyscreen.NPSAppManaged):
    def __init__(self, segfilenm, out_seg_filenm, db_path):
        super(TranscriberApplication, self).__init__()
        self.db = Model(segfilenm, out_seg_filenm, db_path)

    def onStart(self):
        self.addForm("MAIN", RecordListDisplay)
        self.addForm("EDITRECORDFM", EditRecord)


def main():
    """Main method called from commandline."""
    arguments = docopt.docopt(__doc__)
    db_path = arguments['<db_path>']
    segfilenm = arguments['<segfilenm>']
    out_seg_filenm = arguments['<outsegfilenm>'] or segfilenm

    logging.basicConfig(level=logging.DEBUG, filename='test.log')

    app = TranscriberApplication(segfilenm, out_seg_filenm, db_path)
    app.run()


if __name__ == '__main__':
    main()
