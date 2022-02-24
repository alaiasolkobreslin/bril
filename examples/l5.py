import json
import sys

from mycfg import *


def get_preds_cfg(cfg):
    preds = {}
    for name in cfg:
        preds[name] = set()
    for name in cfg:
        for n, succ in cfg.items():
            if name in succ:
                preds[name].add(n)
    return preds


def get_fresh_entry(cfg):
    entry = 'entry'
    if entry not in cfg:
        return entry
    i = 1
    while True:
        new_entry = entry + '.' + str(i)
        if new_entry not in cfg:
            return new_entry
        i += 1


def add_entry(cfg):
    entry = list(cfg.keys())[0]
    for _, succs in cfg.items():
        if entry in succs:
            fresh_entry = get_fresh_entry(cfg)
            cfg[fresh_entry] = [entry]
            print(cfg)
            return fresh_entry
    return entry


def reverse_dominators(dominators):
    rev = {}
    for (block, doms) in dominators.items():
        for block_dom in doms:
            if block_dom in rev:
                rev[block_dom].add(block)
            else:
                rev[block_dom] = {block}
    return rev


def find_dominators(cfg, preds_cfg):
    # TODO: use reverse-post order
    all_blocks = set(cfg.keys())
    dominators = {block: all_blocks for block in cfg}

    while True:
        old_dom = dominators.copy()
        for block in cfg:
            pred_dom = [dominators[p] for p in preds_cfg[block]]
            dominators[block] = {block}
            if pred_dom:
                dominators[block] = dominators[block] | pred_dom[0].intersection(
                    *pred_dom)
        if old_dom == dominators:
            break
    print(f"dominators: {dominators}")
    return dominators


def dominator_tree(cfg, preds_cfg):
    dominators = find_dominators(cfg, preds_cfg)
    dom_tree = {}
    rev_dominators = reverse_dominators(dominators)
    for (block, sub_blocks) in rev_dominators.items():
        children = set()
        for b in sub_blocks:
            if b != block and dominators[b] == dominators[block] | {b}:
                children.add(b)
        dom_tree[block] = children
    print(f"dominator tree: {dom_tree}")
    return dom_tree


def dominance_frontier(cfg, preds_cfg):
    rev_dominators = reverse_dominators(find_dominators(cfg, preds_cfg))
    dom_frontier = {}
    for a in cfg:
        for b in cfg:
            if b not in rev_dominators[a]:
                for pred in preds_cfg[b]:
                    if pred in rev_dominators[a]:
                        if a not in dom_frontier:
                            dom_frontier[a] = set()
                        dom_frontier[a].add(b)
    print(f"dominance frontier: {dom_frontier}")
    return dom_frontier


def dom(prog, typ):
    for func in prog['functions']:
        blocks = form_blocks(func['instrs'])
        name2block = block_map(blocks)
        cfg = get_cfg(name2block)
        add_entry(cfg)
        preds_cfg = get_preds_cfg(cfg)

        if typ == "tree":
            dominator_tree(cfg, preds_cfg)
        elif typ == "frontier":
            dominance_frontier(cfg, preds_cfg)
        else:
            find_dominators(cfg, preds_cfg)


if __name__ == '__main__':
    prog = json.load(sys.stdin)
    args = sys.argv
    typ = 'dominators'
    if len(args) > 1:
        typ = args[1]
    dom(prog, typ)
