<div class="title" align=center>
    <h1>Audio Dataset VPR Classifier</h1>
	<div>A voiceprint recognition classifier for audio dataset</div>
    <br/>
    <p>
        <img src="https://img.shields.io/github/license/2DIPW/audio_dataset_vpr">
    	<img src="https://img.shields.io/badge/python-3.8-blue">
        <img src="https://img.shields.io/github/stars/2DIPW/audio_dataset_vpr?style=social">
        
</div>

[简体中文](https://github.com/2DIPW/audio_dataset_vpr/blob/master/README.md) | English

## 🚩 Introduction
A dataset screening tool that automatically classifies audio dataset by speaker based on the EcapaTdnn voiceprint recognition model. To use it, you just need to prepare several representative voice clips for each speaker. It can be used to assist the make of dataset for speech models such as VITS/SoVITS/Diff-SVC/RVC/DDSP-SVC.

This project is modified by [yeyupiaoling/VoiceprintRecognition-Pytorch](https://github.com/yeyupiaoling/VoiceprintRecognition-Pytorch), which adds batch processing feature, and can save the recognition results as a [2DIPW/audio_dataset_screener]( https://github.com/2DIPW/audio_dataset_screener) JSON project file for further manual screening. Compared with the original project, all codes related to model training have been deleted, so if you need to train your own model, you should use the original project.

This project is experimental and does not guarantee the effect. It is only for learning and communication, not for production environment.

## 📥 Deploy
### Clone
```shell
git clone https://github.com/2DIPW/audio_dataset_vpr.git
cd audio_dataset_vpr
```
### Create a virtual environment (optional, take Anaconda as an example)
```sheel
conda create -n ad-vpr python=3.8
conda activate ad-vpr
```
### Install PyTorch
- Install PyTorch according to your needs, see [official website](https://pytorch.org/get-started/locally) for details, the following is an example of using pip to install PyTorch-CUDA. Skip if already installed.
```shell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```
### Install other requirements
```shell
pip install -r requirements.txt
```
### Configure the voiceprint recognition model
Under the default parameters, you need to put the model files `model.pt`, `model.state`, `optimizer.pt` and the configuration file `config.yml` in the `model` directory. You can also use model and configuration files in other paths by specifying `-m` and `-c` parameters.

- You can download the EcapaTdnn model I trained on [zhvoice](https://aistudio.baidu.com/aistudio/datasetdetail/133922) dataset from Hugging Face: [2DIPW/VPR_zhvoice_EcapaTdnn](https://huggingface.co/2DIPW/VPR_zhvoice_EcapaTdnn/tree/main)
- Or download [more models trained by the original project author](https://github.com/yeyupiaoling/VoiceprintRecognition-Pytorch#%E6%A8%A1%E5%9E%8B%E4%B8%8B%E8%BD%BD)
- Or [train your own model using the original project](https://github.com/yeyupiaoling/VoiceprintRecognition-Pytorch#%E5%88%9B%E5%BB%BA%E6%95%B0%E6%8D%AE)

The quality of voiceprint recognition is directly related to the quality of the model, you can try to find the best model by yourself.
## 🗝 How to use
### Prepare audio feature library
- For each speaker, select several most representative speech segments and put them into the `labels` directory according to the following structure. Create one subdirectory for each speaker, the directory name is the speaker name, and the file name is arbitrary.
- Since the code determines the speaker based on the number of feature segments whose similarity is greater than the given threshold, please ensure that the number of feature segments **equal** for each speaker.
- If you want to use the voiceprint recognition results for further manual screening by Audio Dataset Screener, the number of speakers should not exceed 5, otherwise speakers with serial numbers greater than 5 will be automatically ignored by Audio Dataset Screener.

    ```
    input
    ├───speaker1
    │   ├───xxx1-xxx1.wav
    │   ├───...
    │   └───xxx1-xxx4.wav
    └───speaker2
        ├───xxx2-xxx1.wav
        ├───...
        └───xxx2-xxx4.wav
    ```
### Prepare audio files for classification
- With the default parameters, you need to put all the audio files (wav format) into the `input` directory. You can also load audio files in other paths by specifying the `-i` parameter.
### Run the recognition
- Using `infer.py`
    ```shell
    python infer.py
    ```
    Parameters that can be specified:
    - `-m` | `--model_path`: Path to model. Default: `model/`
    - `-c` | `--configs`: Path to model config file. Default: `model/config.yml`
    - `-d` | `--device`: Device to use, gpu or cpu. Default: `gpu`
    - `-l` | `--label_path`: Path to Voice feature library. Default: `labels/`
    - `-t` | `--threshold`: Threshold for judging compliance. Default: `0.6`
    - `-i` | `--input_path`: Path to input files. Default: `input/`
    - `-o` | `--output_path`: Path to output files. Default: `output/`

- After the process is complete, the input audio files will be moved to the directory named in the `VPR_Result_YYYYMMDD_HHMMSS` format in the `output` directory, and the audio files recognized as different speakers will be moved to the directories named after the speakers, unrecognized audio files will be moved to the `Unrecognized` folder.
- The recognition results will also be saved as a `result.json` file, which can be imported using Audio Dataset Screener for further manual screening.

## ⚖ License
The original project is licensed under [Apache License 2.0](https://github.com/yeyupiaoling/VoiceprintRecognition-Pytorch/blob/develop/LICENSE) . According to the license, my project contains the MODIFICATION_STATEMENT.

This project is licensed under [GNU General Public License v3.0](https://github.com/2DIPW/audio_dataset_vpr/blob/master/LICENSE) .

*Open source leads the world to a brighter future.*
## 📃 References
```
@inproceedings{desplanques2020ecapa,
  title={{ECAPA-TDNN: Emphasized Channel Attention, propagation and aggregation in TDNN based speaker verification}},
  author={Desplanques, Brecht and Thienpondt, Jenthe and Demuynck, Kris},
  booktitle={Interspeech 2020},
  pages={3830--3834},
  year={2020}
}
```