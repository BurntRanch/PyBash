import regex
import sys
import os
from helpers.pybash_errors import NoImportFound, TooManyArguments
from helpers.pybash_warns import Log
import argparse

__out_function__ = ""
__skip_until__ = ""
__in_while_loop__ = False
__while_loops__ = []
__while_statements__ = []
__in_for_loop__ = False
__for_loops__ = []
__for_statements__ = []
__if_statements__ = []
__in_if_statement__ = False
__if_cases__ = []
__has_else__ = []
__if_return__ = False
__if_layers__ = 0
globals_pybash = {}
locals_pybash = {}
__exit_function__ = False
__min_severity__ = 1

def exit():
    print("Goodbye!")
    sys.exit(0)

def __process_file__(filename):
    with open(filename, 'r') as f:
        lines = f.read().splitlines()
        for i in lines:
            process(i)


def process(line, __ignore_while_loops__ = False, __ignore_if_statements__ = False, __ignore_for_loops__ = False):
    global __out_function__, __skip_until__, __while_loops__, __in_while_loop__, __for_loops__, __in_for_loop__, __if_statements__, __in_if_statement__, __if_layers__, locals_pybash, __exit_function__, globals_pybash, locals_pybash

    # fix indentation
    while line.startswith(' ') or line.startswith('\t'):
        line = line.removeprefix(' ').removeprefix('\t')

    # check for comments or empty lines, ENDIFs or whether we should skip this code in general
    if line.startswith("$") or line == '' or (__skip_until__ and (not line.endswith(__skip_until__))) or __exit_function__:
        return

    # some function stuff like recording the function code for execution
    if line == "EXIT FUNC;":
        __out_function__ = ""
        return

    if __out_function__:
        globals_pybash[__out_function__][1].append(line)
        return

    # recording if statement code for execution
    if __in_if_statement__ and not line == "ENDIF;" and not line == "ELSE;" and not regex.match("IF .*;", line) and not __ignore_if_statements__:
        if not __has_else__[-1][0]:
            __if_statements__[-1].append(line)
        else:
            __has_else__[-1][1].append(line)
        return
    
    # recording while loop code for execution
    if __in_while_loop__ and not line == "ENDWHILE;" and not regex.match("WHILE .*;", line) and not __ignore_while_loops__:
        __while_loops__[-1].append(line)
        return
    
    # recording for loop code for execution
    if __in_for_loop__ and not line == "ENDFOR;" and not regex.match("FOR .*;", line) and not __ignore_for_loops__:
        __for_loops__[-1].append(line)
        return

    # regex match for function calls with arguments, etc.
    if regex.match("CALL .*;", line):
        if regex.match("CALL .* ARGS \(.*\);", line):
            if isinstance(globals_pybash.get("".join(line.split(" ")[1]).removesuffix(";"), None), list):
                eval_result = eval(" ".join(line.split(" ")[3:]).removesuffix(';'), globals_pybash, locals_pybash)
                if isinstance(eval_result, tuple):
                    for i, arg in enumerate(eval_result):
                        if globals_pybash[line.split(" ")[1]][0].get(i, None):
                            locals_pybash[globals_pybash[line.split(" ")[1]][0][i]] = arg
                        else:
                            break
                else:
                    if len(globals_pybash[line.split(" ")[1]][0]) > 0:
                        locals_pybash[globals_pybash[line.split(" ")[1]][0][0]] = eval_result
                    else:
                        raise TooManyArguments("'" + line + "', You can't pass arguments to a function that takes no arguments.")
                for code in globals_pybash.get("".join(line.split(" ")[1]), None)[1]:
                    process(code, True, True, True)
                __exit_function__ = False
            else:
                exec(f'globals()[\'RETURN\'] = {line.split(" ")[1]}{" ".join(line.split(" ")[3:]).removesuffix(";")}', globals_pybash, locals_pybash)
        else:
            if isinstance(globals_pybash.get("".join(line.split(" ")[1]).removesuffix(";"), None), list):
                for i in globals_pybash.get("".join(line.split(" ")[1]).removesuffix(";"), None)[1]:
                    process(i)
                __exit_function__ = False
            else:
                exec(f'globals()[\'RETURN\'] = {"".join(line.split(" ")[1]).removesuffix(";")}()', globals_pybash, locals_pybash)
    # variable manipulation (we have a sandbox so now we dont have to worry about users overwriting runtime vars!)
    elif regex.match("SET .* TO .*;", line):
        globals_pybash[line.split(" ")[1]] = eval(" ".join(line.split(" ")[3:]).removesuffix(";"), globals_pybash, locals_pybash)
    elif regex.match("INCREMENT .* BY .*;", line):
        if line.split(" ")[-1].removesuffix(';').isnumeric():
            globals_pybash[line.split(" ")[1]] += int(line.split(" ")[-1].removesuffix(';'))
    elif regex.match("DECREMENT .* BY .*;", line):
        if line.split(" ")[-1].removesuffix(';').isnumeric():
            globals_pybash[line.split(" ")[1]] -= int(line.split(" ")[-1].removesuffix(';'))
    # memory management
    elif regex.match("DELETE VAR .*;", line):
        del globals_pybash[line.split(" ")[2].removesuffix(";")]
    elif regex.match("DELETE FUNC .*;", line):
        del globals_pybash[line.split(" ")[2].removesuffix(";")]
    # function definition, it just records the code so we can evaluate each line eventually
    elif regex.match("DEFINE FUNC .*;", line):
        __out_function__ = line.split(" ")[2].removesuffix(";")
        globals_pybash[__out_function__] = [{}, []]
        if regex.match("DEFINE FUNC .* ARGS .*;", line):
            for i, arg in enumerate(line.split(" ")[4:]):
                if i == len(line.split(" ")[4:]) - 1:
                    globals_pybash[__out_function__][0][i] = arg.removesuffix(";")
                else:
                    globals_pybash[__out_function__][0][i] = arg
                    
    # importing
    elif regex.match("INCLUDE .*;", line):
        if regex.match("INCLUDE .* FROM .*;", line):
            try:
                exec(f'from {line.split(" ")[3].removesuffix(";")} import {line.split(" ")[1]}', globals_pybash)
            except ImportError:
                raise NoImportFound()
        else:
            if os.path.exists(f'{line.split(" ")[1].removesuffix(";")}.pyb'):
                __process_file__(f'{line.split(" ")[1].removesuffix(";")}.pyb')
            else:
                try:
                    exec(f'import {line.split(" ")[1].removesuffix(";")}', globals_pybash)
                except ImportError:
                    raise NoImportFound()
    # ah yes, if statements.
    elif regex.match("IF .*;", line):
        __if_cases__.append(" ".join(line.split(" ")[1:]).removesuffix(";"))
        __if_statements__.append([])
        __has_else__.append([False, []])
        __in_if_statement__ = True
    elif line == "ELSE;":
        __has_else__[-1][0] = True
    elif __in_if_statement__ and line == "ENDIF;" and not __ignore_if_statements__:
        __dont_eval__ = False
        for i, __if_case__ in enumerate(__if_cases__[:-1]):
            if not eval(__if_case__, globals_pybash, locals_pybash):
                __dont_eval__ = True
                break

        if eval(__if_cases__[-1], globals_pybash, locals_pybash) and not __dont_eval__:
            for l in __if_statements__[-1]:
                process(l, __ignore_while_loops__, True)
        elif __has_else__[-1][0]:
            for l in __has_else__[-1][1]:
                process(l, __ignore_while_loops__, True)
        
        __if_statements__.pop()
        __if_cases__.pop()
        __has_else__.pop()
        __in_if_statement__ = not not __if_statements__
    # while loops
    elif regex.match("WHILE .*;", line):
        __while_statements__.append(" ".join(line.split(" ")[1:]).removesuffix(";"))
        __while_loops__.append([])
        __in_while_loop__ = True
        __force_ignore_while__ = True
    elif __in_while_loop__ and line == "ENDWHILE;" and not __ignore_while_loops__:
        __dont_eval__ = False
        for __WHILE_STATEMENT__ in __while_statements__[:-1]:
            if not eval(__WHILE_STATEMENT__, globals_pybash, locals_pybash):
                __dont_eval__ = True
                break
        while eval(__while_statements__[-1], globals_pybash, locals_pybash) and not __dont_eval__:
            for l in __while_loops__[-1]:
                process(l, True, __ignore_if_statements__)
        __while_loops__.pop()
        __while_statements__.pop()
        __in_while_loop__ = not not __while_loops__
    # for loops
    elif regex.match("FOR .* AS .*;", line):
        __for_statements__.append([" ".join(line.split("AS")[0].split(" ")[1:]), line.split("AS")[1].split(" ")[-1].removesuffix(';')])
        __for_loops__.append([])
        __in_for_loop__ = True
    elif __in_for_loop__ and line == "ENDFOR;" and not __ignore_for_loops__:
        __dont_eval__ = False
        for __FOR_STATEMENT__ in __for_statements__[:-1]:
            if not eval(__FOR_STATEMENT__[0], globals_pybash, locals_pybash):
                __dont_eval__ = True
                break
        eval_result = eval(__for_statements__[-1][0], globals_pybash, locals_pybash)
        i = 0
        for __FOR_RESULT__ in eval_result:
            if isinstance(eval_result, list | tuple):
                if len(eval_result) > i:
                    globals_pybash[__for_statements__[-1][1]] = eval_result[i]
                else:
                    break
            else:
                globals_pybash[__for_statements__[-1][1]] = eval_result
            for l in __for_loops__[-1]:
                process(l, __ignore_while_loops__, __ignore_if_statements__, True)
            i += 1
        __for_loops__.pop()
        __for_statements__.pop()
        __in_for_loop__ = not not __for_loops__
    elif regex.match("RETURN .*;", line):
        globals_pybash['RETURN'] = eval(" ".join(line.split(" ")[1:]).removesuffix(';'), globals_pybash, locals_pybash)
        __exit_function__ = True
    # should this code be deleted? i dont think so..
    elif line == __skip_until__:
        __skip_until__ = ""
    else:
        # TO-DO:
        # - use another error instead of this, this is for python.
        if line != "ENDWHILE;" and line != "ENDIF;":
            raise SyntaxError(line)

# check if a file is supplied
if len(sys.argv) < 2:
    while True:
        line = input(">> ")
        process(line)
else:
    # execute each line
    __process_file__(sys.argv[1])
