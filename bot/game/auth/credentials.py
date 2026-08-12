import os
import random
import string


def generate_credentials(profile_num: int, save_path="bot/data/login_data.txt"):
    username = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    password = "".join(
        random.choices(string.ascii_letters + string.digits + string.punctuation, k=10)
    )

    line = f"{profile_num},{username},{password}\n"

    os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)

    with open(save_path, "a", encoding="utf-8") as f:
        f.write(line)

    return username, password


def read_credentials(file_path="bot/data/login_data.txt"):
    creds = {}
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(",", 2)
            if len(parts) != 3:
                continue
            prof_num = int(parts[0].strip())
            login = parts[1].strip()
            password = parts[2].strip()
            creds[prof_num] = (login, password)
    return creds
