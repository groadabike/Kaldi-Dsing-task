# DSing ASR task: Resources and Baseline for unaccompanied singing ASR.

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

 
## 2- Description of directories

* **DSing Kaldi Recipe** contains the baseline Kaldi recipe for DSing corpus.
* **DSing Construction** contains the scripts to transform Smule Sing!300x30x2 to DSing ASR task.
* 

## 