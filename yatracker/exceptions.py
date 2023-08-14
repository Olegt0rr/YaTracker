class YaTrackerError(Exception):
    """Represents base Yandex Tracker error."""


class NotAuthorizedError(YaTrackerError):
    def __init__(self) -> None:
        super().__init__(
            "The user is not authorized. Check whether all the steps "
            "described in API access were completed.",
        )


class SufficientRightsError(YaTrackerError):
    def __init__(self) -> None:
        super().__init__(
            "You do not have sufficient rights to perform this action. "
            "Double-check permissions in the Tracker interface. You "
            "need the same permissions to perform the action via the "
            "API as in the interface.",
        )


class ObjectNotFoundError(YaTrackerError):
    def __init__(self) -> None:
        super().__init__(
            "The requested object was not found. You might have entered"
            " an incorrect object ID or key value.",
        )


class AlreadyExistsError(YaTrackerError):
    def __init__(self) -> None:
        super().__init__(
            "An issue with the same value of the unique parameter already exists.",
        )
