def camel_case(string: str) -> str:
    """Convert string into camel case.

    This intentionally differs from ``pydantic.alias_generators.to_camel``:
    it also strips a trailing underscore, e.g. ``camel_case("filter_")
    == "filter"`` and ``camel_case("type_") == "type"``. This is
    load-bearing for kwargs that shadow Python keywords/builtins
    (``filter_``, ``type_``, ...), so do not replace this with
    ``pydantic.alias_generators.to_camel``.
    """
    if not string:
        return string

    string = string.replace("_", "-")
    lst = string.split("-")
    for i in range(len(lst)):
        if i == 0:
            continue
        lst[i] = lst[i].capitalize()

    return "".join(lst)
