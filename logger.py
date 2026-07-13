LOG_BUFFER = []


def log(msg: str):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(str(msg).encode("ascii", "replace").decode("ascii"))
    LOG_BUFFER.append(msg)

    if len(LOG_BUFFER) > 500:
        LOG_BUFFER.pop(0)