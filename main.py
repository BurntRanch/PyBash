import regex
import sys
import os

out_function = ""
skip_until = ""

def exit():
    print("Goodbye!")
    sys.exit(0)

def process(line):
    global out_function, skip_until
    if line.startswith("$") or line == '' or (skip_until and not line.endswith(skip_until)):
        return
    if line.endswith("EXIT FUNC;"):
        out_function = ""
        return
    if out_function:
        globals()[out_function].append(line.removeprefix('    ').removeprefix('\t'))
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
                if not globals()['RETURN']:
                    globals()['RETURN'] = "None"
    elif regex.match("SET .* TO .*;", line):
        if line.split(" ")[1] != 'RETURN':
            globals()[line.split(" ")[1]] = " ".join(line.split(" ")[3:]).removesuffix(";")
        else:
            raise SyntaxError(line + ", You can't set RETURN.")
    elif regex.match("DELETE VAR .*;", line):
        del globals()[line.split(" ")[2].removesuffix(";")]
    elif regex.match("DELETE FUNC .*;", line):
        del globals()[line.split(" ")[2].removesuffix(";")]
    elif regex.match("DEFINE FUNC .*;", line):
        if line.split(" ")[2].removesuffix(";") != 'RETURN':
            out_function = line.split(" ")[2].removesuffix(";")
            globals()[line.split(" ")[2].removesuffix(";")] = []
        else:
            raise SyntaxError("'" + line + "' You can't set RETURN.")
    elif regex.match("INCLUDE .*;", line):
        if regex.match("INCLUDE .* FROM .*;", line):
            exec(f'from {line.split(" ")[3].removesuffix(";")} import {line.split(" ")[1]}', globals())
        else:
            exec(f'import {line.split(" ")[1].removesuffix(";")}', globals())
    elif regex.match("IF .*;", line):
        exec(f'__IF_RETURN__ = not not {" ".join(line.split(" ")[1:]).removesuffix(";")}', globals())
        if not __IF_RETURN__:
            skip_until = "ENDIF;"
        del globals()['__IF_RETURN__']
    elif line.endswith(skip_until):
        skip_until = ""
    else:
        raise SyntaxError(line)

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
