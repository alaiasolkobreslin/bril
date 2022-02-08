import json
import sys
from collections import OrderedDict

TERMINATORS = 'jmp', 'br', 'ret'


def form_blocks(body):
    cur_block = []

    for instr in body:
        if 'op' in instr:  # An actual instruction
            cur_block.append(instr)

            # Check for terminator
            if instr['op'] in TERMINATORS:
                yield cur_block
                cur_block = []

        else:  # A label
            if cur_block:
                yield cur_block

            cur_block = [instr]

    if cur_block:
        yield cur_block


def dce():
    prog = json.load(sys.stdin)
    new_funcs = []
    for func in prog['functions']:
        blocks = form_blocks(func['instrs'])
        new_blocks = []
        for block in blocks:
            while True:
                to_delete = set()
                last_def = {}
                for i, instr in enumerate(block):
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
                new_block = [instr for i, instr in enumerate(
                    block) if i not in to_delete]
                if block == new_block:
                    break
                block = new_block
            new_blocks += block
        func['instrs'] = new_blocks
        new_funcs.append(func)
    prog['functions'] = new_funcs
    print(json.dumps(prog))


if __name__ == '__main__':
    dce()
