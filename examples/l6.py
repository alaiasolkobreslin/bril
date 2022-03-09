
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
    return phi_nodes


def rename_variables(vars, cfg, name2block, phi_nodes):

    global stack
    stack = {v: [v] for v in vars}
    items = stack.items()
    fresh_nums = {v: 0 for v in vars}
    preds_cfg = get_preds_cfg(cfg)
    entry = list(cfg.keys())[0]

    def _rename(block_name):
        old_stack = stack.copy()
        block = name2block[block_name]
        for instr in block:
            names_pushed = {v: set() for v in vars}

            if 'args' in instr:
                # replace each argument to instr with stack[old name]
                new_args = [stack[arg][-1] for arg in instr['args']]
                instr['args'] = new_args

            if 'dest' in instr:
                # replace instr's destination with a new name
                dest = instr['dest']
                new_dest = instr['dest'] + '.' + str(fresh_nums[dest])
                instr['dest'] = new_dest
                stack[dest].append(new_dest)
                names_pushed[dest].add(new_dest)
                fresh_nums[dest] = fresh_nums[dest] + 1

            for s in preds_cfg[block_name]:
                for p in phi_nodes[s]:
                    pass  # TODO

            for b in cfg[block_name]:
                _rename(b)

            # pop all the names we just pushed onto the stacks
            stack = old_stack

    idk = _rename(entry)

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
