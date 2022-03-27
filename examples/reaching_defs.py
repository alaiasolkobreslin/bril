import json
import sys
from collections import OrderedDict

from mycfg import *


def get_cfg(name2block, init):
    """ Given a name-to-block map, produce a mapping from block names to successor block names.
    """
    out = {}
    for i, (name, block) in enumerate(name2block.items()):
        last = block[-1]
        if last['op'] in ('jmp', 'br'):
            succ = last['labels']
        elif last['op'] == 'ret':
            succ = []
        else:
            if i == len(name2block) - 1:
                succ = []
            else:
                succ = [list(name2block.keys())[i+1]]

        out[name] = (succ, init, init)

    return out


def get_preds_cfg(cfg):
    preds = {}
    for name in cfg:
        preds[name] = set()
    for name in cfg:
        for (n, (succ, _, _)) in cfg.items():
            if name in succ:
                preds[name].add(n)
    return preds

# Domain: sets of defs (should be map?)
# Direction: Forward
# Merge: Union


def transfer(in_set, block, defs_map, num2reaching):
    out_set: set = in_set.copy()
    for instr, i in block:
        num2reaching[i] = {elt for elt in out_set}
        if 'dest' in instr:
            dest = instr['dest']
            kills = defs_map[dest]
            out_set = out_set.difference(kills)
            out_set.add(i)
    return out_set


def meet(val_dicts):
    return set().union(*val_dicts)


def reaching_defs_worklist(cfg, preds_cfg, block, name2block):
    num2reaching = {}
    defs_map = get_defs_map(name2block)
    worklist = set()
    # Initialize worklist: each element is a block name
    for block in name2block:
        worklist.add(block)
    while worklist:
        # Pop off a block from the worklist
        block = worklist.pop()
        (succs, _, out_set_init) = cfg[block]
        out_sets = [cfg[pred][2] for pred in preds_cfg[block]]
        in_set = meet(out_sets)
        out_set = transfer(in_set, name2block[block], defs_map, num2reaching)
        if out_set != out_set_init:
            for succ in succs:
                worklist.add(succ)
        cfg[block] = (succs, in_set, out_set)
    print(num2reaching)
    return num2reaching


def print_set(s):
    sorted_set = sorted(list(s))
    if not sorted_set:
        print('{}')
        return
    flag = True
    for item in sorted_set:
        if flag:
            flag = False
        else:
            print(", ", end="")
        print(item, end="")
    print()


def add_indices(name2block):
    out = OrderedDict()

    i = 0
    for name, instrs in name2block.items():
        new_block = []
        for instr in instrs:
            new_block.append((instr, i))
            i += 1
        out[name] = new_block
    return out


def get_defs_map(name2block):
    out = {}
    for _, instrs in name2block.items():
        for (instr, i) in instrs:
            if 'dest' in instr:
                dest = instr['dest']
                if dest in out:
                    out[dest].add(i)
                else:
                    out[dest] = {i}
    return out


def reaching_definitions(prog):
    for func in prog['functions']:
        block = func['instrs']
        name2block = block_map(form_blocks(block))
        cfg = get_cfg(name2block, {})
        preds_cfg = get_preds_cfg(cfg)
        name2block = add_indices(name2block)
        print(f"name2block: {name2block}")
        return reaching_defs_worklist(cfg, preds_cfg, block, name2block)
        # return cfg
        # for (block, (_, in_set, out_set)) in cfg.items():
        #     print(f'{block}:')
        #     print('\tin', end=":  ")
        #     print_set(in_set)
        #     print('\tout', end=":  ")
        #     print_set(out_set)


if __name__ == '__main__':
    prog = json.load(sys.stdin)
    reaching_definitions(prog)
