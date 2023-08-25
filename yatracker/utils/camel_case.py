def camel_case(string: str) -> str:
    """Convert string into camel case."""
    if not string:
        return string

    string = string.replace("_", "-")
    lst = string.split("-")
    for i in range(len(lst)):
        if i == 0:
            continue
        lst[i] = lst[i].capitalize()

    return "".join(lst)
