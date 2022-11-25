import regex
import sys
import os
from helpers.pyasm_errors import AccessError, NoImportFound

__out_function__ = ""
__skip_until__ = ""
__in_while_loop__ = False
__while_loops__ = []
__while_statements__ = []
__if_statements__ = []
__in_if_statement__ = False
__if_cases__ = []
__if_return__ = False
__if_layers__ = 0
globals_pyasm = {}

def exit():
    print("Goodbye!")
    sys.exit(0)

def __process_file__(filename):
    with open(filename, 'r') as f:
        lines = f.read().splitlines()
        for i in lines:
            process(i)


def process(line, __ignore_while_loop__ = False, __ignore_if_statement__ = False):
    global __out_function__, __skip_until__, __while_loops__, __in_while_loop__, __if_statements__, __in_if_statement__, __if_layers__

    # fix indentation
    while line.startswith(' ') or line.startswith('\t'):
        line = line.removeprefix(' ').removeprefix('\t')

    # check for comments or empty lines, ENDIFs or whether we should skip this code in general
    if line.startswith("$") or line == '' or (__skip_until__ and (not line.endswith(__skip_until__))):
        return

    # some function stuff like recording the function code for execution
    if line == "EXIT FUNC;":
        __out_function__ = ""
        return

    if __out_function__:
        globals_pyasm[__out_function__].append(line)
        return
    
    # recording while loop code for execution
    if __in_while_loop__ and not line == "ENDWHILE;" and not regex.match("WHILE .*;", line) and not __ignore_while_loop__:
        __while_loops__[-1].append(line)
        return

    # recording if statement code for execution
    if __in_if_statement__ and not line == "ENDIF;" and not regex.match("IF .*;", line) and not __ignore_if_statement__:
        __if_statements__[-1].append(line)
        return

    # regex match for function calls with arguments, etc.
    if regex.match("CALL .*;", line):
        if regex.match("CALL .* ARGS \(.*\);", line):
            if " ".join(line.split(" ")[3][:-1]) == "( )":
                print("WARN: You shouldn't use CALL x ARGS (); to call a function that doesn't take an argument, use CALL x; instead.")
            if len(line.split(" ")) <= 3:
                exec(f'RETURN = {line.split(" ")[1]}{line.split(" ")[3].removesuffix(";")}', globals_pyasm)
            else:
                exec(f'RETURN = {line.split(" ")[1]}{" ".join(line.split(" ")[3:]).removesuffix(";")}', globals_pyasm)
        else:
            if isinstance(globals_pyasm.get("".join(line.split(" ")[1]).removesuffix(";"), None), list):
                for i in globals_pyasm.get("".join(line.split(" ")[1]).removesuffix(";"), None):
                    process(i)
            else:
                exec(f'RETURN = {"".join(line.split(" ")[1]).removesuffix(";")}()', globals_pyasm)
    # variable manipulation (we have a sandbox so now we dont have to worry about users overwriting runtime vars!)
    elif regex.match("SET .* TO .*;", line):
        globals_pyasm[line.split(" ")[1]] = eval(" ".join(line.split(" ")[3:]).removesuffix(";"), globals_pyasm)
    elif regex.match("INCREMENT .* BY .*;", line):
        if line.split(" ")[-1].removesuffix(';').isnumeric():
            globals_pyasm[line.split(" ")[1]] += int(line.split(" ")[-1].removesuffix(';'))
    elif regex.match("DECREMENT .* BY .*;", line):
        if line.split(" ")[-1].removesuffix(';').isnumeric():
            globals_pyasm[line.split(" ")[1]] -= int(line.split(" ")[-1].removesuffix(';'))
    # memory management
    elif regex.match("DELETE VAR .*;", line):
        del globals_pyasm[line.split(" ")[2].removesuffix(";")]
    elif regex.match("DELETE FUNC .*;", line):
        del globals_pyasm[line.split(" ")[2].removesuffix(";")]
    # function definition, it just records the code so we can evaluate each line eventually
    elif regex.match("DEFINE FUNC .*;", line):
        __out_function__ = line.split(" ")[2].removesuffix(";")
        globals_pyasm[__out_function__] = []
    # importing
    elif regex.match("INCLUDE .*;", line):
        if regex.match("INCLUDE .* FROM .*;", line):
            try:
                exec(f'from {line.split(" ")[3].removesuffix(";")} import {line.split(" ")[1]}', globals_pyasm)
            except ImportError:
                raise NoImportFound()
        else:
            if os.path.exists(f'{line.split(" ")[1].removesuffix(";")}.pym'):
                __process_file__(f'{line.split(" ")[1].removesuffix(";")}.pym')
            else:
                try:
                    exec(f'import {line.split(" ")[1].removesuffix(";")}', globals_pyasm)
                except ImportError:
                    raise NoImportFound()
    # ah yes, if statements.
    elif regex.match("IF .*;", line):
        __if_cases__.append(" ".join(line.split(" ")[1:]).removesuffix(";"))
        __if_statements__.append([])
        __in_if_statement__ = True
        __if_layers__ += 1

    elif __in_if_statement__ and line == "ENDIF;" and not __ignore_if_statement__:
        __dont_eval__ = False
        for __if_case__ in __if_cases__[:-1]:
            if not eval(__if_case__, globals_pyasm):
                __dont_eval__ = True
                break
        if eval(__if_cases__[-1], globals_pyasm) and not __dont_eval__:
            for l in __if_statements__[-1]:
                process(l, __ignore_while_loop__, True)
        
        __if_statements__.pop()
        __if_cases__.pop()
        __in_if_statement__ = not not __if_statements__
    # while loops
    elif regex.match("WHILE .*;", line):
        __while_statements__.append(" ".join(line.split(" ")[1:]).removesuffix(";"))
        __while_loops__.append([])
        __in_while_loop__ = True
        __force_ignore_while__ = True
    elif __in_while_loop__ and line == "ENDWHILE;" and not __ignore_while_loop__:
        __dont_eval__ = False
        for __WHILE_STATEMENT__ in __while_statements__[:-1]:
            if not eval(__WHILE_STATEMENT__, globals_pyasm):
                __dont_eval__ = True
                break
        while eval(__while_statements__[-1], globals_pyasm) and not __dont_eval__:
            for l in __while_loops__[-1]:
                process(l, True, __ignore_if_statement__)
        __while_loops__.pop()
        __while_statements__.pop()
        __in_while_loop__ = not not __while_loops__
    # should this code be deleted? i dont think so..
    elif line == __skip_until__:
        __skip_until__ = ""
    else:
        # TO-DO:
        # - use another error instead of this, this is for python.
        raise SyntaxError(line)

# check if a file is supplied
if len(sys.argv) < 2:
    while True:
        line = input(">> ")
        process(line)
else:
    # check format and execute each line
    __process_file__(sys.argv[1])
