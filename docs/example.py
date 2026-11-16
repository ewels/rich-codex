"""Example Python file for the rich-codex docs to render.

It doesn't change, so the screenshots of it don't either.
"""

import logging
import random
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger("example")

GREETINGS = ["Hello", "Hej", "Bonjour", "Hola", "Ciao"]


def pick_greeting(seed: int | None = None) -> str:
    """Pick a greeting, the same one every time for a given seed."""
    return random.Random(seed).choice(GREETINGS)


class Greeter:
    """Greet people, and remember who has been greeted."""

    def __init__(self, name: str) -> None:
        """Set up a greeter that signs its greetings with 'name'."""
        self.name = name
        self.greeted: list[str] = []

    def greet(self, person: str, seed: int | None = None) -> str:
        """Greet someone, and log it."""
        message = f"{pick_greeting(seed)} {person}, from {self.name}!"
        self.greeted.append(person)
        log.info(message)
        return message


@dataclass
class Guestbook:
    """Write the people who have been greeted to a file."""

    path: Path
    names: list[str] = field(default_factory=list)

    def sign(self, greeter: Greeter) -> None:
        self.names.extend(greeter.greeted)
        self.path.write_text("\n".join(sorted(set(self.names))) + "\n")


if __name__ == "__main__":
    greeter = Greeter("rich-codex")
    print(greeter.greet("world", seed=42))
