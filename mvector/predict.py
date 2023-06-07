import os
from io import BufferedReader

import numpy as np
import torch
import yaml
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm

from mvector import SUPPORT_MODEL
from mvector.data_utils.audio import AudioSegment
from mvector.data_utils.featurizer import AudioFeaturizer
from mvector.models.ecapa_tdnn import EcapaTdnn
from mvector.models.fc import SpeakerIdetification
from mvector.models.res2net import Res2Net
from mvector.models.resnet_se import ResNetSE
from mvector.models.tdnn import TDNN
from mvector.utils.logger import setup_logger
from mvector.utils.utils import dict_to_object

logger = setup_logger(__name__)


class MVectorPredictor:
    def __init__(self,
                 configs,
                 threshold=0.6,
                 label_path=None,
                 model_path='model/',
                 use_gpu=True):
        """
        声纹识别预测工具
        :param configs: 配置参数
        :param threshold: 判断是否为同一个人的阈值
        :param label_path: 声纹库路径
        :param model_path: 导出的预测模型文件夹路径
        :param use_gpu: 是否使用GPU预测
        """
        if use_gpu:
            assert (torch.cuda.is_available()), 'GPU not available.'
            self.device = torch.device("cuda")
        else:
            os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
            self.device = torch.device("cpu")
        # 索引候选数量
        self.cdd_num = 5
        self.threshold = threshold
        # 读取配置文件
        if isinstance(configs, str):
            with open(configs, 'r', encoding='utf-8') as f:
                configs = yaml.load(f.read(), Loader=yaml.FullLoader)
            print_arguments(configs=configs)
        self.configs = dict_to_object(configs)
        assert 'max_duration' in self.configs.dataset_conf, \
            'You are using an old version of model which is no longer supported.'
        assert self.configs.use_model in SUPPORT_MODEL, f'Model not existed：{self.configs.use_model}'
        self._audio_featurizer = AudioFeaturizer(feature_conf=self.configs.feature_conf, **self.configs.preprocess_conf)
        self._audio_featurizer.to(self.device)
        # 获取模型
        if self.configs.use_model == 'EcapaTdnn' or self.configs.use_model == 'ecapa_tdnn':
            backbone = EcapaTdnn(input_size=self._audio_featurizer.feature_dim, **self.configs.model_conf)
        elif self.configs.use_model == 'Res2Net':
            backbone = Res2Net(input_size=self._audio_featurizer.feature_dim, **self.configs.model_conf)
        elif self.configs.use_model == 'ResNetSE':
            backbone = ResNetSE(input_size=self._audio_featurizer.feature_dim, **self.configs.model_conf)
        elif self.configs.use_model == 'TDNN':
            backbone = TDNN(input_size=self._audio_featurizer.feature_dim, **self.configs.model_conf)
        else:
            raise Exception(f'{self.configs.use_model} model not existed!')
        model = SpeakerIdetification(backbone=backbone, num_class=self.configs.dataset_conf.num_speakers)
        model.to(self.device)
        # 加载模型
        if os.path.isdir(model_path):
            model_path = os.path.join(model_path, 'model.pt')
        assert os.path.exists(model_path), f"{model_path} model not existed!"
        if torch.cuda.is_available() and use_gpu:
            model_state_dict = torch.load(model_path)
        else:
            model_state_dict = torch.load(model_path, map_location='cpu')
        model.load_state_dict(model_state_dict)
        print(f"Model loaded successfully：{model_path}")
        model.eval()
        self.predictor = model.backbone

        # 声纹库的声纹特征
        self.audio_feature = None
        # 声纹特征对应的用户名
        self.users_name = []
        # 声纹特征对应的声纹文件路径
        self.users_audio_path = []
        # 加载声纹库
        self.audio_db_path = label_path
        if self.audio_db_path is not None:
            # 加载声纹库中的声纹
            self.__load_faces(self.audio_db_path)

    # 加载声纹库中的声纹
    def __load_faces(self, audio_db_path):
        # 先加载声纹特征索引
        os.makedirs(audio_db_path, exist_ok=True)
        audios_path = []
        for name in os.listdir(audio_db_path):
            audio_dir = os.path.join(audio_db_path, name)
            if not os.path.isdir(audio_dir): continue
            for file in os.listdir(audio_dir):
                audios_path.append(os.path.join(audio_dir, file).replace('\\', '/'))
        # 声纹库没数据就跳过
        if len(audios_path) == 0: return
        print("Loading label feature library...")
        input_audios = []
        for audio_path in tqdm(audios_path):
            # 如果声纹特征已经在索引就跳过
            if audio_path in self.users_audio_path: continue
            # 读取声纹库音频
            audio_segment = self._load_audio(audio_path)
            # 获取用户名
            user_name = os.path.basename(os.path.dirname(audio_path))
            self.users_name.append(user_name)
            self.users_audio_path.append(audio_path)
            input_audios.append(audio_segment.samples)
            # 处理一批数据
            if len(input_audios) == self.configs.dataset_conf.batch_size:
                features = self.predict_batch(input_audios)
                if self.audio_feature is None:
                    self.audio_feature = features
                else:
                    self.audio_feature = np.vstack((self.audio_feature, features))
                input_audios = []
        # 处理不满一批的数据
        if len(input_audios) != 0:
            features = self.predict_batch(input_audios)
            if self.audio_feature is None:
                self.audio_feature = features
            else:
                self.audio_feature = np.vstack((self.audio_feature, features))
        assert len(self.audio_feature) == len(self.users_name) == len(self.users_audio_path), 'Labels count conflict.'
        print("Label feature library loaded successfully.")

    # 声纹检索
    def __retrieval(self, np_feature):
        results = []
        for feature in np_feature:
            similarity = cosine_similarity(self.audio_feature, feature[np.newaxis, :]).squeeze()
            abs_similarity = np.abs(similarity)
            # 获取候选索引
            if len(abs_similarity) < self.cdd_num:
                candidate_idx = np.argpartition(abs_similarity, -len(abs_similarity))[-len(abs_similarity):]
            else:
                candidate_idx = np.argpartition(abs_similarity, -self.cdd_num)[-self.cdd_num:]
            # 过滤低于阈值的索引
            remove_idx = np.where(abs_similarity[candidate_idx] < self.threshold)
            candidate_idx = np.delete(candidate_idx, remove_idx)
            # 获取标签最多的值
            candidate_label_list = list(np.array(self.users_name)[candidate_idx])
            if len(candidate_label_list) == 0:
                results.append({"label": None, "similarity": None})
            else:
                max_label = max(candidate_label_list, key=candidate_label_list.count)
                idx_for_max_label = [i for i, x in enumerate(self.users_name) if x == max_label]
                similarity_for_max_label = max(abs_similarity[idx_for_max_label])
                results.append({"label": max_label, "similarity": similarity_for_max_label})
        return results

    def _load_audio(self, audio_data, sample_rate=16000):
        """加载音频
        :param audio_data: 需要识别的数据，支持文件路径，文件对象，字节，numpy。如果是字节的话，必须是完整的字节文件
        :param sample_rate: 如果传入的事numpy数据，需要指定采样率
        :return: 识别的文本结果和解码的得分数
        """
        # 加载音频文件，并进行预处理
        if isinstance(audio_data, str):
            audio_segment = AudioSegment.from_file(audio_data)
        elif isinstance(audio_data, BufferedReader):
            audio_segment = AudioSegment.from_file(audio_data)
        elif isinstance(audio_data, np.ndarray):
            audio_segment = AudioSegment.from_ndarray(audio_data, sample_rate)
        elif isinstance(audio_data, bytes):
            audio_segment = AudioSegment.from_bytes(audio_data)
        else:
            raise Exception(f'不支持该数据类型，当前数据类型为：{type(audio_data)}')
        assert audio_segment.duration >= self.configs.dataset_conf.min_duration, \
            f'Audio segment too short，minimum is {self.configs.dataset_conf.min_duration}s，current is{audio_segment.duration}s'
        # 重采样
        if audio_segment.sample_rate != self.configs.dataset_conf.sample_rate:
            audio_segment.resample(self.configs.dataset_conf.sample_rate)
        # decibel normalization
        if self.configs.dataset_conf.use_dB_normalization:
            audio_segment.normalize(target_db=self.configs.dataset_conf.target_dB)
        return audio_segment

    def predict(self,
                audio_data,
                sample_rate=16000):
        """预测一个音频的特征

        :param audio_data: 需要识别的数据，支持文件路径，文件对象，字节，numpy。如果是字节的话，必须是完整并带格式的字节文件
        :param sample_rate: 如果传入的事numpy数据，需要指定采样率
        :return: 声纹特征向量
        """
        # 加载音频文件，并进行预处理
        input_data = self._load_audio(audio_data=audio_data, sample_rate=sample_rate)
        input_data = torch.tensor(input_data.samples, dtype=torch.float32, device=self.device).unsqueeze(0)
        input_len_ratio = torch.tensor([1], dtype=torch.float32, device=self.device)
        audio_feature, _ = self._audio_featurizer(input_data, input_len_ratio)
        # 执行预测
        feature = self.predictor(audio_feature).data.cpu().numpy()[0]
        return feature

    def predict_batch(self, audios_data, sample_rate=16000):
        """预测一批音频的特征

        :param audios_data: 需要识别的数据，支持文件路径，文件对象，字节，numpy。如果是字节的话，必须是完整并带格式的字节文件
        :param sample_rate: 如果传入的事numpy数据，需要指定采样率
        :return: 声纹特征向量
        """
        audios_data1 = []
        for audio_data in audios_data:
            # 加载音频文件，并进行预处理
            input_data = self._load_audio(audio_data=audio_data, sample_rate=sample_rate)
            audios_data1.append(input_data.samples)
        # 找出音频长度最长的
        batch = sorted(audios_data1, key=lambda a: a.shape[0], reverse=True)
        max_audio_length = batch[0].shape[0]
        batch_size = len(batch)
        # 以最大的长度创建0张量
        inputs = np.zeros((batch_size, max_audio_length), dtype='float32')
        input_lens_ratio = []
        for x in range(batch_size):
            tensor = audios_data1[x]
            seq_length = tensor.shape[0]
            # 将数据插入都0张量中，实现了padding
            inputs[x, :seq_length] = tensor[:]
            input_lens_ratio.append(seq_length / max_audio_length)
        audios_data = torch.tensor(inputs, dtype=torch.float32, device=self.device)
        input_lens_ratio = torch.tensor(input_lens_ratio, dtype=torch.float32, device=self.device)
        audio_feature, _ = self._audio_featurizer(audios_data, input_lens_ratio)
        # 执行预测
        features = self.predictor(audio_feature).data.cpu().numpy()
        return features

    def recognition(self, audio_data, threshold=None, sample_rate=16000):
        """声纹识别
        :param audio_data: 需要识别的数据，支持文件路径，文件对象，字节，numpy。如果是字节的话，必须是完整的字节文件
        :param threshold: 判断的阈值，如果为None则用创建对象时使用的阈值
        :param sample_rate: 如果传入的事numpy数据，需要指定采样率
        :return: 识别的用户名称，如果为None，即没有识别到用户
        """
        if threshold:
            self.threshold = threshold
        feature = self.predict(audio_data, sample_rate=sample_rate)
        result = self.__retrieval(np_feature=[feature])[0]
        return result["label"], result["similarity"]
