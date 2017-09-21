#
# Copyright (c) 2017 Ognjen Galić
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE-
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import hashlib
import os
from enum import Enum
from typing import List


class File:

    location: str = None
    filename: str = None
    checksum: str = None
    checksum_previous: str = None

    def __eq__(self, o: object) -> bool:
        comp: File = o
        return comp.filename == self.filename and comp.location == self.location

    def __str__(self) -> str:
        return "{}/{} ({})".format(self.location, self.filename, self.checksum)


class EventType(Enum):

    DELETE = "D"
    CREATE = "C"
    MODIFY = "H"


class Event:

    id: int = 0
    type: EventType = None
    file: File = None
    optional1: str = None
    optional2: str = None

    def __str__(self) -> str:
        return "id: {} type: {} file: {}".format(self.id, self.type, self.file)


class FileTrack:

    index_files: List[File] = []
    index_events: List[Event] = []
    event_id = 0

    def status(self) -> List[Event]:
        """
        This method returns the pending @see Events to be written to disk or
        analyzed by the user.
        :return: List of pending events
        """

        disk_files = self._walk_tree(".")
        events: List[Event] = []

        new_files = [item for item in disk_files if item not in self.index_files]
        deleted_files = [item for item in self.index_files if item not in disk_files]
        changed_files = []

        for index_f in self.index_files:
            for file_f in disk_files:
                if index_f.filename == file_f.filename and \
                                index_f.location == file_f.location and \
                                index_f.checksum != file_f.checksum:
                    file_f.checksum_previous = index_f.checksum
                    changed_files.append(file_f)

        for new_file in new_files:
            event = Event()
            event.id = self.event_id
            event.file = new_file
            event.type = EventType.CREATE
            self.event_id += 1
            events.append(event)

        for deleted_file in deleted_files:
            event = Event()
            event.id = self.event_id
            event.file = deleted_file
            event.type = EventType.DELETE
            self.event_id += 1
            events.append(event)

        for changed_file in changed_files:
            event = Event()
            event.id = self.event_id
            event.file = changed_file
            event.type = EventType.MODIFY
            event.optional1 = changed_file.checksum_previous
            self.event_id += 1
            events.append(event)

        return events

    def init(self) -> None:
        """
        Reads the index and changes files into memory for manipulation
        or creates them if they do not exists.
        :return: None
        """

        if os.path.exists(".filetrack"):
            print("Refusing to create new repository in existing one, loading metadata")
            self.index_files = self._read_index_from_disk()
            self.index_events = self._read_events_from_disk()
            return
        else:
            os.mkdir(".filetrack")

        print("Initializing filetrack in .filetrack")

        # Create a new index and events file

        self.index_files = self._walk_tree(".")

        for file in self.index_files:
            event = Event()
            event.type = EventType.CREATE
            event.file = file
            event.id = self.event_id
            self.index_events.append(event)
            self.event_id += 1

        self._write_index_to_disk()
        self._write_events_to_disk()

    def commit(self, data: List[Event]) -> None:
        """
        Commits the passed list of events to disk. To be used with
        status()
        :param data: list of events gathered by status() to be commited to disk
        :return: None
        """


        if len(data) == 0:
            print("Nothing to commit...")
            return

        self.index_files = self._walk_tree(".")
        for event in data:
            self.index_events.append(event)

        self._write_events_to_disk()
        self._write_index_to_disk()

    def _walk_tree(self, path: str) -> List[File]:
        files: List[File] = []
        for file in os.walk(path):
            path: str = file[0]
            files_subdir: List[str] = file[2]
            for subfile in files_subdir:
                if ".filetrack" in path:
                    continue
                file_obj = File()
                file_obj.location = path
                file_obj.filename = subfile
                file_obj.checksum = self._sha1sum_file("{}/{}".format(file_obj.location, file_obj.filename))
                files.append(file_obj)
        return files

    @staticmethod
    def _sha1sum_file(path):
        h = hashlib.sha1()
        with open(path, 'rb', buffering=0) as f:
            for b in iter(lambda: f.read(128 * 1024), b''):
                h.update(b)
        return h.hexdigest()

    def _write_index_to_disk(self):

        if os.path.exists(".filetrack/index"):
            index_file = open(".filetrack/index", "w+", encoding="utf-8")
        else:
            index_file = open(".filetrack/index", "x", encoding="utf-8")

        for file in self.index_files:
            index_file.write("{}|{}|{}\n".format(file.location, file.filename, file.checksum))

        index_file.write("EOF\n")
        index_file.close()

    @staticmethod
    def _read_index_from_disk() -> List[File]:

        file_return: List[File] = []
        index_file = open(".filetrack/index", "r", encoding="utf-8")

        for line in index_file.readlines():
            line_array = line.replace("\n", "").split("|")

            if line_array[0] == "EOF":
                break

            file_obj = File()
            file_obj.location = line_array[0]
            file_obj.filename = line_array[1]
            file_obj.checksum = line_array[2]
            file_return.append(file_obj)

        return file_return

    def _read_events_from_disk(self):

        events_file = open(".filetrack/events", "r", encoding="utf-8")

        event_arr: List[Event] = []

        for line in events_file.readlines():
            if line == "EOF\n":
                break
            line_segments = line.replace("\n", "").split("|")

            event = Event()
            event.id = int(line_segments[0])
            event.type = eval(line_segments[1])
            event.file = File()
            event.file.location = line_segments[2]
            event.file.filename = line_segments[3]
            event.file.checksum = line_segments[4]
            event.optional1 = line_segments[5]
            event.optional2 = line_segments[6]
            event_arr.append(event)

        self.event_id = event_arr[-1].id + 1
        return event_arr

    def _write_events_to_disk(self):

        if os.path.exists(".filetrack/events"):
            events_file = open(".filetrack/events", "w+", encoding="utf-8")
        else:
            events_file = open(".filetrack/events", "x", encoding="utf-8")

        for event in self.index_events:
            events_file.write("{}|{}|{}|{}|{}|{}|{}\n".format(event.id,
                                                              event.type,
                                                              event.file.location,
                                                              event.file.filename,
                                                              event.file.checksum,
                                                              event.optional1,
                                                              event.optional2))

        events_file.write("EOF\n")
        events_file.close()

        pass

    def get_history(self) -> List[Event]:
        return self._read_events_from_disk()