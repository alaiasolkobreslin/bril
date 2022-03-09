
import json
import sys
from tkinter import N

from mycfg import *
from l5 import *


def dom_frontier(cfg, d):
    preds_cfg = get_preds_cfg(cfg)
    frontier = dominance_frontier(cfg, preds_cfg)
    return frontier[d]


def get_variable_names(name2block):
    vars = set()
    for _, block in name2block.items():
        for instr in block:
            if 'dest' in instr:
                vars.add(instr['dest'])
    return vars


def get_var_defs(vars, name2block):
    defs = {v: set() for v in vars}
    for v in vars:
        for (name, block) in name2block.items():
            for instr in block:
                if 'dest' in instr and instr['dest'] == v:
                    defs[v].add(name)
    return defs


def insert_phi_nodes(vars, cfg, name2block):
    phi_nodes = {block: set() for block in cfg}
    defs = get_var_defs(vars, name2block)
    for v in vars:
        while True:
            v_defs = defs[v].copy()
            for d in v_defs:  # Blocks where v is assigned
                frontier = dom_frontier(cfg, d)
                for block in frontier:  # Dominance frontier
                    phi_nodes[block].add(v)
                    defs[v].add(block)
            if defs[v] == v_defs:
                break
    return phi_nodes


def rename_variables(vars, cfg, name2block, phi_nodes):

    stack = {v: [v] for v in vars}
    fresh_nums = {v: 0 for v in vars}
    preds_cfg = get_preds_cfg(cfg)
    entry = list(cfg.keys())[0]
    renamed_phi_args = {block: {p: ([], [])
                                for p in phi_nodes[block]} for block in cfg}
    renamed_phi_dests = {block: {p: p
                                 for p in phi_nodes[block]} for block in cfg}
    dominance_tree = dominator_tree(cfg, preds_cfg)

    def push_stack(dest):
        fresh = fresh_nums[dest]
        new_dest = dest + '.' + str(fresh)
        stack[dest].append(new_dest)
        fresh_nums[dest] = fresh + 1
        return new_dest

    def rename(block_name):
        nonlocal stack
        block = name2block[block_name]

        new_stack_items = {v: set() for v in vars}

        for p in phi_nodes[block_name]:
            new_dest = push_stack(p)
            renamed_phi_dests[block_name][p] = new_dest
            new_stack_items[p].add(new_dest)

        for instr in block:
            if 'args' in instr:
                # replace each argument to instr with stack[old name]
                new_args = []
                for arg in instr['args']:
                    if arg in stack:
                        new_args.append(stack[arg][-1])
                    else:
                        new_args.append(arg)
                instr['args'] = new_args

            if 'dest' in instr:
                # replace instr's destination with a new name
                dest = instr['dest']
                if dest in stack:
                    new_dest = push_stack(dest)
                    instr['dest'] = new_dest
                    new_stack_items[dest].add(new_dest)

        for s in cfg[block_name]:
            for p in phi_nodes[s]:
                # Assuming p is for a variable v, make it read from stack[v].
                if p in renamed_phi_args[s]:
                    renamed_phi_args[s][p][0].append(stack[p][-1])
                    renamed_phi_args[s][p][1].append(block_name)
                # else:
                #     pass

        for b in sorted(dominance_tree[block_name]):
            rename(b)

        # pop all the names we just pushed onto the stacks
        for (v, new_items) in new_stack_items.items():
            for s in new_items:
                stack[v].remove(s)

    rename(entry)
    return renamed_phi_args, renamed_phi_dests


def insert_phi_instructions(name2block, renamed_phi_args, renamed_phi_dests, types):
    for name, block in name2block.items():
        phi_args = renamed_phi_args[name]
        phi_dests = renamed_phi_dests[name]
        for (p, dest) in phi_dests.items():
            args = phi_args[p][0]
            instr = {
                "op": "phi",
                "dest": dest,
                "args": args,
                "labels": [labels for labels in phi_args[p][1]],
                "type": types[p]
            }

            block.insert(0, instr)


def get_types(name2block):
    types = {}
    for _, block in name2block.items():
        for instr in block:
            if 'type' in instr:
                types[instr['dest']] = instr['type']
    return types


def from_ssa(name2block, blocks):
    # insert id instructions
    for block in blocks:
        for instr in block:
            if 'op' in instr and instr['op'] == 'phi':
                print('yeet skeet got here')
                for i, label in enumerate(instr['labels']):
                    arg = instr['args'][i]
                    last_block = name2block[label]
                    new_instr = {
                        "op": "id",
                        "dest": instr['dest'],
                        "type": instr['type'],
                        "args": [arg]
                    }
                    last_block.insert(-1, new_instr)

    # remove phi nodes
    new_blocks = []
    for block in blocks:
        new_block = []
        for instr in block:
            if 'op' not in instr or instr['op'] != 'phi':
                new_block.append(instr)
        new_blocks.append(block)
    return new_blocks


def ssa():
    prog = json.load(sys.stdin)
    for func in prog['functions']:
        blocks = []
        for block in form_blocks(func['instrs']):
            blocks.append(block)
        name2block = block_map(form_blocks(func['instrs']))
        types = get_types(name2block)
        cfg = get_cfg(name2block)
        vars = get_variable_names(name2block)
        phi_nodes = insert_phi_nodes(vars, cfg, name2block)
        renamed_phi_args, renamed_phi_dests = rename_variables(
            vars, cfg, name2block, phi_nodes)
        insert_phi_instructions(
            name2block, renamed_phi_args, renamed_phi_dests, types)
        new_blocks = from_ssa(name2block, blocks)
        func['instrs'] = new_blocks
    print(json.dumps(prog))


if __name__ == '__main__':
    ssa()
