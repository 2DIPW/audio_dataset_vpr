<div class="title" align=center>
    <h1>Audio Dataset VPR Classifier</h1>
	<div>音频数据集声纹识别分类器</div>
    <br/>
    <p>
        <img src="https://img.shields.io/github/license/2DIPW/audio_dataset_vpr">
    	<img src="https://img.shields.io/badge/python-3.8-blue">
        <img src="https://img.shields.io/github/stars/2DIPW/audio_dataset_vpr?style=social">
        
</div>

简体中文 | [English](https://github.com/2DIPW/audio_dataset_vpr/blob/master/README_EN.md)

## 🚩 简介
一个基于声纹识别模型对音频数据集按说话人自动分类的数据集筛选辅助工具，仅需为每个说话人准备数条代表性的语音片段，可用于辅助 VITS/SoVITS/Diff-SVC/RVC/DDSP-SVC 等语音模型数据集的制作。

基于 [yeyupiaoling/VoiceprintRecognition-Pytorch](https://github.com/yeyupiaoling/VoiceprintRecognition-Pytorch) 修改，增加了批量声纹识别功能，并能将识别结果保存为可导入 [2DIPW/audio_dataset_screener](https://github.com/2DIPW/audio_dataset_screener) 中进行进一步手工筛选的 JSON 工程文件。相比原项目删除了所有与模型训练相关的源码，故如需训练自己的模型请使用原项目。

此项目为实验性项目，不保证使用效果，仅供学习与交流，并非为生产环境准备。

## 📥 部署
### 克隆
```shell
git clone https://github.com/2DIPW/audio_dataset_vpr.git
cd audio_dataset_vpr
```
### 创建虚拟环境（可选，以Anaconda为例）
```sheel
conda create -n ad-vpr python=3.8
conda activate ad-vpr
```
### 安装PyTorch
- 根据需求安装 PyTorch，详见[官网](https://pytorch.org/get-started/locally)，以下为 pip 安装 PyTorch-CUDA 版本的示例。如果已经安装，请跳过。
```shell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```
### 安装其他依赖
```shell
pip install -r requirements.txt
```
### 配置声纹识别模型
默认参数下，你需要将模型文件`model.pt`、`model.state`、`optimizer.pt`及配置文件`config.yml`置于`model`目录。你也可以通过指定`-m`和`-c`参数读取其他路径下的模型及配置文件。

- 你可以从 Hugging Face 下载我基于 [zhvoice](https://aistudio.baidu.com/aistudio/datasetdetail/133922) 数据集训练的 EcapaTdnn 模型：[2DIPW/VPR_zhvoice_EcapaTdnn](https://huggingface.co/2DIPW/VPR_zhvoice_EcapaTdnn/tree/main)
- 或者下载[原项目作者训练的更多模型](https://github.com/yeyupiaoling/VoiceprintRecognition-Pytorch#%E6%A8%A1%E5%9E%8B%E4%B8%8B%E8%BD%BD)
- 或者基于原项目[训练自己的模型](https://github.com/yeyupiaoling/VoiceprintRecognition-Pytorch#%E5%88%9B%E5%BB%BA%E6%95%B0%E6%8D%AE)

声纹识别模型的质量与识别效果直接相关，你可以自行尝试摸索最佳的模型。
## 🗝 使用方法
### 准备音频特征库
- 对于每个说话人，选取几段最具代表性的语音片段，按以下文件结构放入`labels`目录。每个说话人建立一个子目录，目录名为说话人名称，文件名不做要求。
- 由于代码是根据相似度大于给定阈值的特征片段数量来判定说话人的，请保证每个说话人特征语音片段**数量相等**。
- 如果你想将声纹识别结果用于 Audio Dataset Screener 的后续手工筛选，说话人不应超过5位，否则序号大于5的说话人会被 Audio Dataset Screener 自动忽略。

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
### 准备待分类的音频文件
- 默认参数下，你需要将所有待分类的音频片段（wav格式）放入`input`目录。你也可以通过指定`-i`参数读取其他路径下的音频片段。
### 运行识别分类
- 使用`infer.py`
    ```shell
    python infer.py
    ```
    可指定的参数:
    - `-m` | `--model_path`: 存放声纹识别模型的目录。默认值：`model/`
    - `-c` | `--configs`: 模型配置文件的路径。默认值：`model/config.yml`
    - `-d` | `--device`: 推理设备，gpu或cpu。默认值：`gpu`
    - `-l` | `--label_path`: 存放音频特征库的目录。默认值：`labels/`
    - `-t` | `--threshold`: 判定阈值，若置信度大于该值则认为特征相符。默认值：`0.6`
    - `-i` | `--input_path`: 存放待分类音频文件的目录。默认值：`input/`
    - `-o` | `--output_path`: 存放分类结果的目录。默认值：`output/`

- 识别结束后，输入的音频文件将会被移动至`output`目录下的以`VPR_Result_YYYYMMDD_HHMMSS`格式命名的目录中，识别为不同说话人的音频文件将会移动至对应说话人名称的目录，未被识别的音频文件会移至`Unrecognized`文件夹。
- 识别结果也将保存为`result.json`文件，可使用 Audio Dataset Screener 导入进行进一步的手工筛选。

## ⚖ 开源协议
原项目基于 [Apache License 2.0](https://github.com/yeyupiaoling/VoiceprintRecognition-Pytorch/blob/develop/LICENSE) 开源，按照该协议，本项目中原项目的源码附带文件修改说明（MODIFICATION_STATEMENT）。

本项目基于 [GNU General Public License v3.0](https://github.com/2DIPW/audio_dataset_vpr/blob/master/LICENSE) 开源

*世界因开源更精彩*
## 📃 参考文献
```
@inproceedings{desplanques2020ecapa,
  title={{ECAPA-TDNN: Emphasized Channel Attention, propagation and aggregation in TDNN based speaker verification}},
  author={Desplanques, Brecht and Thienpondt, Jenthe and Demuynck, Kris},
  booktitle={Interspeech 2020},
  pages={3830--3834},
  year={2020}
}
```