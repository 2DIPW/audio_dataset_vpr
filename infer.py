import argparse
import os
import json
import shutil
from datetime import datetime
from scipy.io import wavfile
from mvector.predict import MVectorPredictor


def if_not_mkdir(path):
    if not os.path.exists(path):
        os.mkdir(path)


def about():
    print(r"""
            ___             ___          ____        __                  __     _    ______  ____ 
           /   | __  ______/ (_)___     / __ \____ _/ /_____ _________  / /_   | |  / / __ \/ __ \
          / /| |/ / / / __  / / __ \   / / / / __ `/ __/ __ `/ ___/ _ \/ __/   | | / / /_/ / /_/ /
         / ___ / /_/ / /_/ / / /_/ /  / /_/ / /_/ / /_/ /_/ (__  )  __/ /_     | |/ / ____/ _, _/ 
        /_/  |_\__,_/\__,_/_/\____/  /_____/\__,_/\__/\__,_/____/\___/\__/     |___/_/   /_/ |_|  

Audio Dataset Voiceprint Recognition Classifier by 2DIPW based on yeyupiaoling/VoiceprintRecognition-Pytorch
     Licensed under GNU General Public License v3. Open source leads the world to a brighter future!

""")


if __name__ == "__main__":
    about()
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--model_path', type=str, default="model/", help="Path to model.")
    parser.add_argument('-c', '--configs', type=str, default="model/config.yml", help="Path to model config file.")
    parser.add_argument('-d', '--device', type=str, default="gpu", help='Device to use, gpu or cpu.')
    parser.add_argument('-l', '--label_path', type=str, default="labels/", help="Path to Voice feature library.")
    parser.add_argument('-t', '--threshold', type=float, default=0.6, help="Threshold for judging compliance.")
    parser.add_argument('-i', '--input_path', type=str, default="input/", help="Path to input files.")
    parser.add_argument('-o', '--output_path', type=str, default="output/", help="Path to output files.")

    args = parser.parse_args()

    predictor = MVectorPredictor(configs=args.configs,
                                 threshold=args.threshold,
                                 label_path=args.label_path,
                                 model_path=args.model_path,
                                 use_gpu=True if args.device == "gpu" else False)

    if not os.path.exists(args.input_path):
        raise Exception("Input path not existed.")

    # Get labels dict from label_path
    labels_list = [f for f in os.listdir(args.label_path) if os.path.isdir(os.path.join(args.label_path, f))]
    labels_dict = {}
    for i, label in enumerate(labels_list):
        labels_dict[label] = i + 1
    print(f"Feature labels:{labels_dict}")

    # Get input files list from input_path
    input_files = []
    for root, dirs, files in os.walk(args.input_path):
        input_files += [os.path.abspath(os.path.join(root, f)) for f in files if f.split('.')[-1].upper() in ["WAV"]]

    input_files_amount = len(input_files)

    result_dicts_list = []

    for i, file in enumerate(input_files):
        sample_rate, audio_data = wavfile.read(file)
        label, similarity = predictor.recognition(audio_data=audio_data, sample_rate=sample_rate)
        if label:
            print(
                f"\033[32m[{i+1}/{input_files_amount}]\033[0m \033[33m{os.path.basename(file)}\033[0m is recognized as speaker \033[31m{label}\033[0m, the max similarity is \033[34m{similarity}\033[0m.")
            result_dicts_list.append(
                {"Filepath": file, "Label": labels_dict[label], "Similarity": float(similarity)})
        else:
            print(
                f"\033[32m[{i+1}/{input_files_amount}]\033[0m \033[33m{os.path.basename(file)}\033[0m could not be recognized as any speaker.")
            result_dicts_list.append(
                {"Filepath": file, "Label": 0, "Similarity": 0})

    output_path_for_this_run = os.path.join(args.output_path, datetime.now().strftime("VPR_Result_%Y%m%d_%H%M%S"))
    if_not_mkdir(output_path_for_this_run)
    json_path = os.path.abspath(os.path.join(output_path_for_this_run, "result.json"))

    # Move input files to category folders
    print("Moving input files to category folders...")
    folder_list_without_unrecognized = [os.path.abspath(os.path.join(output_path_for_this_run, label)) for label in labels_list]
    folder_list = [os.path.abspath(os.path.join(output_path_for_this_run, "Unrecognized"))] + folder_list_without_unrecognized

    for folder in folder_list:
        if_not_mkdir(folder)
    for result in result_dicts_list:
        destination_folder = folder_list[result["Label"]]
        try:
            shutil.move(result["Filepath"], destination_folder)
            result["Filepath"] = os.path.abspath(os.path.join(destination_folder, os.path.basename(result["Filepath"])))
        except Exception as e:
            print(e)

    # Write result json file to output_path
    with open(json_path, "w") as f:
        json.dump({"Labels": {str(i+1): folder for i, folder in enumerate(folder_list_without_unrecognized)}, "Files": result_dicts_list}, f, indent=4)
        print(f"Result json is saved as {json_path}")
