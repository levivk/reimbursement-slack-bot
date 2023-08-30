from io import TextIOWrapper
import pickle, json, csv, os, shutil
from typing import IO, Any, Iterable, Callable, Union, Mapping

class PersistentTable():
    '''
    Persistent table-like storage using a csv file

    based on: https://code.activestate.com/recipes/576642/
    '''

    def __init__(self, filename: str, fieldnames: list[str], converters: Mapping[str, Callable[[str], Any] | None], create_new: bool = False):
        self.filename = filename
        self.fieldnames = fieldnames
        self.converters = converters
        self.items: list[dict[str,Any]] = list()

        if not create_new and os.access(filename, os.R_OK):
            with open(filename, 'r', newline='') as csvfile:
                self.load(csvfile)

    def sync(self):
        'Open file and write items'
        tempname = self.filename + '.tmp'
        with open(tempname, 'w', newline='') as csvfile:
            try:
                self.dump(csvfile)
            except Exception:
                os.remove(tempname)
                raise
            shutil.move(tempname, self.filename)    # atomic

    def dump(self, csvfile: TextIOWrapper):
        'write items to file'
        writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
        writer.writeheader()
        writer.writerows(self.items)

    def close(self):
        self.sync()

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.close()

    def load(self, csvfile: Iterable[str]):
        try:
            reader = csv.DictReader(csvfile, fieldnames=self.fieldnames)
            # ensure header matches
            header_dict = next(reader)
            if(list(header_dict.keys()) != list(header_dict.values())):
                raise ValueError(f'Data file {self.filename} has headers {header_dict.values()} but expected {header_dict.keys()}')

            # convert strings back to original types
            for d in reader:
                d2 = dict()
                for k in d:
                    f = self.converters[k]
                    d2[k] = f(d[k]) if f is not None else d[k]
                self.items.append(d2)

        except Exception:
            raise ValueError(f'Data file {self.filename} not formatted correctly')

    def __len__(self):
        return len(self.items)

    def __getitem__(self, key):
        return self.items[key]

    def __str__(self):
        return str(self.items)

    def append(self, **kwargs):
        if set(kwargs) != set(self.fieldnames):
            raise ValueError(f'Attempt to append invalid row to table {self.filename}. Columns are {sorted(kwargs)} and should be {sorted(self.fieldnames)}')
        # TODO: check types against converter outputs?
        self.items.append(kwargs)
        self.sync()


    


if __name__ == '__main__':
    import random

    # Make and use a persistent dictionary
    # with PersistentDict('/tmp/demo.json', 'c', format='json') as d:
    #     print(d, 'start')
    #     d['abc'] = '123'
    #     d['rand'] = random.randrange(10000)
    #     d['foo'] = 'birb'
    #     print(d, 'updated')

    # # Show what the file looks like on disk
    # with open('/tmp/demo.json', 'rb') as f:
    #     print(f.read())
    # def convert_int(s: str) -> int:
    #     return int(s)

    # def convert_float(s: str) -> float:
    #     return float(s)


    converters = dict(
        text = None,
        number = int,
        random = float,
    )
    keys = list(converters.keys())
    with PersistentTable('/tmp/demo1.csv', keys, converters=converters, create_new=False) as t:
        print(t, 'start')
        # d = dict()
        # d[keys[0]] = 'mom'
        # d[keys[1]] = 123
        # d[keys[2]] = random.random()
        t.append(text='hi', number=345, random=random.random())
        print(t, 'updated')
        print('t[2]', t[-1])

    with open('/tmp/demo1.csv', 'r') as f:
        print('\n', f.read())
