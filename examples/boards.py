import asyncio
from datetime import date

from yatracker import YaTracker
from yatracker.types import BoardColumnParams

# CAUTION! Don't store credentials in your code!
ORG_ID = ...
TOKEN = ...


async def main() -> None:
    """Run boards example.

    This way you may create a board with columns, list its columns
    and manage a sprint.
    """
    # define tracker (once)
    tracker = YaTracker(ORG_ID, TOKEN)

    # create a board with two columns
    board = await tracker.create_board(
        name="New Board",
        sprints_available=True,
        columns=[
            BoardColumnParams(name="To Do", statuses=["open"]),
            BoardColumnParams(name="Done", statuses=["closed"]),
        ],
    )
    print(board.id, board.name)

    # list board columns (also available as `await board.get_columns()`)
    columns = await tracker.get_board_columns(board.id)
    for column in columns:
        print(column.id, column.name)

    # create a sprint and start it
    sprint = await tracker.create_sprint(
        name="Sprint 1",
        board_id=board.id,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 14),
    )
    sprint = await tracker.start_sprint(sprint.id, sprint.version)
    print(sprint.status)

    # don't forget to close tracker on app shutdown (once)
    await tracker.close()


if __name__ == "__main__":
    asyncio.run(main())
