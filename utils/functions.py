def safe_int(string, default=None):
    try:
        return int(string)
    except ValueError:
        return default
