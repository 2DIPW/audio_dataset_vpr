import argparse
import os
from scipy.io import wavfile
from mvector.predict import MVectorPredictor

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--configs', type=str, default="model/config.yml", help="Path to model config file.")
    parser.add_argument('-g', '--use_gpu', action='store_true', default=True, help='Enable GPU accelerate')
    parser.add_argument('-d', '--audio_db_path', type=str, default="tags/", help="Path to audio db.")
    parser.add_argument('-t', '--threshold', type=float, default="0.6", help="Threshold for judging compliance.")
    parser.add_argument('-m', '--model_path', type=str, default="model/", help="Path to model.")
    parser.add_argument('-i', '--input_path', type=str, default="input/", help="Path to input data.")
    parser.add_argument('-o', '--output_path', type=str, default="output/", help="Path to output data.")

    args = parser.parse_args()

    # 获取识别器
    predictor = MVectorPredictor(configs=args.configs,
                                 threshold=args.threshold,
                                 audio_db_path=args.audio_db_path,
                                 model_path=args.model_path,
                                 use_gpu=args.use_gpu)

    input_files = [f for f in os.listdir(args.input_path) if (not os.path.isdir(f)) and f.endswith(".wav")]

    for file in input_files:
        sample_rate, audio_data = wavfile.read(file)
        name = predictor.recognition(audio_data=audio_data, sample_rate=sample_rate)
        if name:
            print(f"{file} is recognized as speaker {name}, the similarity is")
        else:
            print(f"{file} could not be recognized as any speaker.")

