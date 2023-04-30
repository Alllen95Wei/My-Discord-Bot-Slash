import json
import os
import datetime


def get_raw_info(user_id):
    file = os.path.join(os.path.abspath(os.path.dirname(__file__)), "user_data", str(user_id) + ".json")
    if os.path.exists(file):
        with open(file, "r") as f:
            user_info = json.loads(f.read())
            return user_info
    else:
        empty_data = {"join_date": None,
                      "exp":
                          {"voice": 0,
                           "text": 0},
                      "level":
                          {"voice": 0,
                           "text": 0},
                      "last_active_time": 0
                      }
        return empty_data


def write_raw_info(user_id, data):
    file = os.path.join(os.path.abspath(os.path.dirname(__file__)), "user_data", str(user_id) + ".json")
    with open(file, "w") as f:
        json.dump(data, f, indent=2)


def get_exp(user_id, exp_type):
    user_info = get_raw_info(user_id)
    if exp_type in ["voice", "text"]:
        return user_info["exp"][exp_type]
    else:
        raise ValueError("exp_type must be either \"voice\" or \"text\"")


def add_exp(user_id, exp_type, amount):
    user_info = get_raw_info(user_id)
    if exp_type in ["voice", "text"]:
        user_info["exp"][exp_type] += amount
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
        if len(str(raw_date[4])) == 1:
            min_reformat = "0" + str(raw_date[4])
        else:
            min_reformat = raw_date[4]
        if len(str(raw_date[5])) == 1:
            sec_reformat = "0" + str(raw_date[5])
        else:
            sec_reformat = raw_date[5]
        str_date = f"{raw_date[0]}/{raw_date[1]}/{raw_date[2]} {raw_date[3]}:{min_reformat}:{sec_reformat}"
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


def get_level(user_id, level_type):
    if level_type in ["voice", "text"]:
        user_info = get_raw_info(user_id)
        return user_info["level"][level_type]
    else:
        raise ValueError("level_type must be either \"voice\" or \"text\"")


def add_level(user_id, level_type, level):
    user_info = get_raw_info(user_id)
    user_info["level"][level_type] += level
    write_raw_info(user_id, user_info)


def upgrade_exp_needed(user_id, level_type):
    if level_type in ["voice", "text"]:
        current_level = get_level(user_id, level_type)
        if level_type == "text":
            exp_needed = 80 + (25 * current_level)
        else:
            exp_needed = 50 + (30 * current_level)
        return exp_needed
    else:
        raise ValueError("level_type must be either \"voice\" or \"text\"")


def level_calc(user_id, level_type):
    if level_type in ["voice", "text"]:
        exp = get_exp(user_id, level_type)
        exp_needed = upgrade_exp_needed(user_id, level_type)
        if exp >= exp_needed:
            add_level(user_id, level_type, 1)
            add_exp(user_id, level_type, -exp_needed)
            return True
        else:
            return False
    else:
        raise ValueError("level_type must be either \"voice\" or \"text\"")


def get_last_active_time(user_id):
    user_info = get_raw_info(user_id)
    time = user_info["last_active_time"]
    return time


def set_last_active_time(user_id, time):
    user_info = get_raw_info(user_id)
    user_info["last_active_time"] = time
    write_raw_info(user_id, user_info)


anonymous_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), "user_data", "anonymous.json")


def get_anonymous_raw_data() -> dict:
    global anonymous_file
    with open(anonymous_file, "r") as f:
        data = json.load(f)
    return data


def write_anonymous_raw_data(data):
    global anonymous_file
    with open(anonymous_file, "w") as f:
        json.dump(data, f, indent=2)


def get_anonymous_identity(user_id):
    raw_data = get_anonymous_raw_data()
    try:
        identity = raw_data[str(user_id)]["identity"]
        return identity
    except KeyError:
        raise KeyError("User not found")


def set_anonymous_identity(user_id, identity: list[2]):
    raw_data = get_anonymous_raw_data()
    try:
        raw_data[str(user_id)]["identity"] = identity
    except KeyError:
        raw_data[str(user_id)] = {"identity": identity}
    write_anonymous_raw_data(raw_data)


def get_anonymous_last_msg_sent_time(user_id):
    raw_data = get_anonymous_raw_data()
    try:
        user = raw_data[str(user_id)]
    except KeyError:
        raise KeyError("User not found")
    try:
        last_time = user["last_message_sent"]
    except KeyError:
        last_time = 0
    return last_time


def set_anonymous_last_msg_sent_time(user_id, last_time):
    raw_data = get_anonymous_raw_data()
    try:
        raw_data[str(user_id)]["last_message_sent"] = last_time
    except KeyError:
        raise KeyError("User not found")
    write_anonymous_raw_data(raw_data)


def get_allow_anonymous(user_id):
    raw_data = get_anonymous_raw_data()
    try:
        allow = raw_data[str(user_id)]["allow_anonymous"]
    except KeyError:
        allow = True
    return allow


def set_allow_anonymous(user_id, allow: bool):
    raw_data = get_anonymous_raw_data()
    try:
        raw_data[str(user_id)]["allow_anonymous"] = allow
    except KeyError:
        raise KeyError("User not found")
    write_anonymous_raw_data(raw_data)


def get_agree_TOS_of_anonymous(user_id) -> bool:
    raw_data = get_anonymous_raw_data()
    try:
        allow = raw_data[str(user_id)]["agree_TOS"]
    except KeyError:
        allow = False
    return allow


def set_agree_TOS_of_anonymous(user_id, allow: bool):
    raw_data = get_anonymous_raw_data()
    try:
        raw_data[str(user_id)]["agree_TOS"] = allow
    except KeyError:
        raw_data[str(user_id)] = {"agree_TOS": allow}
    write_anonymous_raw_data(raw_data)
