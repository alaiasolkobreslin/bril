import json
import sys


def speculate():
    # for func in prog['functions']:
    #     if func['name'] == 'main':
    #         instrs = func['instrs']

    #         new_instrs = [{'op': 'speculate'}]
    #         for line in sys.stdin:
    #             if line[0] == '{':
    #                 instr = json.loads(line)
    #                 new_instrs.push(instr)
    #                 print(instr)
    #         new_instrs.push({'op': 'commit'})

    #         func['instrs'] = new_instrs + instrs
    # print(json.dumps(prog))

    new_instrs = [{'op': 'speculate'}]
    for line in sys.stdin:
        if line[0] == '{':
            instr = json.loads(line)
            new_instrs.append(instr)
    new_instrs.append({'op': 'commit'})

    print(new_instrs)

    # idea:
    # 1. Read the entire trace
    # 2. Inject the trace right after the declaration of main
    # 3. Create a new label to represent the "actual" main
    # 4. Adjust the guard to reflect this actual label
    # 5. Add Speculate, commit, and guard instructions


if __name__ == '__main__':
    # file = open(sys.argv[0])
    # prog = json.load(file)
    # speculate(prog)

    speculate()
