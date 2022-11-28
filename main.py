import sys
import os
from helpers.pybash_errors import NoImportFound, TooManyArguments

__out_function__ = ""
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
globals_pybash = {}
locals_pybash = {}
__exit_function__ = False

def exit():
    print("Goodbye!")
    sys.exit(0)

def __process_file__(filename):
    with open(filename, 'r') as f:
        lines = f.read().splitlines()
        for i in lines:
            process(i)


def process(line: str, __ignore_while_loops__: bool = False, __ignore_if_statements__: bool = False, __ignore_for_loops__: bool = False) -> None:
    global __out_function__, __while_loops__, __in_while_loop__, __for_loops__, __in_for_loop__, __if_statements__, __in_if_statement__, locals_pybash, __exit_function__, globals_pybash

    # fix indentation
    while line.startswith(' ') or line.startswith('\t'):
        line = line.removeprefix(' ').removeprefix('\t')

    # check for comments or empty lines, ENDIFs or whether we should skip this code in general
    if line.startswith("$") or line == '' or __exit_function__:
        return

    # some function stuff like recording the function code for execution
    if line == "EXIT FUNC;":
        __out_function__ = ""
        return

    if __out_function__:
        globals_pybash[__out_function__][1].append(line)
        return

    # recording if statement code for execution
    if __in_if_statement__ and not line == "ENDIF;" and not line == "ELSE;" and not line.startswith('IF') and not __ignore_if_statements__:
        if not __has_else__[-1][0]:
            __if_statements__[-1].append(line)
        else:
            __has_else__[-1][1].append(line)
        return
    
    # recording while loop code for execution
    if __in_while_loop__ and not line == "ENDWHILE;" and not line.startswith('WHILE') and not __ignore_while_loops__:
        __while_loops__[-1].append(line)
        return
    
    # recording for loop code for execution
    if __in_for_loop__ and not line == "ENDFOR;" and not line.startswith('FOR') and not __ignore_for_loops__:
        __for_loops__[-1].append(line)
        return

    # regex match for function calls with arguments, etc.
    match line.split(' '):
        case ['CALL', function, 'ARGS', *args]:
            if isinstance(globals_pybash.get("".join(function).removesuffix(";"), None), list):
                eval_result = eval(" ".join(args).removesuffix(';'), globals_pybash, locals_pybash)
                if isinstance(eval_result, tuple):
                    for i, arg in enumerate(eval_result):
                        if globals_pybash[function][0].get(i, None):
                            locals_pybash[globals_pybash[function][0][i]] = arg
                        else:
                            break
                else:
                    if len(globals_pybash[function][0]) > 0:
                        locals_pybash[globals_pybash[function][0][0]] = eval_result
                    else:
                        raise TooManyArguments("'" + line + "', You can't pass arguments to a function that takes no arguments.")
                for code in globals_pybash.get("".join(function), None)[1]:
                    process(code, True, True, True)
                __exit_function__ = False
            else:
                exec(f'globals()[\'RETURN\'] = {function}{" ".join(args).removesuffix(";")}', globals_pybash, locals_pybash)
        case ['CALL', *function]:
            if isinstance(globals_pybash.get("-".join(function).removesuffix(";"), None), list):
                for i in globals_pybash.get("-".join(function).removesuffix(";"), None)[1]:
                    process(i)
                __exit_function__ = False
            else:
                exec(f'globals()[\'RETURN\'] = {"-".join(function).removesuffix(";")}()', globals_pybash, locals_pybash)
        # variable manipulation (we have a sandbox so now we dont have to worry about users overwriting runtime vars!)
        case ['SET', variable, 'TO', *value]:
            globals_pybash[variable] = eval(" ".join(value).removesuffix(';'), globals_pybash, locals_pybash)
        case ['INCREMENT', variable, 'BY', amount]:
            if amount.removesuffix(';').isnumeric():
                globals_pybash[variable] += int(amount)
        case ['DECREMENT', variable, 'BY', amount]:
            if amount.removesuffix(';').isnumeric():
                globals_pybash[variable] -= int(amount.removesuffix(';'))
        # memory management
        case ['DELETE', *variable]:
            del globals_pybash["-".join(variable).removesuffix(";")]
        # function definition, it just records the code so we can evaluate each line eventually
        case ['DEFINE', 'FUNC', function, 'ARGS', *args]:
            __out_function__ = function.removesuffix(";")
            globals_pybash[__out_function__] = [{}, []]
            for i, arg in enumerate(args):
                if i == len(args) - 1:
                    globals_pybash[__out_function__][0][i] = arg.removesuffix(";")
                else:
                    globals_pybash[__out_function__][0][i] = arg
        case ['DEFINE', 'FUNC', *function]:
            __out_function__ = "-".join(function).removesuffix(";")
            globals_pybash[__out_function__] = [{}, []]
                        
        # importing
        case ['INCLUDE', obj, 'FROM', library]:
            try:
                exec(f'from {library.removesuffix(";")} import {obj}', globals_pybash)
            except ImportError:
                raise NoImportFound()
        case ['INCLUDE', library]:
            if os.path.exists(f'{library.removesuffix(";")}.pyb'):
                __process_file__(f'{library.removesuffix(";")}.pyb')
            else:
                try:
                    exec(f'import {library.removesuffix(";")}', globals_pybash)
                except ImportError:
                    raise NoImportFound()
        # ah yes, if statements.
        case ['IF', *statement]:
            __if_cases__.append(" ".join(statement).removesuffix(";"))
            __if_statements__.append([])
            __has_else__.append([False, []])
            __in_if_statement__ = True
        case ["ELSE;"]:
            __has_else__[-1][0] = True
        case ["ENDIF;"]:
            if __in_if_statement__ and not __ignore_if_statements__:
                __dont_eval__ = False
                for i, __if_case__ in enumerate(__if_cases__[:-1]):
                    if not eval(__if_case__, globals_pybash, locals_pybash):
                        __dont_eval__ = True
                        break

                if eval(__if_cases__[-1], globals_pybash, locals_pybash) and not __dont_eval__:
                    for l in __if_statements__[-1]:
                        process(l, __ignore_while_loops__, True, __ignore_for_loops__)
                elif __has_else__[-1][0]:
                    for l in __has_else__[-1][1]:
                        process(l, __ignore_while_loops__, True, __ignore_for_loops__)
                
                __if_statements__.pop()
                __if_cases__.pop()
                __has_else__.pop()
                __in_if_statement__ = not not __if_statements__
        # while loops
        case ['WHILE', *statement]:
            __while_statements__.append(" ".join(statement).removesuffix(";"))
            __while_loops__.append([])
            __in_while_loop__ = True
            __force_ignore_while__ = True
        case ["ENDWHILE;"]:
            if __in_while_loop__ and not __ignore_while_loops__:
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
        case ['FOR', *statement, 'AS', variable]:
            __for_statements__.append([" ".join(statement), variable.removesuffix(';')])
            __for_loops__.append([])
            __in_for_loop__ = True
        case ["ENDFOR;"]:
            if __in_for_loop__ and not __ignore_for_loops__:
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
        case ['RETURN', *to_return]:
            globals_pybash['RETURN'] = eval(" ".join(to_return).removesuffix(';'), globals_pybash, locals_pybash)
            __exit_function__ = True
        case other:
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
