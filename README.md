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
For more details, go to  [https://ccrma.stanford.edu/damp/](https://ccrma.stanford.edu/damp/).   


## 3- Transform Sing! to DSing dataset

The scripts to transform the **Sing!** dataset to DSing ASR task dataset are located in the **[DSing Construction](DSing Construction/)** directory.
The process is based on a series of python tools that are summarise in the runme_sing2dsing.sh bash script.

1. Define the variable *version* with the name of the DSing version you want to construct (DSing1, DSing3 or DSing30).
Any other option will rise an error.
2. Set the variable *DSing_dest* with the path where the DSing version will be saved.
3. Set the variable *SmuleSing_path* with the path to your copy of Smule Sing!300x30x2.

 