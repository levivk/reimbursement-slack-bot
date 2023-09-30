from io import TextIOWrapper
import csv
import os
import shutil
from typing import Any, Iterable, Callable, Mapping, Self, Type, Iterator
from threading import Lock


class PersistentTable:
    """
    Persistent table-like storage using a csv file

    based on: https://code.activestate.com/recipes/576642/
    """

    def __init__(
        self,
        filename: str,
        fieldnames: list[str],
        converters: Mapping[str, Callable[[str], Any] | None],
        create_new: bool = False,
    ):
        self.filename = filename
        self.fieldnames = fieldnames
        self.converters = converters
        self.items: list[dict[str, Any]] = list()

        # Create lock for thread safety
        self.lock = Lock()

        if not create_new and os.access(filename, os.R_OK):
            with open(filename, "r", newline="") as csvfile:
                self.load(csvfile)

    def sync(self) -> None:
        "Open file and write items"
        tempname = self.filename + ".tmp"
        with open(tempname, "w", newline="") as csvfile:
            try:
                self.dump(csvfile)
            except Exception:
                os.remove(tempname)
                raise
            shutil.move(tempname, self.filename)  # atomic

    def dump(self, csvfile: TextIOWrapper) -> None:
        "write items to file"
        writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
        writer.writeheader()
        writer.writerows(self.items)

    def close(self) -> None:
        self.sync()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def load(self, csvfile: Iterable[str]) -> None:
        try:
            reader = csv.DictReader(csvfile, fieldnames=self.fieldnames)
            # ensure header matches
            header_dict = next(reader)
            if list(header_dict.keys()) != list(header_dict.values()):
                raise ValueError(
                    f"Data file {self.filename} has headers {header_dict.values()} but"
                    f" expected {header_dict.keys()}"
                )

            # convert strings back to original types
            for d in reader:
                d2 = dict()
                for k in d:
                    f = self.converters[k]
                    d2[k] = f(d[k]) if f is not None else d[k]
                self.items.append(d2)

        except Exception as e:
            raise ValueError(f"Data file {self.filename} not formatted correctly or something: {e}")

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, key: int) -> dict[str, Any]:
        return self.items[key]

    def __str__(self) -> str:
        return str(self.items)

    def __iter__(self) -> Iterator[dict[str,Any]]:
        return iter(self.items)

    def append(self, **kwargs: Any) -> None:
        if set(kwargs) != set(self.fieldnames):
            raise ValueError(
                f"Attempt to append invalid row to table {self.filename}. Columns "
                f"are {sorted(kwargs)} and should be {sorted(self.fieldnames)}"
            )
        # TODO: check types against converter outputs?
        self.items.append(kwargs)
        self.sync()

    def get_lock(self) -> Lock:
        return self.lock


if __name__ == "__main__":
    import random

    converters = dict(
        text=None,
        number=int,
        random=float,
    )
    keys = list(converters.keys())
    with PersistentTable("/tmp/demo1.csv", keys, converters=converters, create_new=False) as t:
        print(t, "start")
        t.append(text="hi", number=345, random=random.random())
        print(t, "updated")
        t[2]['random'] = random.random()
        print("t[2]", t[2])

        for r in t:
            print(r)

    with open("/tmp/demo1.csv", "r") as f:
        print("\n", f.read())
