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


def get_predecessors(name, cfg):
    preds = set()
    for (block, (succ, _, _)) in cfg.items():
        if name in succ:
            preds.add(block)
    return preds


def block_map(blocks):
    out = OrderedDict()

    for block in blocks:
        if 'label' in block[0]:
            name = block[0]['label']
            block = block[1:]
        else:
            name = 'b{}'.format(len(out))
        out[name] = block

    return out


def transfer(in_dict, block):
    out_dict = in_dict.copy()
    for instr in block:
        if 'dest' in instr:
            dest = instr['dest']
            if 'value' in instr:
                out_dict[dest] = instr['value']
            else:
                out_dict[dest] = '?'
    return out_dict


def meet(val_dicts):
    out_dict = {}
    for val_dict in val_dicts:
        if not val_dict:
            continue
        for (key, val) in val_dict.items():
            if val == '?':
                out_dict[key] = val
            elif key in out_dict:
                if val == out_dict[key]:
                    continue
                out_dict[key] = '?'
            else:
                out_dict[key] = val
    return out_dict


def constant_prop_worklist(cfg, preds_cfg, name2block):
    worklist = set()
    # Initialize worklist: each element is a block name
    for block in name2block:
        worklist.add(block)
    while worklist:
        # Pop off a block from the worklist
        block = worklist.pop()
        (succs, _, out_dict_init) = cfg[block]
        out_dicts = [cfg[pred][2] for pred in preds_cfg[block]]
        in_dict = meet(out_dicts)
        out_dict = transfer(in_dict, name2block[block])
        if out_dict != out_dict_init:
            for succ in succs:
                worklist.add(succ)
        cfg[block] = (succs, in_dict, out_dict)


def print_dict(dict):
    sorted_keys = sorted(dict.keys())
    if not sorted_keys:
        print('{}')
        return
    flag = True
    for key in sorted_keys:
        if flag:
            flag = False
        else:
            print(", ", end="")
        print(key, end=": ")
        print(dict[key], end="")
    print()


def constant_propagation():
    prog = json.load(sys.stdin)
    for func in prog['functions']:
        name2block = block_map(form_blocks(func['instrs']))
        cfg = get_cfg(name2block, {})
        preds_cfg = get_preds_cfg(cfg)
        constant_prop_worklist(cfg, preds_cfg, name2block)
        for (block, (_, in_dict, out_dict)) in cfg.items():
            print(f'{block}:')
            print('\tin', end=":  ")
            print_dict(in_dict)
            print('\tout', end=":  ")
            print_dict(out_dict)


if __name__ == '__main__':
    constant_propagation()
