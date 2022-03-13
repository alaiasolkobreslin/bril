from l5 import *


def get_paths_from_entry_to_b(cfg, entry, b, current_path):
    current_path = current_path + [entry]
    if entry == b:
        return [current_path]
    paths = []
    for block in cfg[entry]:
        if block not in current_path:
            new_path = get_paths_from_entry_to_b(cfg, block, b, current_path)
            paths += new_path
    return paths


def does_dominate(cfg, entry, a, b):
    paths = get_paths_from_entry_to_b(cfg, entry, b, [])
    for path in paths:
        if a not in path:
            return False
    return True


def find_dominators_correct(dominators, cfg, entry):
    for block, doms in dominators.items():
        for a in doms:
            if not does_dominate(cfg, entry, a, block):
                return False
    return True


def dominator_tree_correct(dom_tree, cfg, entry):
    for a, children in dom_tree.items():
        # Check that children are dominated by block
        for b in children:
            if not does_dominate(cfg, entry, a, b):
                return False
        # Check that block only has one parent
        parents = 0
        for node in cfg:
            if a in dom_tree[node]:
                parents += 1
        if parents > 1:
            return False
    return True


def dominance_frontier_correct(dom_frontier, cfg, preds_cfg, entry):
    for a, frontier in dom_frontier.items():
        for b in frontier:
            if does_dominate(cfg, entry, a, b) and a != b:
                return False
            does_dominate_some_pred = False
            for pred in preds_cfg:
                if does_dominate(cfg, entry, a, pred):
                    does_dominate_some_pred = True
            if not does_dominate_some_pred:
                return False
    return True


def dom_test(prog, typ):
    for func in prog['functions']:
        blocks = form_blocks(func['instrs'])
        name2block = block_map(blocks)
        cfg = get_cfg(name2block)
        entry = add_entry(cfg)
        preds_cfg = get_preds_cfg(cfg)

    if typ == "tree":
        tree = dominator_tree(cfg, preds_cfg)
        assert(dominator_tree_correct(tree, cfg, entry))
    elif typ == "frontier":
        frontier = dominance_frontier(cfg, preds_cfg)
        assert(dominance_frontier_correct(frontier, cfg, preds_cfg, entry))
    else:
        dominators = find_dominators(cfg, preds_cfg)
        assert(find_dominators_correct(dominators, cfg, entry))


if __name__ == '__main__':
    prog = json.load(sys.stdin)
    args = sys.argv
    typ = 'dominators'
    if len(args) > 1:
        typ = args[1]
    dom_test(prog, typ)
