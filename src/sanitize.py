import re


def sanitize(func):
    def wrapper(*args, **kwargs):
        sanitized_args = []
        for arg in args:
            if type(arg) is str and "code" not in arg:
                arg = re.sub(r"[^a-zA-Z]", "", arg).lower()
            if type(arg) is str and len(arg):
                sanitized_args.append(arg)
        return func(*sanitized_args, **kwargs)

    return wrapper
