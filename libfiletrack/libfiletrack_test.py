import json
import pickle
from typing import List

from libfiletrack import FileTrack


def main():

    # To execute this change directory to the testdata folder

    filetrack = FileTrack()
    filetrack.init()
    events = filetrack.status()

    for event in events:
        print(str(event))

    filetrack.commit(events)

    return 0

if __name__ == "__main__":
    main()