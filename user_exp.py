import json
import os
import datetime


def get_raw_info(user_id):
    folder = os.path.abspath(os.path.dirname(__file__)) + "\\user_data\\"
    file = folder + str(user_id) + ".json"
    if os.path.exists(file):
        with open(file, "r") as f:
            user_info = json.loads(f.read())
            return user_info
    else:
        empty_data = {"join_date": None,
                      "exp": [
                          {"voice": 0,
                           "text": 0}
                      ]}
        return empty_data


def write_raw_info(user_id, data):
    folder = os.path.abspath(os.path.dirname(__file__)) + "\\user_data\\"
    file = folder + str(user_id) + ".json"
    with open(file, "w") as f:
        json.dump(data, f)


def get_specific_info(user_id, info_name):
    user_info = get_raw_info(user_id)
    if info_name:
        return user_info[info_name]
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


def get_join_date(user_id):
    user_info = get_raw_info(user_id)
    return user_info["join_date"]


def get_join_date_in_str(user_id):
    raw_date = get_join_date(user_id)
    if raw_date is not None:
        str_date = f"{raw_date[0]}/{raw_date[1]}/{raw_date[2]} {raw_date[3]}:{raw_date[4]}:{raw_date[5]}"
        return str_date
    else:
        return None


def joined_time(user_id):
    raw_date = get_join_date(user_id)
    if raw_date is not None:
        join_date = datetime.datetime(year=raw_date[0], month=raw_date[1], day=raw_date[2],
                                      hour=raw_date[3], minute=raw_date[4], second=raw_date[5])
        now = datetime.datetime.now()
        time_diff = now - join_date
        time_diff = f"{time_diff.days} 天， {time_diff.seconds // 3600} 小時， " \
                    f"{(time_diff.seconds // 60) % 60} 分鐘， {time_diff.seconds % 60} 秒"
        return time_diff
    else:
        return None
