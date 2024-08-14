# coding=utf-8
import json
import os
import datetime
from string import hexdigits
from random import choice

base_dir = os.path.abspath(os.path.dirname(__file__))


class User:
    INIT_DATA = {
        "join_date": None,
        "exp": {"voice": 0, "text": 0},
        "level": {"voice": 0, "text": 0},
        "notify_threshold": {
            "voice": 5,
            "text": 1,
        },
        "last_notify": {"voice": 0, "text": 0},
        "voice_exp_report_enabled": False,
        "last_active_time": 0,
        "last_daily_reward_claimed": 0,
    }

    def __init__(self, user_id: [int, str]):
        self.user_id = user_id

    def get_raw_info(self, is_dict=True):
        file = os.path.join(base_dir, "user_data", str(self.user_id) + ".json")
        if is_dict:
            if os.path.exists(file):
                with open(file, "r") as f:
                    user_info = json.loads(f.read())
                    return user_info
            else:
                return self.INIT_DATA
        else:
            with open(file, "r") as f:
                return f.read()

    def write_raw_info(self, data):
        file = os.path.join(base_dir, "user_data", str(self.user_id) + ".json")
        with open(file, "w") as f:
            json.dump(data, f, indent=2)

    def get_exp(self, exp_type):
        user_info = self.get_raw_info()
        if exp_type in ("voice", "text"):
            return round(user_info["exp"][exp_type] * 10) / 10
        else:
            raise ValueError('exp_type must be either "voice" or "text"')

    def add_exp(self, exp_type, amount):
        user_info = self.get_raw_info(self.user_id)
        if exp_type in ("voice", "text"):
            user_info["exp"][exp_type] += amount
            self.write_raw_info(user_info)
        else:
            raise ValueError('exp_type must be either "voice" or "text"')

    def set_join_date(self, date):
        user_info = self.get_raw_info()
        user_info["join_date"] = date
        self.write_raw_info(user_info)

    def get_join_date(self):
        user_info = self.get_raw_info()
        return user_info["join_date"]

    def get_join_date_in_str(self):
        raw_date = self.get_join_date()
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

    def joined_time(self):
        raw_date = self.get_join_date()
        if raw_date is not None:
            join_date = datetime.datetime(
                year=raw_date[0],
                month=raw_date[1],
                day=raw_date[2],
                hour=raw_date[3],
                minute=raw_date[4],
                second=raw_date[5],
            )
            now = datetime.datetime.now()
            time_diff = now - join_date
            time_diff = (
                f"{time_diff.days} 天， {time_diff.seconds // 3600} 小時， "
                f"{(time_diff.seconds // 60) % 60} 分鐘， {time_diff.seconds % 60} 秒"
            )
            return time_diff
        else:
            return None

    def get_level(self, level_type: str):
        if level_type in ("voice", "text"):
            user_info = self.get_raw_info()
            return user_info["level"][level_type]
        else:
            raise ValueError('level_type must be either "voice" or "text"')

    def add_level(self, level_type: str, level):
        user_info = self.get_raw_info()
        user_info["level"][level_type] += level
        self.write_raw_info(user_info)

    def get_last_notify_level(self) -> dict:
        user_info = self.get_raw_info()
        last_notify_lvl = user_info.get("last_notify", {"voice": 0, "text": 0})
        return last_notify_lvl

    def set_last_notify_level(self, level_type: str, level: int):
        if level_type in ("voice", "text"):
            user_info = self.get_raw_info()
            last_notify_lvl = user_info.get("last_notify", {"voice": 0, "text": 0})
            last_notify_lvl[level_type] = level
            user_info["last_notify"] = last_notify_lvl
        else:
            raise ValueError('level_type must be either "voice" or "text"')

    def upgrade_exp_needed(self, level_type: str):
        if level_type in ("voice", "text"):
            current_level = self.get_level(level_type)
            if level_type == "text":
                exp_needed = 80 + (25 * current_level)
            else:
                exp_needed = 50 + (30 * current_level)
            return exp_needed
        else:
            raise ValueError('level_type must be either "voice" or "text"')

    def level_calc(self, level_type: str) -> bool:
        if level_type in ("voice", "text"):
            exp = self.get_exp(level_type)
            exp_needed = self.upgrade_exp_needed(level_type)
            if exp >= exp_needed:
                self.add_level(level_type, 1)
                self.add_exp(level_type, -exp_needed)
                return True
            else:
                return False
        else:
            raise ValueError('level_type must be either "voice" or "text"')

    def get_notify_threshold(self) -> dict:
        user_info = self.get_raw_info()
        threshold = user_info.get(
            "notify_threshold",
            {
                "voice": 5,
                "text": 1,
            },
        )
        return threshold

    def set_notify_threshold(self, text_lvl: int, voice_lvl: int):
        user_info = self.get_raw_info()
        user_info["notify_threshold"] = {"text": text_lvl, "voice": voice_lvl}
        self.write_raw_info(user_info)

    def notify_threshold_reached(self, level_type: str) -> bool:
        if level_type in ("voice", "text"):
            threshold = self.get_notify_threshold()[level_type]
            last_notify_lvl = self.get_last_notify_level()[level_type]
            current_lvl = self.get_level(level_type)
            if (current_lvl - last_notify_lvl) >= threshold:
                self.set_last_notify_level(level_type, current_lvl)
                return True
            else:
                return False
        else:
            raise ValueError('level_type must be either "voice" or "text"')

    def get_exp_report_enabled(self) -> bool:
        user_info = self.get_raw_info()
        return user_info.get("voice_exp_report_enabled", True)

    def set_exp_report_enabled(self, enabled: bool):
        user_info = self.get_raw_info()
        user_info["voice_exp_report_enabled"] = enabled
        self.write_raw_info(user_info)

    def get_last_active_time(self):
        user_info = self.get_raw_info()
        time = user_info["last_active_time"]
        return time

    def set_last_active_time(self, time):
        user_info = self.get_raw_info()
        user_info["last_active_time"] = time
        self.write_raw_info(user_info)

    def get_last_daily_reward_claimed(self):
        user_info = self.get_raw_info()
        try:
            time = user_info["last_daily_reward_claimed"]
        except KeyError:
            time = None
        return time

    def set_last_daily_reward_claimed(self, time):
        user_info = self.get_raw_info()
        user_info["last_daily_reward_claimed"] = time
        self.write_raw_info(user_info)


anonymous_file = os.path.join(base_dir, "user_data", "anonymous.json")


def get_anonymous_raw_data() -> dict:
    with open(anonymous_file, "r") as f:
        data = json.load(f)
    return data


def write_anonymous_raw_data(data):
    with open(anonymous_file, "w") as f:
        json.dump(data, f, indent=2)


def get_anonymous_identity(user_id: int):
    raw_data = get_anonymous_raw_data()
    try:
        identity = raw_data[str(user_id)]["identity"]
        return identity
    except KeyError:
        raise KeyError("User not found")


def set_anonymous_identity(user_id: int, identity: list[2]):
    raw_data = get_anonymous_raw_data()
    try:
        raw_data[str(user_id)]["identity"] = identity
    except KeyError:
        raw_data[str(user_id)] = {"identity": identity}
    write_anonymous_raw_data(raw_data)


def get_anonymous_last_msg_sent_time(user_id: int):
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


def set_anonymous_last_msg_sent_time(user_id: int, last_time):
    raw_data = get_anonymous_raw_data()
    try:
        raw_data[str(user_id)]["last_message_sent"] = last_time
    except KeyError:
        raise KeyError("User not found")
    write_anonymous_raw_data(raw_data)


def get_allow_anonymous(user_id: int):
    raw_data = get_anonymous_raw_data()
    try:
        allow = raw_data[str(user_id)]["allow_anonymous"]
    except KeyError:
        allow = True
    return allow


def set_allow_anonymous(user_id: int, allow: bool):
    raw_data = get_anonymous_raw_data()
    try:
        raw_data[str(user_id)]["allow_anonymous"] = allow
    except KeyError:
        raise KeyError("User not found")
    write_anonymous_raw_data(raw_data)


def get_agree_TOS_of_anonymous(user_id: int) -> bool:
    raw_data = get_anonymous_raw_data()
    try:
        allow = raw_data[str(user_id)]["agree_TOS"]
    except KeyError:
        allow = False
    return allow


def set_agree_TOS_of_anonymous(user_id: int, allow: bool):
    raw_data = get_anonymous_raw_data()
    try:
        raw_data[str(user_id)]["agree_TOS"] = allow
    except KeyError:
        raw_data[str(user_id)] = {"agree_TOS": allow}
    write_anonymous_raw_data(raw_data)


def get_daily_reward_probability() -> dict:
    file = os.path.join(base_dir, "user_data", "daily_reward_prob.json")
    if os.path.exists(file):
        with open(file, "r") as f:
            user_info = json.loads(f.read())
            return user_info
    else:
        empty_data = {10: 0, 20: 0, 50: 0, 100: 0}
        return empty_data


def add_daily_reward_probability(points: int):
    file = os.path.join(base_dir, "user_data", "daily_reward_prob.json")
    user_info = get_daily_reward_probability()
    try:
        user_info[str(points)] += 1
    except KeyError:
        user_info[str(points)] = 1
    with open(file, "w") as f:
        json.dump(user_info, f, indent=2)


announcement_file = os.path.join(base_dir, "user_data", "announcement_receivers.json")


def get_announcement_receivers() -> dict:
    if os.path.exists(announcement_file):
        with open(announcement_file, "r") as f:
            return json.loads(f.read())
    else:
        return {}


def write_announcement_receivers(data: dict):
    with open(announcement_file, "w") as f:
        json.dump(data, f, indent=2)


def edit_announcement_receiver(user_id: int, announcement_types: list):
    announcement_data = get_announcement_receivers()
    for a_type in announcement_types:
        if a_type not in ["一般公告", "緊急公告", "更新通知", "雜七雜八"]:
            raise ValueError(
                'announcement_type must be "一般公告", "緊急公告", "更新通知", "雜七雜八"'
                f"({a_type} was given)"
            )
    if not announcement_types:
        try:
            del announcement_data[str(user_id)]
        except KeyError:
            pass
    else:
        announcement_data[str(user_id)] = announcement_types
    write_announcement_receivers(announcement_data)


class RewardData:
    def __init__(self, reward_id: str):
        self.reward_id = reward_id

    @staticmethod
    def create_new_reward():
        while True:
            random_char_list = [choice(hexdigits) for _ in range(8)]
            random_char = "".join(random_char_list).upper()
            file = os.path.join(base_dir, "reward_data", random_char + ".json")
            if not os.path.exists(file):
                break
        empty_data = RewardData(random_char).get_raw_info()
        RewardData(random_char).write_raw_info(empty_data)
        return random_char

    def delete(self):
        file = os.path.join(base_dir, "reward_data", self.reward_id + ".json")
        if os.path.exists(file):
            os.remove(file)
        else:
            raise FileNotFoundError("Reward not found.")

    @staticmethod
    def get_all_reward_id() -> list:
        file = os.path.join(base_dir, "reward_data")
        return [i.split(".")[0] for i in os.listdir(file)]

    def get_raw_info(self, is_dict=True) -> dict | str:
        file = os.path.join(base_dir, "reward_data", str(self.reward_id) + ".json")
        if is_dict:
            if os.path.exists(file):
                with open(file, "r") as f:
                    user_info = json.loads(f.read())
                    return user_info
            else:
                empty_data = {
                    "title": "",
                    "description": "",
                    "reward": {"text": 0, "voice": 0},
                    "limit": {"claimed": [], "amount": None, "time": 0},
                }
                return empty_data
        else:
            with open(file, "r") as f:
                return f.read()

    def write_raw_info(self, data):
        file = os.path.join(base_dir, "reward_data", str(self.reward_id) + ".json")
        with open(file, "w") as f:
            json.dump(data, f, indent=2)

    def get_title(self):
        data = self.get_raw_info()
        return data["title"]

    def set_title(self, title: str):
        data = self.get_raw_info()
        data["title"] = title
        self.write_raw_info(data)

    def get_description(self):
        data = self.get_raw_info()
        return data["description"]

    def set_description(self, description: str):
        data = self.get_raw_info()
        data["description"] = description
        self.write_raw_info(data)

    def get_rewards(self):
        data = self.get_raw_info()
        return data["reward"]

    def set_reward(self, reward_type: str, amount: int):
        data = self.get_raw_info()
        if reward_type in ["text", "voice"]:
            data["reward"][reward_type] = amount
            self.write_raw_info(data)
        else:
            raise ValueError('reward_type must be either "text" or "voice"')

    def get_amount(self) -> int | None:
        data = self.get_raw_info()
        return data["limit"]["amount"]

    def set_amount(self, amount: int):
        data = self.get_raw_info()
        data["limit"]["amount"] = amount
        self.write_raw_info(data)

    def get_claimed_users(self) -> list:
        data = self.get_raw_info()
        return data["limit"]["claimed"]

    def add_claimed_user(self, user_id: int):
        data = self.get_raw_info()
        data["limit"]["claimed"].append(user_id)
        self.write_raw_info(data)

    def get_time_limit(self):
        data = self.get_raw_info()
        return data["limit"]["time"]

    def set_time_limit(self, time: int | None):
        data = self.get_raw_info()
        data["limit"]["time"] = time
        self.write_raw_info(data)


class MusicbotError:
    file = os.path.join(base_dir, "musicbot_error_explanation.json")

    def __init__(self, error: str):
        database = self.read_file()
        for key in database.keys():
            if key in error:
                self.exact_problem = key
                self.description = database[key]["description"]
                self.solution = database[key]["solution"]
                return
        raise KeyError("The error message cannot be explained now.")

    @staticmethod
    def read_file() -> dict:
        with open(file=MusicbotError.file, mode="r", encoding="utf-8") as f:
            return json.loads(f.read())

    def get_description(self) -> str:
        return self.description

    def get_solution(self) -> str:
        return self.solution


class SoundboardIndex:
    INIT_DATA = {
        "sounds": [
            # {"display_name": "", "description": "", "file_path": ""}
        ]
    }

    def __init__(self, guild_id: int):
        self.guild_id = guild_id

    def get_raw_info(self) -> dict:
        file = os.path.join(base_dir, "soundboard_data", str(self.guild_id), "index.json")
        if os.path.exists(file):
            with open(file, "r", encoding="utf-8") as f:
                soundboard_info = json.loads(f.read())
                return soundboard_info
        else:
            return self.INIT_DATA

    def write_raw_info(self, data):
        file = os.path.join(base_dir, "soundboard_data", str(self.guild_id), "index.json")
        with open(file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get_sounds(self) -> list:
        data = self.get_raw_info()
        return data["sounds"]

    def add_sound(self, display_name: str, file_path: str, description: str = ""):
        data = self.get_raw_info()
        sounds_list = data["sounds"]
        sounds_list.append({
            "display_name": display_name,
            "description": description,
            "file_path": file_path,
        })
        self.write_raw_info(data)

    def remove_sound(self, index: int):
        data = self.get_raw_info()
        sounds_list: list = data["sounds"]
        sounds_list.pop(index)
        self.write_raw_info(data)
