import regex
import sys
import os
from helpers.pyasm_errors import InvalidVariableName

__out_function__ = ""
__skip_until__ = ""

def exit():
    print("Goodbye!")
    sys.exit(0)

def __process_file__(filename):
    with open(filename, 'r') as f:
        lines = f.read().splitlines()
        for i in lines:
            process(i)


def process(line):
    global __out_function__, __skip_until__
    if line.startswith("$") or line == '' or (__skip_until__ and (not line.endswith(__skip_until__))):
        if line.endswith("ENDIF;"):
            __skip_until__ = ""
        return
    if line.endswith("EXIT FUNC;"):
        __out_function__ = ""
        return
    if __out_function__:
        globals()[__out_function__].append(line.removeprefix('    ').removeprefix('\t'))
        return
    if regex.match("CALL .*;", line):
        if regex.match("CALL .* ARGS \(.*\);", line):
            if " ".join(line.split(" ")[3][:-1]) == "( )":
                print("WARN: You shouldn't use CALL x ARGS (); to call a function that doesn't take an argument, use CALL x; instead.")
            if len(line.split(" ")) <= 3:
                exec(f'RETURN = {line.split(" ")[1]}{line.split(" ")[3].removesuffix(";")}', globals())
                if not globals()['RETURN']:
                    globals()['RETURN'] = "None"
            else:
                exec(f'RETURN = {line.split(" ")[1]}{" ".join(line.split(" ")[3:]).removesuffix(";")}', globals())
                if not globals()['RETURN']:
                    globals()['RETURN'] = "None"
        else:
            if globals().get("".join(line.split(" ")[1]).removesuffix(";"), None):
                for i in globals().get("".join(line.split(" ")[1]).removesuffix(";"), None):
                    process(i)
            else:
                exec(f'RETURN = {"".join(line.split(" ")[1]).removesuffix(";")}()', globals())
    elif regex.match("SET .* TO .*;", line):
        if line.split(" ")[1] != 'RETURN' and not regex.match("__.*__", line.split(" ")[1]):
            globals()[line.split(" ")[1]] = " ".join(line.split(" ")[3:]).removesuffix(";")
        else:
            raise InvalidVariableName(line + ", You can't set PyAsm runtime variables.")
    elif regex.match("DELETE VAR .*;", line):
        del globals()[line.split(" ")[2].removesuffix(";")]
    elif regex.match("DELETE FUNC .*;", line):
        del globals()[line.split(" ")[2].removesuffix(";")]
    elif regex.match("DEFINE FUNC .*;", line):
        if line.split(" ")[2].removesuffix(";") != 'RETURN' and not regex.match("__.*__", line.split(" ")[2].removesuffix(";")):
            __out_function__ = line.split(" ")[2].removesuffix(";")
            globals()[line.split(" ")[2].removesuffix(";")] = []
        else:
            raise InvalidVariableName("'" + line + "' You can't set PyAsm runtime variables.")
    elif regex.match("INCLUDE .*;", line):
        if regex.match("INCLUDE .* FROM .*;", line):
            exec(f'from {line.split(" ")[3].removesuffix(";")} import {line.split(" ")[1]}', globals())
        else:
            if os.path.exists(f'{line.split(" ")[1].removesuffix(";")}.pym'):
                __process_file__(f'{line.split(" ")[1].removesuffix(";")}.pym')
            else:
                exec(f'import {line.split(" ")[1].removesuffix(";")}', globals())
    elif regex.match("IF .*;", line):
        exec(f'__IF_RETURN__ = not not {" ".join(line.split(" ")[1:]).removesuffix(";")}', globals())
        # if the statement is false
        if not __IF_RETURN__:
            __skip_until__ = "ELSE;"
        #del globals()['__IF_RETURN__']
    # if we see an ELSE;
    elif line.endswith("ELSE;"):
        if __IF_RETURN__:
            __skip_until__ = "ENDIF;"
        else:
            __skip_until__ = ""
    elif line.endswith(__skip_until__):
        __skip_until__ = ""
    else:
        raise SyntaxError(line)
    #breakpoint()

# check if a file is supplied
if len(sys.argv) < 2:
    while True:
        line = input(">> ")
        process(line)
else:
    # check format and execute each line
    if os.path.isfile(sys.argv[1]) and sys.argv[1].endswith(".pym"):
        with open(sys.argv[1], 'r') as f:
            lines = f.read().splitlines()
            for i in lines:
                process(i)
    else:
        print("FATAL: Unrecognized file format. (Try putting .pym in the end of the file name!)")
