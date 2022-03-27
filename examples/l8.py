import json
import sys

from mycfg import *
from l5 import *

from reaching_defs import reaching_definitions
from reaching_defs import add_indices


def get_num_mappings(name2block):
    num2label = {}
    num2instr = {}
    for name, instrs in name2block.items():
        for instr, i in instrs:
            num2label[i] = name
            num2instr[i] = instr
    return num2label, num2instr


def get_back_edges(cfg, dominators):
    back_edges = []
    for n, doms in dominators.items():
        for h in doms:
            if h in cfg[n]:
                back_edges.append((n, h))
    return back_edges


def get_natural_loops(cfg):
    preds_cfg = get_preds_cfg(cfg)
    dominators = find_dominators(cfg, preds_cfg)
    back_edges = get_back_edges(cfg, dominators)
    natural_loops = []
    for (n, h) in back_edges:
        body = [h]
        stack = [n]
        while stack:
            d = stack.pop()
            if d not in body:
                body.append(d)
                for pred in preds_cfg[d]:
                    stack.append(pred)
        natural_loops.append(body)
    return natural_loops


def get_reaching_defs_of_var(reaching, var, num2instr):
    defs = []
    for i in reaching:
        instr = num2instr[i]
        if 'dest' in instr and instr['dest'] == var:
            defs.append(i)
    print(f"reaching defs of var: {var} are defs: {defs}")
    return defs


def is_li(reaching, num2label, loop, li):
    print("here in is li")
    all_outside = True
    for i in reaching:
        label = num2label[i]
        if label in loop:
            all_outside = False
    return all_outside or (len(reaching) == 1 and reaching[0] in li)


def identify_li_instrs(natural_loops, reaching_defs, preds_cfg, name2block):
    num2label, num2instr = get_num_mappings(name2block)
    li = set()
    for loop in natural_loops:
        header = loop[0]
        preheader = preds_cfg[header]
        while True:
            li_copy = {elt for elt in li}
            for name in loop:
                block = name2block[name]
                for instr, i in block:
                    if 'args' in instr:
                        flag = True
                        for arg in instr['args']:
                            reaching = get_reaching_defs_of_var(
                                reaching_defs[i], arg, num2instr)
                            if not is_li(reaching, num2label, loop, li):
                                flag = False
                        if flag:
                            li.add(i)
                    elif 'op' in instr and instr['op'] == 'const':
                        li.add(i)
            if li_copy == li:
                break
    print(f"loop invariant stuff: {li}")

# iterate to convergence:
#     for every instruction in the loop:
#         mark it as LI iff, for all arguments x, either:
#             all reaching defintions of x are outside of the loop, or
#             there is exactly one definition, and it is already marked as
#                 loop invariant


def licm(prog):
    reaching_defs = reaching_definitions(prog)
    # print(reaching_defs)

    for func in prog['functions']:
        blocks = func['instrs']
        name2block = block_map(form_blocks(blocks))
        cfg = get_cfg(name2block)
        preds_cfg = get_preds_cfg(cfg)
        name2block = add_indices(name2block)
        # num2label, num2instr = get_num_mappings(name2block)
        # print(num2label)
        natural_loops = get_natural_loops(cfg)
        identify_li_instrs(natural_loops, reaching_defs, preds_cfg, name2block)
        # print(natural_loops)

    # print(json.dumps(prog))


if __name__ == '__main__':
    prog = json.load(sys.stdin)
    licm(prog)
