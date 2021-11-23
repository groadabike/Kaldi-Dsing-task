# DSing ASR task: Resources and Baseline for an unaccompanied singing ASR.

In this repository, you will find the scripts used to construct the DSing ASR-oriented dataset
and the baseline system constructed on Kaldi.  

Cite:
```
@inproceedings{Roa_Dabike-Barker_2019,  
  author = {Roa Dabike, Gerardo and Barker, Jon}  
  title = {{Automatic Lyric Transcription from Karaoke Vocal Tracks: Resources and a Baseline System}},  
  year = 2019,  
  booktitle = {Proceedings of the 20th Annual Conference of the International Speech Communication Association (INTERSPEECH 2019)}  
}
```

## 1- DSing dataset

DSing is an ASR-oriented dataset constructed from the [Smule Sing!300x30x2](https://ccrma.stanford.edu/damp/) dataset (**Sing!**).
This repository provides the scripts to transform **Sing!** to the DSing ASR task. 

## 2- Initial steps

The first step before running any of the scripts is to obtain access to **Sing!** dataset.
For more details, go to [DAMP repository](https://ccrma.stanford.edu/damp/).   

## 3- Extract DSing dataset using pre-segmented data.

In directory **[DSing preconstructed](DSing preconstructed)** you can find the DSing dataset segmentation.