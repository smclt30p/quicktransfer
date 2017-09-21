libfiletrack - File Tracking Library

This library is used to track file movement and change events.
The actual changes to the files are not tracked, just that they 
HAVE changed.

There are 2 main files that make libfiletrack work, the "index"
file and the "changes" file.

* The Index File

The index file contains a list of the files that were in the folder
since the last commit. It's a simple ASCII file that contains file
paths.

* The Changes File

The changes file contains a list of changes that were made at some
point in time. A group of changes is called a commit. A commit has
a timestamp, checksum and message. The format of the file is specific,
it's not XML or JSON or any standard serialization format.

* How To Detect File Changes 

The index file is created at the initialization of the repository. 
The index file contains a list of the files in the current directory.

The index stores the file path, the name, and the checksum.

There is 3 file operation scenarios possible:

1. New File
   A file is considered new if it is inside the directory and the new file is
   not inside the index.

2. File Deleted (Moved/Renamed)
   A file is considered deleted if it inside the index, but is NOT inside the
   active directory.

3. File modified
   A file is considered modified if it is inside the index, on the disk, and
   there is a checksum mismatch.

For other scenarios such as move/rename, a hard delete and re-create is used.

* The Index File Format

The index file is in the current format:

<path>|<filename>|<checksum><LF>

For example:

.|1.txt|da39a3ee5e6b4b0d3255bfef95601890afd80709
.|2.txt|da39a3ee5e6b4b0d3255bfef95601890afd80709
.|3.txt|942a1486aeb37340f5545ad3ee46645f516e1818
EOF

The index file is overwritten each time it is saved.

* The Changes File

The changes fle is in the current format:

<id>|<event>|<filepath>|<filename>|<checksum>|<optional1>|<optional2><LF>

There is 3 events:

CREATE, DELETE and MODIFY

For example:

0|EventType.CREATE|.|1.txt|da39a3ee5e6b4b0d3255bfef95601890afd80709|None|None
1|EventType.CREATE|.|2.txt|da39a3ee5e6b4b0d3255bfef95601890afd80709|None|None
2|EventType.CREATE|.|3.txt|942a1486aeb37340f5545ad3ee46645f516e1818|None|None
3|EventType.MODIFY|.|5.txt|0d989ff86bc59be692a7c54c074f7dc43ed05c5a|942a1486aeb37340f5545ad3ee46645f516e1818|None
EOF

* Making a commit

A commit is an action of writing a new file hierarchy to the index file
and adding a commit to the changes log.