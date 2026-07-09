# DSing ASR task: Resources and Baseline for an unaccompanied singing ASR.

This is the accompanied repository for our paper `Automatic Lyric Transcription from Karaoke Vocal Tracks: Resources and a Baseline System`.

It contains the resources and the baseline system for the DSing ASR task.

## What is DSing?

DSing is an unaccompanied singing dataset created to fill a gap in the automatic lyrics transcriptions datasets.
It is derived from the [Smule DAMP-MVP 300x30x2](https://zenodo.org/records/2747436) dataset, which are thousands of solo-singing karaoke recordings.

## Directories in this repo

- DSing Kaldi Recipe : Directory with a Kaldi recipe for the DSing ASR task.
- DSing preconstructed : Directory with the DSing dataset segmentation.

## How to use the data?

1. Request permission and download the data from [Smule DAMP-MVP 300x30x2](https://zenodo.org/records/2747436).
2. In the directory **[DSing preconstructed](DSing preconstructed)** you can find the DSing dataset segmentation.


## Reference

If you use this segmentation, please cite DAMP-MVP 300x30x2 as indicated by Smule and our paper as follows:

```
@inproceedings{Roa_Dabike-Barker_2019,  
  author = {Roa-Dabike, Gerardo and Barker, Jon}  
  title = {{Automatic Lyric Transcription from Karaoke Vocal Tracks: Resources and a Baseline System}},  
  year = 2019,  
  booktitle = {Proceedings of the 20th Annual Conference of the International Speech Communication Association (INTERSPEECH 2019)}  
}
```