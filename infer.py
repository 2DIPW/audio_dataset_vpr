import argparse
import os
import json
from datetime import datetime
from scipy.io import wavfile
from mvector.predict import MVectorPredictor


def if_not_mkdir(path):
    if not os.path.exists(path):
        os.mkdir(path)


if __name__ == "__main__":
    print("===Audio Dataset Voiceprint Recognition by 2DIPW===")
    print("Based on yyupiaoling/VoiceprintRecognition-Pytorch")
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--configs', type=str, default="model/config.yml", help="Path to model config file.")
    parser.add_argument('-g', '--use_gpu', action='store_true', default=True, help='Enable GPU accelerate')
    parser.add_argument('-l', '--label_path', type=str, default="labels/", help="Path to audio db.")
    parser.add_argument('-t', '--threshold', type=float, default="0.6", help="Threshold for judging compliance.")
    parser.add_argument('-m', '--model_path', type=str, default="model/", help="Path to model.")
    parser.add_argument('-i', '--input_path', type=str, default="input/", help="Path to input data.")
    parser.add_argument('-o', '--output_path', type=str, default="output/", help="Path to output data.")

    args = parser.parse_args()

    predictor = MVectorPredictor(configs=args.configs,
                                 threshold=args.threshold,
                                 label_path=args.label_path,
                                 model_path=args.model_path,
                                 use_gpu=args.use_gpu)

    if not os.path.exists(args.input_path):
        raise Exception("Input path not existed.")

    # Get labels dict from label_path
    labels_list = [f for f in os.listdir(args.label_path) if os.path.isdir(f)]
    labels_dict = {}
    for i, label in enumerate(labels_list): labels_dict[label] = i + 1

    # Get input files list from input_path
    input_files = [f for f in os.listdir(args.input_path) if (not os.path.isdir(f)) and f.endswith(".wav")]
    input_files_amount = len(input_files)

    result_dicts_list = []

    for i, file in enumerate(input_files):
        sample_rate, audio_data = wavfile.read(file)
        label, similarity = predictor.recognition(audio_data=audio_data, sample_rate=sample_rate)
        if label:
            print(f"[{i}/{input_files_amount}] {file} is recognized as speaker {label}, the max similarity is {similarity}.")
            result_dicts_list.append(
                {"filename": file, "filepath": os.path.join(args.input_path, file), "label": labels_dict[label],
                 "similarity": similarity})
        else:
            print(f"[{i}/{input_files_amount}] {file} could not be recognized as any speaker.")
            result_dicts_list.append(
                {"filename": file, "filepath": os.path.join(args.input_path, file), "label": None, "similarity": None})

    # Write result json file to output_path
    if_not_mkdir(args.output_path)
    result_filepath = os.path.join(args.output_path, datetime.now().strftime("%Y%m%d-%H%M%S.json"))
    with open(result_filepath, "w") as f:
        json.dump({"labels": labels_dict, "files": result_dicts_list}, f)
        print(f"Result json is saved as {result_filepath}")


