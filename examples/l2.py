import json
import sys


def add_prints():
    """
    Adds an instruction that prints the number 42 before every jump instruction
    If another instruction stores a different value in dest "v" before the print
    then that value will be printed instead.
    """
    prog = json.load(sys.stdin)
    set_var = {"dest": "v",
               "op": "const",
               "type": "int",
               "value": 42}
    print_var = {"args": ["v"],
                 "op": "print"}
    for func in prog['functions']:
        instrs_modified = [set_var]
        for instr in func['instrs']:
            if 'op' in instr:
                if instr['op'] == 'jmp':
                    instrs_modified .append(print_var)
            instrs_modified.append(instr)
        func['instrs'] = instrs_modified
    print(json.dumps(prog))


if __name__ == '__main__':
    add_prints()
