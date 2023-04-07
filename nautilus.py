import sys
import shlex

# File Parent Class
class File():
    # name of the directory or file
    name: str
    # parent is a directory
    parent = None
    # absolute path of the directory or file
    path: str
    # current user upon creation determines owner
    owner: str
    # permission of the directory or file
    perms: str
    def __init__(self, name: str, parent):
        self.name = name
        self.parent = parent
        self.path = self.parent.path + "/" + name
        # Owner set inside the touch method
        self.perms = "-rw-r--"
        self.parent.add(self)

# Directory Child Class
class Directory():
    # name of the directory or file
    name: str
    # parent is a directory
    parent = None
    # absolute path of the directory or file
    path: str
    # current user upon creation determines owner
    owner: str
    # permission of the directory or file
    perms: str
    # List to store all contents of the directory
    contents: list
    def __init__(self, name: str, parent):
        self.contents = []
        self.name = name
        self.parent = parent
        if not name == "/":
            if self.parent.path == "/":
                self.path = self.parent.path + name
            else:
                self.path = self.parent.path + "/" + name
            # self.parent.add(self)
        else:
            self.path = "/"
            self.parent = self
            self.owner = "root"
        # Owner set inside the mkdir method
        self.perms = "drwxr-x"

    def add(self, child):
        self.contents.append(child)
        return child


class Manager:
    user = "root"
    users = ["root"]
    root: Directory
    working_directory: Directory
    # Dictionary will store all file and directory names as keys, with a list of full ls output as value

    def __init__(self, root):
        self.root = root
        self.working_directory = root
    
    def get_working_directory(self):
        return self.working_directory
    
    def set_working_directory(self, directory: Directory):
        self.working_directory = directory
    
    # Make a new user
    def add_user(self, user: str):
        if self.users.contains(user):
            print("adduser: The user already exists")
            return
        self.users.append(user)


def main():
    
    commands_list = ["exit", "pwd", "cd", "mkdir", "touch", "cp", "mv", "rm", "rmdir", "chmod", "chown", "adduser", "deluser", "su", "ls"]
    # Dictionary to store functions for all the possible commands
    commands = {"exit": exit,
                "pwd": pwd,
                "cd": cd,
                "mkdir": mkdir,
                "touch": touch,
                "cp": cp,
                "mv": mv,
                "rm": rm,
                "rmdir": rmdir,
                "chmod": chmod,
                "chown": chown,
                "adduser": adduser,
                "deluser": deluser,
                "su": su,
                "ls": ls}
    # Making the root directory and namespace manager
    manager = Manager(Directory("/", None))

    # Keeping the program going
    while True:
        inp = input(f"{manager.user}:{manager.working_directory.path}$ ")
        inputs = shlex.split(inp) # shlex will preserve quoted strings
        if not inputs:
            continue
        if len(inputs) == 1:
            command = inputs[0]
            if command not in commands:
                print(f"{command}: Command not found")
                continue
            else:
                commands[command](manager)
        else:
            command = inputs.pop(0)
            if command not in commands:
                print(f"{command}: Command not found")
            commands[command](manager, inputs)
        
###
### COMMANDS AS FUNCTIONS
### 
# exit
def exit(manager: Manager, *args):
    if len(args) != 0:
        print("exit: Invalid syntax")
        return
    print(f"bye, {manager.user}")
    sys.exit()

# pwd
def pwd(manager: Manager, *args):
    if len(args) != 0:
        print("pwd: Invalid syntax")
        return
    print(manager.working_directory.path)

# cd
def cd(manager: Manager, *args):
    # If there's no arguments
    if len(args) == 0:
        print("cd: Invalid syntax")
        return
    # If there's too many  arguments
    elif len(args[0]) > 1:
        print("cd: Invalid syntax")
        return
    inputs = args[0]
    path = inputs[0]
    if path[-1] == "/" and path != "/": # Trimming the last slash (if there is one)
        path = path[:-1]
    # If path is invalid
    if not checkPath(manager, path):
        print("cd: No such file or directory")
        return
    # If destination is a file and not a directory
    if not isinstance(checkPath(manager, path), Directory):
        print("cd: Destination is a file")
        return
    # Checking permission for the whole path given
    toEnter = checkPathPerms(manager, path, "x") # will return object if permissions are fine, False otherwise
    if toEnter:
        manager.working_directory = toEnter
        return
    else:
        print("cd: Permission denied")
    
# mkdir
def mkdir(manager: Manager, *args):
    # If incorrect number of arguments are passed
    if len(args) == 0:
        print("mkdir: Invalid syntax")
        return
    elif len(args[0]) > 2:
        print("mkdir: Invalid syntax")
        return

    inputs = args[0]
    flag = False
    name = ""
    if len(inputs) == 1:
        path = inputs[0]
        if path[-1] == "/":
            path = path[:-1]
        name = inputs[0]
    elif len(inputs) == 2 and inputs[0] == "-p":
        path = inputs[1]
        if path[-1] == "/":
            path = path[:-1]
        arr = path.split("/")
        flag = True
        name = path[:-(len(arr[-1]))]
    elif len(inputs) == 2:
        print("mkdir: Invalid syntax")
        return
    
    arr = path.split("/")
    # If invalid characters are passed
    for str in arr:
        if not isValid(str):
            print("mkdir: Invalid syntax")
            return

    if path[-1] == "/":
        name = path[-(len(arr[-1])+1) : -1]
    else:
        name = path[-(len(arr[-1])) : ]
        
    if not flag:
        if checkPath(manager, path):
            print("mkdir: File exists")
            return
        absolute = False
        if path[0] == "/":
            absolute = True
        if not absolute: # If path is relative
            if len(arr) == 1:
                if checkPerm(manager, manager.working_directory, "w"):
                    create = Directory(name, manager.working_directory)
                    manager.working_directory.add(create)
                    create.owner = manager.user
                    return
                else:
                    print("mkdir: Permission denied")
                    return
        else: # If path is absolute
            arr.pop(0) # remove first element, which is ""
            if len(arr) == 1: # Means we need to use root directory
                create = Directory(name, manager.root)
                manager.root.add(create)
                create.owner = manager.user
                return
        tempPath = path[:-(len(arr[-1])+1)] # Slicing path to remove the last element, including the slash
        if tempPath == "":
            tempPath = "/"
        # If ancestors don't exist
        destination = checkPath(manager, tempPath)
        if not destination:
            print("mkdir: Ancestor directory does not exist")
            return
        dirAncPath = destination.parent.path[:-(len(destination.parent.name)+1)]
        if dirAncPath == "":
            dirAncPath = "/"
        if checkPathPerms(manager, dirAncPath, "x"):
            if checkPerm(manager, destination, "w"):
                create = Directory(name, destination)
                destination.add(create)
                create.owner = manager.user
            else:
                print("mkdir: Permission denied")
                return
        else:
            print("mkdir: Permission denied")
            return
    elif flag: # FLAG
        absolute = False
        if path[0] == "/":
            absolute = True
        if not absolute: # If path is relative
            if len(arr) == 1:
                if checkPerm(manager, manager.working_directory, "w"):
                    create = Directory(name, manager.working_directory)
                    manager.working_directory.add(create)
                    create.owner = manager.user
                    return  
                else:
                    print("mkdir: Permission denied")
                    return
            tempPath = path[:-(len(arr[-1])+1)] # Slicing path to remove the last element, including the slash
        else: # If path is absolute
            arr.pop(0) # remove first element, which is ""
            if len(arr) == 1: # Means we need to use root directory
                create = Directory(name, manager.root)
                manager.root.add(create)
                create.owner = manager.user
                return
            tempPath = path[1:-(len(arr[-1])+1)] # Slicing path to remove the last element, including the slash
                
        if tempPath == "":
            tempPath = "/"
        current = manager.working_directory
        tempArr = tempPath.split("/")
        i = 0
        while i < len(tempArr):
            exists = False
            for thing in current.contents:
                if thing.name == tempArr[i] and isinstance(thing, Directory):
                    current = thing
                    exists = True
            
            if not exists:
                create = Directory(tempArr[i], current)
                current = current.add(create)
                create.owner = manager.user
            i += 1

        destination = checkPath(manager, tempPath)
        dirAncPath = destination.parent.path[:-(len(destination.parent.name)+1)]
        if dirAncPath == "":
            dirAncPath = "/"
        # print(tempPath)
        if checkPathPerms(manager, dirAncPath, "x"):
            if checkPerm(manager, destination, "w"):
                # print(tempDir.path)
                create = Directory(name, destination)
                destination.add(create)
                create.owner = manager.user
            else:
                print("mkdir: Permission denied")
                return
        else:
            print("mkdir: Permission denied")
            return

# touch
def touch(manager: Manager, *args):
    # If there's no arguments
    if len(args) == 0:
        print("touch: Invalid syntax")
        return
    # If there's too many  arguments
    elif len(args[0]) > 1:
        print("touch: Invalid syntax")
        return
    inputs = args[0]
    path = inputs[0]
    arr = path.split("/")
    # If invalid characters are passed
    for str in arr:
        if not isValid(str):
            print("touch: Invalid syntax")
            return

    name = path[-(len(arr[-1])) : ] # trimming path and only getting name of file
    if path[0] == "/":
        absolute = True
    else:
        absolute = False
    if path[-1] == "/" and path != "/": # Trimming the last slash (if there is one)
        path = path[:-1]
    # If file already exists
    if checkPath(manager, path):
        return

    if not absolute:
        if len(arr) == 1:
            if checkPathPerms(manager, manager.working_directory.path, "x") and checkPerm(manager, manager.working_directory, "w"):
                create = File(name, manager.working_directory)
                create.owner = manager.user
                return create
            else:
                print("touch: Permission denied")
                return
    else:
        arr.pop(0)
        if len(arr) == 1:
            create = File(name, manager.root)
            create.owner = manager.user
            return create
    # If file needs to be created by following path
    tempPath = path[ : -(len(arr[-1])+1)] # removing name of file to only get path
    destination = checkPath(manager, tempPath)
    if not destination:
        print("touch: Ancestor directory does not exist")
        return
    if checkPathPerms(manager, destination.path, "x"): # Checking "x" permission for ancestors
        if checkPerm(manager, destination, "w"): # Checking "w" permission for parent
            create = File(name, destination)
            create.owner = manager.user
            return create
        else:
            print("touch: Permission denied")
            return
    else:
        print("touch: Permission denied")
        return

# cp
def cp(manager: Manager, *args):
    # If incorrect number of arguments are passed
    if len(args) == 0:
        print("cp: Invalid syntax")
        return
    elif len(args[0]) != 2:
        print("cp: Invalid syntax")
        return
    
    src = args[0][0] # source path
    dst = args[0][1] # destination path
    srcArr = src.split("/") # file path
    dstArr = dst.split("/") # directory path
    name = dst[-(len(dstArr[-1])) : ] # trimming path and only getting name of file
    # ancestor paths for src and dst
    if len(srcArr) == 1:
        srcParPath = src
    else:
        srcParPath = src[:-(len(srcArr[-1])+1)]
    
    if len(dstArr) == 1:
        dstParPath = manager.working_directory.path
    else:
        dstParPath = dst[:-(len(dstArr[-1])+1)]

    ## ERROR HANDLING
    # If invalid characters are passed
    for str in srcArr:
        if not isValid(str):
            print("cp: Invalid syntax")
            return
    for str in dstArr:
        if not isValid(str):
            print("cp: Invalid syntax")
            return
    
    # If src file does not exist
    source = checkPath(manager, src)
    if not source:
        print("cp: No such file")
        return
    # If dst already exists
    if isinstance(checkPath(manager, dst), File):
        print("cp: File exists")
        return
    elif isinstance(checkPath(manager, dst), Directory):
        print("cp: Destination is a directory")
        return
    # If src is a directory
    if isinstance(checkPath(manager, src), Directory):
        print("cp: Source is a directory")
        return
    # If dst's parent does not exist
    destination = checkPath(manager, dstParPath)
    if not destination:
        print("cp: No such file or directory")
        return
    elif isinstance(destination, File):
        print("cp: No such file or directory")
        return
    
    dstAncPath = destination.path[:-(len(destination.name)+1)]
    if dstAncPath == "":
        dstAncPath = "/"
    srcAncPath = source.parent.path

    # Permission "r" on src
    if not checkPerm(manager, source, "r"):
        print("cp: Permission denied")
        return
    # Permission "x" on src ancestors
    if not checkPathPerms(manager, srcAncPath, "x"):
        print("cp: Permission denied")
        return
    # Permission "x" on dst ancestors
    if not checkPathPerms(manager, dstAncPath, "x"):
        print("cp: Permission denied")
        return
    # Permission "w" on dst parent
    if not checkPerm(manager, destination, "w"):
        print("cp: Permission denied")
        return

    # Actually copying the file
    create = File(name, destination)
    create.owner = manager.user

# mv
def mv(manager: Manager, *args):
    # If incorrect number of arguments are passed
    if len(args) == 0:
        print("mv: Invalid syntax")
        return
    elif len(args[0]) != 2:
        print("mv: Invalid syntax")
        return
    
    src = args[0][0] # source path
    dst = args[0][1] # destination path
    srcArr = src.split("/") # file path
    if srcArr[0] == "":
        srcArr.pop(0)
    dstArr = dst.split("/") # directory path
    if dstArr[0] == "":
        dstArr.pop(0)
    name = dst[-(len(srcArr[-1])) : ] # trimming path and only getting name of created file
    # ancestor paths for src and dst
    if len(srcArr) == 1:
        srcParPath = src
    else:
        srcParPath = src[:-(len(srcArr[-1])+1)]
    
    if len(dstArr) == 1:
        dstParPath = manager.working_directory.path
    else:
        dstParPath = dst[:-(len(dstArr[-1])+1)]


    ## ERROR HANDLING
    # If invalid characters are passed
    for str in srcArr:
        if not isValid(str):
            print("mv: Invalid syntax")
            return
    for str in dstArr:
        if not isValid(str):
            print("mv: Invalid syntax")
            return
    
    # If dst already exists
    if isinstance(checkPath(manager, dst), File):
        print("mv: File exists")
        return
    # If src file does not exist
    source = checkPath(manager, src)
    if not source:
        print("mv: No such file")
        return
    elif isinstance(checkPath(manager, dst), Directory):
        print("mv: Destination is a directory")
        return
    # If src is a directory
    if isinstance(checkPath(manager, src), Directory):
        print("mv: Source is a directory")
        return
    # If dst's parent does not exist
    destination = checkPath(manager, dstParPath)
    if not destination:
        print("mv: No such file or directory")
        return
    elif isinstance(destination, File):
        print("mv: No such file or directory")
        return
    
    sourceDir = checkPath(manager, srcParPath) # Stores the src parent directory
    dstAncPath = destination.path[:-(len(destination.name)+1)]
    if dstAncPath == "":
        dstAncPath = "/"
    srcAncPath = sourceDir.path[:-(len(sourceDir.name)+1)]
    if srcAncPath == "":
        srcAncPath = "/"

    # Permission "x" on src ancestors
    if not checkPathPerms(manager, srcAncPath, "x"):
        print("mv: Permission denied")
    # Permission "w" on src parent
    if not checkPerm(manager, sourceDir, "w"):
        print("mv: Permission denied")
        return
    # Permission "x" on dst ancestors
    if not checkPathPerms(manager, dstAncPath, "x"):
        print("mv: Permission denied")
        return
    # Permission "w" on dst parent
    if not checkPerm(manager, destination, "w"):
        print("mv: Permission denied")
        return

    # Actually moving the file
    create = File(name, destination)
    create.owner = manager.user
    parentList = source.parent.contents
    parentList.remove(source)
    del source

# rm
def rm(manager: Manager, *args):
    if len(args) == 0:
        print("rm: Invalid syntax")
        return
    elif len(args[0]) > 1:
        print("rm: Invalid syntax")
        return
    
    inputs = args[0]
    path = inputs[0]
    arr = path.split("/")
    # If invalid characters are passed
    for str in arr:
        if not isValid(str):
            print("rm: Invalid syntax")
            return

    file = checkPath(manager, path)
    if not file:
        print("rm: No such file")
        return
    elif isinstance(file, Directory):
        print("rm: Is a directory")
        return
    
    fileAncPath = file.parent.path[:-(len(file.parent.name)+1)]
    if fileAncPath == "":
        fileAncPath = "/"
    # Permission "w" on file
    if not checkPerm(manager, file, "w"):
        print("rm: Permission denied")
        return
    # Permission "x" on file ancestors
    if not checkPathPerms(manager, fileAncPath, "x"):
        print("rm: Permission denied")
        return
    # Permission "w" on dile parent
    if not checkPerm(manager, file.parent, "w"):
        print("rm: Permission denied")
        return
    
    # Removing the file
    parentList = file.parent.contents
    parentList.remove(file)
    del file

# rmdir
def rmdir(manager: Manager, *args):
    if len(args) == 0:
        print("rmdir: Invalid syntax")
        return
    elif len(args[0]) > 1:
        print("rmdir: Invalid syntax")
        return
    
    inputs = args[0]
    path = inputs[0]
    arr = path.split("/")
    # If invalid characters are passed
    for str in arr:
        if not isValid(str):
            print("rmdir: Invalid syntax")
            return
    dir = checkPath(manager, path)
    # If directory does not exist
    if not dir:
        print("rmdir: No such file or directory")
        return
    # If path exists but is not a directory
    if not isinstance(dir, Directory):
        print("rmdir: Not a directory")
        return
    # If directory is not empty
    if dir.contents:
        print("rmdir: Directory not empty")
        return
    # If directory is working directory
    if dir == manager.working_directory:
        print("rmdir: Cannot remove pwd")
        return
    
    dirAncPath = dir.parent.path[:-(len(dir.parent.name)+1)]
    if dirAncPath == "":
        dirAncPath = "/"
    # Permission "x" on directory ancestors
    if not checkPathPerms(manager, dir.parent.path, "x"):
        print("rmdir: Permission denied")
        return
    # Permission "w" on directory parent
    if not checkPerm(manager, dir.parent, "w"):
        print("rmdir: Permission denied")
        return
    
    # Removing the directory
    parentList = dir.parent.contents
    parentList.remove(dir)
    del dir
  
# chmod
def chmod(manager: Manager, *args):
    # If incorrect number of parameters are passed
    if len(args) == 0:
        print("chmod: Invalid syntax")
        return
    elif len(args[0]) < 2 or len(args[0]) > 3:
        print("chmod: Invalid syntax")
        return
    
    inputs = args[0]
    if len(inputs) == 2:
        recursive = False
        mode = inputs[0]
        path = inputs[1]
    if len(inputs) == 3 and inputs[0] == "-r":
        recursive = True
        mode = inputs[1]
        path = inputs[2]
    
    destination = checkPath(manager, path)

    # If mode is invalid
    count = mode.count("-") + mode.count("+") + mode.count("=")
    if count != 1:
        print("chmod: Invalid mode")
        return
    if "-" in mode:
        operation = "-"
        modeList = mode.split("-")
    elif "+" in mode:
        operation = "+"
        modeList = mode.split("+")
    elif "=" in mode:
        operation = "="
        modeList = mode.split("=")

    if (modeList[0].count("u") + modeList[0].count("o") + modeList[0].count("a")) != len(modeList[0]):
        print("chmod: Invalid mode")
        return
    elif (modeList[1].count("r") + modeList[1].count("w") + modeList[1].count("x")) != len(modeList[1]):
        print("chmod: Invalid mode")
        return
    
    toChange = []
    if "r" in modeList[1]:
        toChange.append("r")
    else:
        toChange.append("-")
    if "w" in modeList[1]:
        toChange.append("w")
    else:
        toChange.append("-")
    if "x" in modeList[1]:
        toChange.append("x")
    else:
        toChange.append("-")

    
    if not recursive:
        # If file cannot be found
        if not destination:
            print("chmod: No such file or directory")
            return
        # If user is invalid
        if destination.owner != manager.user and manager.user != "root":
            print("chmod: Operation not permitted")
            return
        # Getting permission string
        fileType = destination.perms[0]
        userPerms = destination.perms[1:4]
        otherPerms = destination.perms[4:]
        # Checking execute permission on ancestors
        ancPath = destination.parent.path
        if not checkPathPerms(manager, ancPath, "x"):
            print("chmod: Permission denied")
            return
        # Changing the permissions
        if "u" in modeList[0] or "a" in modeList[0]: # userPerms permissions need to be changed
            if operation == "-": # Removing perms
                for value in toChange:
                    userPerms = userPerms.replace(value, "-")
            elif operation == "+": # Adding perms
                if "r" in toChange:
                    userPerms = "r" + userPerms[1:]
                if "w" in toChange:
                    userPerms = userPerms[0] + "w" + userPerms[2]
                if "x" in toChange:
                    userPerms = userPerms[:2] + "x"
            elif operation == "=": # Setting perms
                if modeList[1] == "":
                    userPerms = "---"
                else:
                    userPerms = ''.join(toChange)
        if "o" in modeList[0] or "a" in modeList[0]: # otherPerms permissions need to be changed
            if operation == "-": # Removing perms
                for value in toChange:
                    otherPerms = otherPerms.replace(value, "-")
            elif operation == "+": # Adding perms
                if "r" in toChange:
                    otherPerms = "r" + otherPerms[1:]
                if "w" in toChange:
                    otherPerms = otherPerms[0] + "w" + otherPerms[2]
                if "x" in toChange:
                    otherPerms = otherPerms[:2] + "x"
            elif operation == "=": # Setting perms
                if modeList[1] == "":
                    otherPerms = "---"
                else:
                    otherPerms = ''.join(toChange)
        destination.perms = fileType + userPerms + otherPerms
    else: # If "-r" is passed
        # If file cannot be found
        if not destination:
            print("chmod: No such file or directory")
            return
        myList = []
        if isinstance(destination, Directory):
            myList = listFiles(manager, destination)
        myList.append(destination)
        for file in myList:
            # If user is invalid
            if file.owner != manager.user and manager.user != "root":
                print("chmod: Operation not permitted")
                continue
            # Checking execute permission on ancestors
            ancPath = file.parent.path
            if not checkPathPerms(manager, ancPath, "x"):
                print("chmod: Permission denied")
                continue
            # Getting permission string for file
            fileType = file.perms[0]
            userPerms = file.perms[1:4]
            otherPerms = file.perms[4:]

            # Changing the permissions
            if "u" in modeList[0] or "a" in modeList[0]: # userPerms permissions need to be changed
                if operation == "-": # Removing perms
                    for value in toChange:
                        userPerms = userPerms.replace(value, "-")
                elif operation == "+": # Adding perms
                    if "r" in toChange:
                        userPerms = "r" + userPerms[1:]
                    if "w" in toChange:
                        userPerms = userPerms[0] + "w" + userPerms[2]
                    if "x" in toChange:
                        userPerms = userPerms[:2] + "x"
                elif operation == "=": # Setting perms
                    if modeList[1] == "":
                        userPerms = "---"
                    else:
                        userPerms = ''.join(toChange)
            if "o" in modeList[0] or "a" in modeList[0]: # otherPerms permissions need to be changed
                if operation == "-": # Removing perms
                    for value in toChange:
                        otherPerms = otherPerms.replace(value, "-")
                elif operation == "+": # Adding perms
                    if "r" in toChange:
                        otherPerms = "r" + otherPerms[1:]
                    if "w" in toChange:
                        otherPerms = otherPerms[0] + "w" + otherPerms[2]
                    if "x" in toChange:
                        otherPerms = otherPerms[:2] + "x"
                elif operation == "=": # Setting perms
                    if modeList[1] == "":
                        otherPerms = "---"
                    else:
                        otherPerms = ''.join(toChange)
            file.perms = fileType + userPerms + otherPerms

        
# chown
def chown(manager: Manager, *args):
    # If current user is not root
    if manager.user != "root":
        print("chown: Operation not permitted")
        return
    # If incorrect number of parameters are passed
    if len(args) == 0:
        print("chmod: Invalid syntax")
        return
    elif len(args[0]) < 2 or len(args[0]) > 3:
        print("chmod: Invalid syntax")
        return
    
    inputs = args[0]
    if len(inputs) == 2:
        recursive = False
        user = inputs[0]
        path = inputs[1]
    if len(inputs) == 3 and inputs[0] == "-r":
        recursive = True
        user = inputs[1]
        path = inputs[2]
    
    # If user is invalid
    if user not in manager.users:
        print("chown: Invalid user")
        return

    destination = checkPath(manager, path)
    # If file cannot be found
    if not destination:
        print("chown: No such file or directory")
        return
    
    if not recursive:
        destination.owner = user
    else: # If "-r" is passed
        if isinstance(destination, Directory):
            myList = listFiles(manager, destination)
            myList.append(destination)
            for file in myList:
                file.owner = user
        else:
            destination.owner = user

# adduser
def adduser(manager: Manager, *args):
    # If current user is not root
    if manager.user != "root":
        print("adduser: Operation not permitted")
        return
    # If incorrect number of arguments is passed
    if len(args) == 0:
        print("adduser: Invalid syntax")
        return
    elif len(args[0]) > 1:
        print("adduser: Invalid syntax")
        return
    
    inputs = args[0]
    user = inputs[0]
    # If user already exists
    for value in manager.users:
        if value == user:
            print("adduser: The user already exists")
            return
    
    # Adding the user
    manager.users.append(user)

# deluser
def deluser(manager: Manager, *args):
    # If current user is not root
    if manager.user != "root":
        print("deluser: Operation not permitted")
        return
    # If incorrect number of arguments is passed
    if len(args) == 0:
        print("adduser: Invalid syntax")
        return
    elif len(args[0]) > 1:
        print("adduser: Invalid syntax")
        return
    
    inputs = args[0]
    user = inputs[0]

    # If user does not exist
    exists = False
    for value in manager.users:
        if value == user:
            exists = True
    if not exists:
        print("deluser: The user does not exist")
        return
    
    # If given user is root
    if user == "root":
        print("""WARNING: You are just about to delete the root account
Usually this is never required as it may render the whole system unusable
If you really want this, call deluser with parameter --force
(but this `deluser` does not allow `--force`, haha)
Stopping now without having performed any action""")
        return
    
    # Deleting the given user
    manager.users.remove(user)
    
# su
def su(manager: Manager, *args):
    # If no arguments are passed
    if len(args) == 0:
        manager.user = "root"
        return
    elif len(args[0]) > 1: # If incorrect number of arguments are passed
        print("su: Invalid syntax")
        return
    
    inputs = args[0]
    user = inputs[0]
    
    for value in manager.users:
        if value == user:
            manager.user = user
            return
    
    # If user does not exist
    print("su: Invalid user")

# ls
def ls(manager: Manager, *args):
    path = ""
    flags = []
    # If no arguments are passed to ls
    if len(args) == 0:
        lsDir = manager.working_directory
    else:
        inputs = args[0]
        if (inputs[-1] != "-a" and inputs[-1] != "-d" and inputs[-1] != "-l"):
            path = inputs.pop(-1)
            flags = inputs
            lsDir = checkPath(manager, path)
        else:
            flags = inputs
            lsDir = manager.working_directory
        
        if not lsDir:
            print("ls: No such file or directory")
            return

    if isinstance(lsDir, File):
        # Checking "r" permission for lsDir
        if not checkPerm(manager, lsDir.parent, "r"):
            print("ls: Permission denied")
            return
        # Checking "x" permission for lsDir's ancestors
        if not checkPathPerms(manager, lsDir.parent.path, "x"):
            print("ls: Permission denied")
            return
        arr = path.split("/")
        if path == "/":
            arr = ["/"]
        if lsDir.name[0] != "." and "." not in arr and ".." not in arr:
            if "-l" in flags:
                print(f"{lsDir.perms} {lsDir.owner} {path}")
                return
            else:
                print(path)
                return
        elif "-a" in flags:
            if "-l" in flags:
                print(f"{lsDir.perms} {lsDir.owner} {path}")
                return
            else:
                print(path)
                return
        return
    
    # Checking "r" permission for lsDir
    if not checkPerm(manager, lsDir, "r"):
        print("ls: Permission denied")
        return

    if not flags: # If there are no flags
        lsDir.contents.sort(key=lambda x: x.name)
        for thing in lsDir.contents:
            if thing.name[0] != ".":
                print(thing.name, end="\n")
        return
    if "-l" in flags and "-d" not in flags:
        if "-a" in flags:
            print(f"{lsDir.perms} {lsDir.owner} .")
            print(f"{lsDir.parent.perms} {lsDir.parent.owner} ..")
            lsDir.contents.sort(key=lambda x: x.name)
            for thing in lsDir.contents:
                print(f"{thing.perms} {thing.owner} {thing.name}", end="\n")
        else:
            lsDir.contents.sort(key=lambda x: x.name)
            for thing in lsDir.contents:
                if thing.name[0] != ".":
                    print(f"{thing.perms} {thing.owner} {thing.name}", end="\n")
    if "-a" in flags and "-l" not in flags and "-d" not in flags:
        print(".")
        print("..")
        lsDir.contents.sort(key=lambda x: x.name)
        for thing in lsDir.contents:
            print(thing.name, end="\n")
        return
    if "-d" in flags:
        # Checking "r" permission for lsDir parent
        if not checkPerm(manager, lsDir.parent, "r"):
            print("ls: Permission denied")
            return
        # Checking "x" permission for lsDir ancestors
        if not checkPathPerms(manager,lsDir.parent.path, "x"):
            print("ls: Permission denied")
            return
        if path != "":
            if path != "/":
                arr = path.split("/")
            else:
                arr = ["/"]
            if "-a" in flags:
                if "-l" in flags:
                    print(f"{lsDir.perms} {lsDir.owner} {path}")
                else:
                    print(path)
            elif ("." not in arr and ".." not in arr) or path[0] == "/":
                if "-l" in flags:
                    if (not arr[-1][0] == ".") or (arr[-1] == "." and len(arr) > 1):
                        print(f"{lsDir.perms} {lsDir.owner} {path}")
                else:
                    if (not arr[-1][0] == ".") or (arr[-1] == "." and len(arr) > 1):
                        print(path)
        else:
            if "-a" in flags and "-l" in flags:
                print(f"{lsDir.perms} {lsDir.owner} .")
            elif "-a" in flags:
                print(".")

## AUXILIARY FUNCTIONS

def checkPerm(manager: Manager, dir: Directory or File, perm: str) -> bool:
    # root user bypasses all permissions
    if manager.user == "root":
        return True
    # storing the relevant permissions based on current user
    if manager.user == dir.owner:
        perms = dir.perms[1:4]
    else:
        perms = dir.perms[4:]
    
    if(perm == "r" and perms[0] == "r"):
        return True
    elif(perm == "w" and perms[1] == "w"):
        return True
    elif(perm == "x" and perms[2] == "x"):
        return True
    else:
        return False

def checkPathPerms(manager: Manager, path: str, perm: str) -> bool or File or Directory:
    absolute = False
    if path[0] == "/":
        absolute = True
    arr = path.split("/")
    if path == "/":
        if checkPerm(manager, manager.root, perm):
            return manager.root
        else:
            return False
    if not absolute:
        current = manager.working_directory
        i = 0
        while i < len(arr):
            if arr[i] == ".":
                if i == len(arr) - 1:
                    return current
                else:
                    i += 1
                    continue
            elif arr[i] == "..":
                if i == len(arr) - 1:
                    return current.parent
                else:
                    current = current.parent
                    i += 1
                    continue
            if isinstance(current, File):
                return False
            for thing in current.contents:
                if thing.name == arr[i]:
                    if checkPerm(manager, thing, perm):
                        temp = thing
                    else:
                        return False
            
            if i == len(arr) - 1:
                return temp # Means we're at end of path, so return the file or directory
            current = temp # Otherwise continue with checking
            i += 1
    else:
        current = manager.root
        i = 1
        while i < len(arr):
            if arr[i] == ".":
                if i == len(arr) - 1:
                    return current
                else:
                    i += 1
                    continue
            elif arr[i] == "..":
                if i == len(arr) - 1:
                    return current.parent
                else:
                    current = current.parent
                    i += 1
                    continue
            if isinstance(current, File):
                return False
            for thing in current.contents:
                if thing.name == arr[i]:
                    if checkPerm(manager, thing, perm):
                        temp = thing
                    else:
                        return False # Ancestor doesn't have needed permission
            
            if i == len(arr) - 1:
                return temp # Means we're at end of path, so return the file or directory
            current = temp # Otherwise continue with checking
            i += 1

def checkPath(manager: Manager, path: str) -> bool or File or Directory:
    absolute = False
    if path[0] == "/":
        absolute = True
    arr = path.split("/")
    if path == "/":
        return manager.root
    if not absolute:
        current = manager.working_directory
        i = 0
        while i < len(arr):
            if arr[i] == ".":
                if i == len(arr) - 1:
                    return current
                else:
                    i += 1
                    continue
            elif arr[i] == "..":
                if i == len(arr) - 1:
                    return current.parent
                else:
                    current = current.parent
                    i += 1
                    continue
            # check if current path part is in working directory
            exists = False
            if isinstance(current, File):
                return False
            for thing in current.contents:
                if thing.name == arr[i]:
                    exists = True
                    temp = thing
            
            if not exists:
                return False
            else:
                if i == len(arr) - 1:
                    return temp # Means the path exists
                current = temp # Otherwise continue with checking
                i += 1
    # If path is absolute
    else:
        current = manager.root
        # arr[0] will be ""
        i = 1
        while i < len(arr):
            if arr[i] == ".":
                if i == len(arr) - 1:
                    return current
                else:
                    i += 1
                    continue
            elif arr[i] == "..":
                if i == len(arr) - 1:
                    return current.parent
                else:
                    current = current.parent
                    i += 1
                    continue
            # check if current path part is in working directory
            exists = False
            if isinstance(current, File):
                return False
            for thing in current.contents:
                if thing.name == arr[i]:
                    exists = True
                    temp = thing
            
            if not exists:
                return False
            else:
                if i == len(arr) - 1:
                    return temp # Means the path exists
                current = temp # Otherwise continue with checking
                i += 1
            
def isValid(input) -> bool:
    chars = [" ", "-", ".", "_"]
    for c in input:
        if not c.isalnum() and c not in chars:
            return False
    return True
    
def listFiles(manager: Manager, dir: Directory) -> list:
    output = []

    for file in dir.contents:
        if isinstance(file, Directory):
            output.append(file)
            output += listFiles(manager, file)
        elif isinstance(file, File):
            output.append(file)
    
    return output

if __name__ == '__main__':
    main()
