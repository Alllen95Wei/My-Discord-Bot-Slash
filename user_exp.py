import json
import os


def get_raw_info(user_id):
    folder = os.path.abspath(os.path.dirname(__file__)) + "\\user_data\\"
    file = folder + str(user_id) + ".json"
    if os.path.exists(file):
        with open(file, "r") as f:
            user_info = json.load(f)
            return user_info
    else:
        with open(file, "w") as f:
            user_info = {"join_date": None,
                         "exp": [
                             {"voice": 0,
                              "text": 0}
                         ]}
            json.dump(user_info, f)
            return user_info


def write_raw_info(user_id, data):
    folder = os.path.abspath(os.path.dirname(__file__)) + "\\user_data\\"
    file = folder + str(user_id) + ".json"
    with open(file, "w") as f:
        json.dump(data, f)


def get_specific_info(user_id, info):
    user_info = get_raw_info(user_id)
    if info:
        return user_info[info]
    else:
        return user_info


def get_exp(user_id, exp_type: ["voice", "text"]):
    user_info = get_raw_info(user_id)
    if exp_type in ["voice", "text"]:
        return user_info["exp"][0][exp_type]
    else:
        raise ValueError("exp_type must be either \"voice\" or \"text\"")


def add_exp(user_id, exp_type: ["voice", "text"], amount):
    user_info = get_raw_info(user_id)
    if exp_type in ["voice", "text"]:
        user_info["exp"][0][exp_type] += amount
        write_raw_info(user_id, user_info)
    else:
        raise ValueError("exp_type must be either \"voice\" or \"text\"")


def set_join_date(user_id, date):
    user_info = get_raw_info(user_id)
    user_info["join_date"] = date
    write_raw_info(user_id, user_info)
