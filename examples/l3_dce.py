import json
import sys


def dce():
    prog = json.load(sys.stdin)
    new_funcs = []
    for func in prog['functions']:
        instrs = func['instrs']
        new_func = []
        while True:
            to_delete = set()
            last_def = {}
            for i, instr in enumerate(instrs):
                # Check for uses
                if 'args' in instr:
                    for arg in instr['args']:
                        if arg in last_def:
                            last_def.pop(arg)

                if 'dest' in instr:
                    # Check for defs
                    if instr['dest'] in last_def:
                        to_delete.add(last_def[instr['dest']])
                    last_def[instr['dest']] = i
            for i in last_def.values():
                to_delete.add(i)
            new_func = [instr for i, instr in enumerate(
                instrs) if i not in to_delete]
            if instrs == new_func:
                break
            instrs = new_func
        func['instrs'] = new_func
        new_funcs.append(func)
    prog['functions'] = new_funcs
    print(json.dumps(prog))


if __name__ == '__main__':
    dce()
