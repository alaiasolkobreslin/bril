import json
import sys

from mycfg import *
from l5 import *

from reaching_defs import reaching_definitions
from reaching_defs import add_indices
from cfg import add_terminators


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
    return defs


def is_li(reaching, num2label, loop, li, instr):
    # op = instr['op']
    # if op == 'call' or op == 'ptradd':
    #     return False
    all_outside = True
    for i in reaching:
        label = num2label[i]
        if label in loop:
            all_outside = False
    return all_outside or (len(reaching) == 1 and reaching[0] in li)


def def_dominates_all_uses(name2block, reverse_dominators, num2label, var, i):
    i_block = num2label[i]
    dominates = reverse_dominators[i_block]
    uses = set()
    for _, block in name2block.items():
        for instr, j in block:
            if 'args' in instr and var in instr['args']:
                # This is a use
                uses.add(num2label[j])
    for use in uses:
        if use not in dominates:
            return False
    return True


def no_other_defs_exist(var, loop, name2block, i):
    # Checks that no other definitions of the same variable exist in the loop
    for name in loop:
        block = name2block[name]
        for instr, j in block:
            if j == i:
                continue
            if 'dest' in instr and instr['dest'] == var:
                return False
    return True


def instr_dominates_loop_exits(reverse_dominators, loop, cfg, num2label, name2block, i, var, instr):
    def is_exit(name):
        for label in cfg[name]:
            if label not in loop:
                return True
        return False

    # Check that the instruction dominates all loop exits.
    instr_label = num2label[i]
    loop_exits = []
    for block in loop:
        if is_exit(block):
            loop_exits.append(block)
    flag = True
    for exit in loop_exits:
        if block not in reverse_dominators[instr_label]:
            flag = False
    if flag:
        return True

    # Check for side effects:
    # op = instr['op']
    # if op == 'call' or op == 'ptradd':
    #     return False

    # Check that the The assigned-to variable is dead after the loop
    seen = set()
    stack = []
    for exit in loop_exits:
        seen.add(exit)
        stack.append(exit)
    while stack:
        curr = stack.pop()
        block = name2block[curr]
        for instr in block:
            if 'args' in instr and var in instr['args']:
                return False
        for succ in cfg[curr]:
            if succ not in seen:
                stack.append(succ)
                seen.add(succ)

    return True


def safe_to_move(name2block, reverse_dominators, num2label, loop, cfg, var, i, instr):
    return def_dominates_all_uses(
        name2block, reverse_dominators, num2label, var, i) and no_other_defs_exist(
            var, loop, name2block, i) and instr_dominates_loop_exits(
                reverse_dominators, loop, cfg, num2label, name2block, i, var, instr)


def flatten_blocks(name2block):
    flattened = []
    for name, block in name2block.items():
        flattened.append({"label": name})
        for instr, _ in block:
            flattened.append(instr)
    return flattened


def identify_li_instrs(natural_loops, reaching_defs, cfg, preds_cfg, name2block):
    num2label, num2instr = get_num_mappings(name2block)
    dominators = find_dominators(cfg, preds_cfg)
    rev_dominators = reverse_dominators(dominators)
    for loop in natural_loops:
        li = set()
        header = loop[0]
        preheader_name = None
        for pred in preds_cfg[header]:
            if pred not in loop:
                preheader_name = pred
        preheader = name2block[preheader_name]
        while True:
            li_copy = {elt for elt in li}
            for name in loop:
                block = name2block[name]
                for instr, i in block:
                    op = instr['op']
                    if op == 'br' or op == 'ret' or op == 'print':
                        continue
                    if 'args' in instr:
                        flag = True
                        for arg in instr['args']:
                            reaching = get_reaching_defs_of_var(
                                reaching_defs[i], arg, num2instr)
                            if not is_li(reaching, num2label, loop, li, instr):
                                flag = False
                        if flag:
                            li.add(i)
                    elif 'op' in instr and instr['op'] == 'const':
                        li.add(i)
            if li_copy == li:
                break
        for i in li:
            # print(f"instr {num2instr[i]}")
            instr = num2instr[i]
            var = instr['dest']
            if safe_to_move(name2block, rev_dominators, num2label, loop, cfg, var, i, instr):
                block = name2block[num2label[i]]
                for k, (instr, j) in enumerate(block):
                    if j == i:
                        del block[k]
                        break
                # preheader.insert(len(preheader)-1, (num2instr[i], i))
                preheader.append((num2instr[i], i))
                # preheader.append((num2instr[i], i))
                num2label[i] = preheader_name

    return flatten_blocks(name2block)


def licm(prog):

    for func in prog['functions']:
        reaching_defs = reaching_definitions(func)
        blocks = func['instrs']
        name2block = block_map(form_blocks(blocks))
        # add_terminators(name2block)
        cfg = get_cfg(name2block)
        preds_cfg = get_preds_cfg(cfg)
        name2block = add_indices(name2block)
        natural_loops = get_natural_loops(cfg)
        new_blocks = identify_li_instrs(natural_loops, reaching_defs,
                                        cfg, preds_cfg, name2block)
        func['instrs'] = new_blocks

    print(json.dumps(prog))


if __name__ == '__main__':
    prog = json.load(sys.stdin)
    licm(prog)
