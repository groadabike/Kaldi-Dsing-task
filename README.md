# DSing: Resources and Baseline for Unaccompanied Singing ASR

This is the accompanying repository for our paper *Automatic Lyric Transcription from Karaoke Vocal Tracks: Resources and a Baseline System*, 
containing the DSing dataset segmentation and a baseline Kaldi ASR system.

## What is DSing?

DSing is an unaccompanied singing dataset created to fill a gap in automatic lyrics transcription datasets. 
It is derived from the [Smule DAMP-MVP 300x30x2](https://zenodo.org/records/2747436) dataset, 
a collection of thousands of solo-singing karaoke recordings.

## Repository structure

- [`DSing-Kaldi-Recipe/`](DSing-Kaldi-Recipe) -- Kaldi recipe for the DSing ASR task (the baseline system).
- [`DSing-preconstructed/`](DSing-preconstructed) -- the DSing dataset segmentation.

## Getting started

### 1. Get the data
Request permission and download the audio from [Smule DAMP-MVP 300x30x2](https://zenodo.org/records/2747436).

### 2. Get the dataset segmentation
The train/dev/test splits used in our paper are in [`DSing-preconstructed/`](DSing-preconstructed).

### 3. Run the baseline system
See [`DSing-Kaldi-Recipe/`](DSing-Kaldi-Recipe) for instructions on training and evaluating the baseline Kaldi ASR system.

## Reference

If you use this segmentation, please cite DAMP-MVP 300x30x2 as indicated by Smule, and our paper as follows:

```bibtex
@inproceedings{Roa_Dabike-Barker_2019,
  author    = {Roa-Dabike, Gerardo and Barker, Jon},
  title     = {{Automatic Lyric Transcription from Karaoke Vocal Tracks: Resources and a Baseline System}},
  year      = 2019,
  booktitle = {Proceedings of the 20th Annual Conference of the International Speech Communication Association (INTERSPEECH 2019)}
}
```