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
