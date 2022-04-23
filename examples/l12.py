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


def speculate(prog):
    fresh = get_fresh_label(prog)
    for func in prog['functions']:
        if func['name'] == 'main':
            instrs = func['instrs']

            new_instrs = [{'op': 'speculate'}]
            for line in sys.stdin:
                if line[0] == '{':
                    instr = json.loads(line)
                    if 'op' in instr and instr['op'] == 'guard':
                        instr['labels'] = [fresh]
                    new_instrs.append(instr)

            new_instrs.append({'label': fresh})
            func['instrs'] = new_instrs + instrs
    print(json.dumps(prog))

    # idea:
    # 1. Read the entire trace
    # 2. Inject the trace right after the declaration of main
    # 3. Create a new label to represent the "actual" main
    # 4. Adjust the guard to reflect this actual label
    # 5. Add Speculate, commit, and guard instructions


if __name__ == '__main__':
    # file = open(sys.argv[0])
    file = open("../benchmarks/collatz.json")
    prog = json.load(file)
    speculate(prog)
