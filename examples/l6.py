
import json
import sys
from tkinter import N

from collections import defaultdict

from mycfg import *
from l5 import *
from cfg import add_entry, add_terminators


def dom_frontier(cfg):
    preds_cfg = get_preds_cfg(cfg)
    frontier = dominance_frontier(cfg, preds_cfg)
    return frontier


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
    frontier = dom_frontier(cfg)
    for v in vars:
        while True:
            v_defs = defs[v].copy()
            for d in v_defs:  # Blocks where v is assigned
                for block in frontier[d]:  # Dominance frontier
                    phi_nodes[block].add(v)
                    defs[v].add(block)
            if defs[v] == v_defs:
                break
    return phi_nodes


def rename_variables(vars, cfg, name2block, phi_nodes, fn_arguments):

    # stack initally contains only the function arguments
    stack = defaultdict(list, {a: [a] for a in fn_arguments})
    # fresh_nums keeps track of the counter for each var and is used for renaming
    fresh_nums = {v: 0 for v in vars}
    # predecessors cfg
    preds_cfg = get_preds_cfg(cfg)
    entry = list(cfg.keys())[0]
    # renamed_phi_args keeps a set of (argname, label) pairs associated with
    # each phi node
    renamed_phi_args = {block: {p: set()
                                for p in phi_nodes[block]} for block in cfg}
    # renamed_phi_dests keeps a dest name associated with each phi node
    renamed_phi_dests = {block: {p: p
                                 for p in phi_nodes[block]} for block in cfg}
    dominance_tree = dominator_tree(cfg, preds_cfg)

    def push_stack(dest):
        fresh = fresh_nums[dest]
        new_dest = dest + '.' + str(fresh)
        if dest not in stack:
            stack[dest] = [new_dest]
        else:
            stack[dest].append(new_dest)
        fresh_nums[dest] = fresh + 1
        return new_dest

    def rename(block_name):
        nonlocal stack
        block = name2block[block_name]

        # keep track of new elements pushed onto the stack during this call
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
                    if stack[arg]:
                        new_args.append(stack[arg][-1])
                    else:
                        new_args.append(arg)
                instr['args'] = new_args

            if 'dest' in instr:
                # replace instr's destination with a new name
                dest = instr['dest']
                new_dest = push_stack(dest)
                instr['dest'] = new_dest
                new_stack_items[dest].add(new_dest)

        for s in cfg[block_name]:
            for p in phi_nodes[s]:
                # Assuming p is for a variable v, make it read from stack[v].
                renamed = None
                if stack[p]:
                    renamed = (stack[p][-1], block_name)
                else:
                    renamed = ('undefined', block_name)
                renamed_phi_args[s][p].add(renamed)

        for b in dominance_tree[block_name]:
            rename(b)

        # pop all the names we just pushed onto the stacks
        # (I realize this is a really silly way of resetting the stack)
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
            instr = {
                "op": "phi",
                "dest": dest,
                "args": [block_label[0] for block_label in phi_args[p]],
                "labels": [block_label[1] for block_label in phi_args[p]],
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


def remove_phis(name2block, blocks):
    # insert id instructions
    for instr in blocks:
        if 'op' in instr and instr['op'] == 'phi':
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

    blocks = flatten_blocks(name2block)
    # remove phi nodes
    new_blocks = []
    for instr in blocks:
        if 'op' not in instr or instr['op'] != 'phi':
            new_blocks.append(instr)
    return new_blocks


def flatten_blocks(name2block):
    flattened = []
    for name, block in name2block.items():
        flattened.append({"label": name})
        flattened += block
    return flattened


def to_ssa(prog):
    for func in prog['functions']:
        if 'args' in func:
            fn_arguments = {arg['name'] for arg in func['args']}
        else:
            fn_arguments = set()
        name2block = block_map(form_blocks(func['instrs']))
        add_entry(name2block)
        add_terminators(name2block)
        types = get_types(name2block)
        cfg = get_cfg(name2block)
        vars = get_variable_names(name2block)
        phi_nodes = insert_phi_nodes(vars, cfg, name2block)
        renamed_phi_args, renamed_phi_dests = rename_variables(
            vars, cfg, name2block, phi_nodes, fn_arguments)
        insert_phi_instructions(
            name2block, renamed_phi_args, renamed_phi_dests, types)
        new_blocks = flatten_blocks(name2block)
        func['instrs'] = new_blocks
    print(json.dumps(prog))


def from_ssa(prog):
    for func in prog['functions']:
        blocks = func['instrs']
        name2block = block_map(form_blocks(blocks))
        new_blocks = remove_phis(name2block, blocks)
        func['instrs'] = new_blocks
    print(json.dumps(prog))


if __name__ == '__main__':
    prog = json.load(sys.stdin)
    args = sys.argv
    typ = '--to-ssa'
    if len(args) > 1:
        typ = args[1]
    if typ == '--from-ssa':
        from_ssa(prog)
    else:
        to_ssa(prog)
