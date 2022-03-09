
import json
import sys

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
                print(f"frontier: {frontier}")
                for block in frontier:  # Dominance frontier
                    phi_nodes[block].add(v)
                    defs[v].add(block)
            if defs[v] == v_defs:
                break
    print(phi_nodes)
    return phi_nodes


def rename_variables(vars, cfg, name2block, phi_nodes):

    stack = {v: [v] for v in vars}
    fresh_nums = {v: 0 for v in vars}
    preds_cfg = get_preds_cfg(cfg)
    entry = list(cfg.keys())[0]
    renamed_phi_args = {block: {p: []
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
        old_stack = {k: v for (k, v) in stack.items()}
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
                    renamed_phi_args[s][p].append(stack[p][-1])
                else:
                    pass

        for b in dominance_tree[block_name]:
            rename(b)

        # pop all the names we just pushed onto the stacks
        print(f"stack before clear: {stack}")
        # stack.clear()
        # stack.update(old_stack)
        for (v, s) in new_stack_items.items():
            if s in stack[v]:
                print('yeet here')
                stack[v].remove(s)
        print(f"stack after clear: {stack}")

    rename(entry)
    print(name2block)

# stack[v] is a stack of variable names (for every variable v)

# def rename(block):
#   for instr in block:
#     replace each argument to instr with stack[old name]

#     replace instr's destination with a new name
#     push that new name onto stack[old name]

#   for s in block's successors:
#     for p in s's ϕ-nodes:
#       Assuming p is for a variable v, make it read from stack[v].

#   for b in blocks immediately dominated by block:
#     # That is, children in the dominance tree.
#     rename(b)

#   pop all the names we just pushed onto the stacks

# rename(entry)


def to_ssa():
    prog = json.load(sys.stdin)
    for func in prog['functions']:
        name2block = block_map(form_blocks(func['instrs']))
        cfg = get_cfg(name2block)
        vars = get_variable_names(name2block)
        phi_nodes = insert_phi_nodes(vars, cfg, name2block)
        rename_variables(vars, cfg, name2block, phi_nodes)
        print(dict)


if __name__ == '__main__':
    to_ssa()
