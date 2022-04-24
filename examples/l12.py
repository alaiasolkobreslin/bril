import json
import sys


def get_labels(prog):
    labels = []
    for func in prog['functions']:
        for instr in func['instrs']:
            if 'label' in instr:
                labels.append(instr['label'])
    return labels


def get_fresh_label(prog):
    labels = get_labels(prog)
    fresh = 'fresh'
    count = 0
    while fresh in labels:
        fresh = 'fresh' + str(count)
        count += 1
    return fresh


def get_vars(prog):
    vars = set()
    for func in prog['functions']:
        for instr in func['instrs']:
            if 'dest' in instr:
                vars.add(instr['dest'])
    return vars


def get_fresh_var(prog):
    vars = get_vars(prog)
    fresh = "freshVar"
    count = 0
    while fresh in vars:
        fresh = 'freshVar' + str(count)
        count += 1
    return fresh


def speculate(prog):
    fresh_label = get_fresh_label(prog)
    fresh_var = get_fresh_var(prog)
    for func in prog['functions']:
        if func['name'] == 'main':
            instrs = func['instrs']

            new_instrs = [{'op': 'speculate'}]
            for line in sys.stdin:
                if line[0] == '{':
                    instr = json.loads(line)
                    if 'op' in instr and instr['op'] == 'guard':
                        instr['labels'] = [fresh_label]
                    new_instrs.append(instr)

            new_instrs.append({'label': fresh_label})
            func['instrs'] = new_instrs + instrs
    print(json.dumps(prog))


if __name__ == '__main__':
    file = open(sys.argv[1])
    prog = json.load(file)
    speculate(prog)
