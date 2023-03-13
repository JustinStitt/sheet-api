import re


def sanitize(func):
    def wrapper(*args, **kwargs):
        sanitized_args = []
        for arg in args:
            if type(arg) is str and "woc" not in arg and "<" not in arg:
                arg = re.sub(r"[^a-zA-Z]", "", arg).lower()
            # if type(arg) is str and "<" not in arg:
            if type(arg) is str and "<" in arg:
                continue
            sanitized_args.append(arg)
        return func(*sanitized_args, **kwargs)

    return wrapper
