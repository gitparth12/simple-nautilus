# simple-nautilus
_For my INFO1112 assignment 2 at The University of Sydney_

An interactive application in Python that allows the user to send commands to a file management application and receive outputs. The application largely mocks common Unix commands such as ls, cd, pwd, and so on.

### On the high level, the application is capable of:

1. Interpreting commands received on standard input.
2. Producing messages on standard output.
3. Maintaining some data structure that keeps track of a virtual name space.
4. Creating, delete and move virtual files and folders during program run time.
5. Supporting user and permission management in addition to file management.

**Note** that the system is incapable of storing content but purely the file system structure. This is an intensional design and therefore the size of a file is not defined and is omitted in the system. Similarly, the concept of time and group is omitted intentionally.
