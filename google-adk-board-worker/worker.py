from __future__ import annotations

import argparse
import asyncio

from quiet import silence

silence()

import board  # noqa: E402
from google.adk.runners import InMemoryRunner  # noqa: E402
from task_worker.agent import WORKSPACE, root_agent  # noqa: E402

TASK = "Read notes.txt, translate its contents into natural Spanish, and write the Spanish to spanish.txt."


def seed() -> int:
    """Reset the board, put notes.txt in place, and add the one goal."""
    board.reset_board()
    WORKSPACE.mkdir(exist_ok=True)
    (WORKSPACE / "spanish.txt").unlink(missing_ok=True)
    return board.add_goal(TASK)


async def run() -> None:
    runner = InMemoryRunner(agent=root_agent)
    await runner.run_debug("Please work the pending task on the board.", verbose=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Day 1 ADK board worker.")
    parser.add_argument(
        "--seed-only",
        action="store_true",
        help="Seed a fresh task without running the agent (for the adk web demo).",
    )
    args = parser.parse_args()

    goal_id = seed()
    print(f"Seeded goal {goal_id}: {TASK}\n")
    if args.seed_only:
        print("Board is ready. Run `uv run adk web` and ask the worker to work the board.")
        return

    board.claim_todo(goal_id)  # the worker picks up the goal: pending -> in_progress
    asyncio.run(run())

    print("\nBoard after the run:")
    board.show_board()

    spanish = WORKSPACE / "spanish.txt"
    if spanish.exists():
        print("\nspanish.txt:\n" + spanish.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
