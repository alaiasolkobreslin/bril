import json
import sys

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


def get_vars(instrs):
    vars = set()
    for instr in instrs:
        if 'dest' in instr:
            vars.add(instr['dest'])
    return vars


def fresh_var(vars, n):
    var = 'v' + str(n)
    while var in vars:
        n += 1
        var = 'v' + str(n)
    n += 1
    return var, n


def dest_overwritten(instrs, i):
    dest = instrs[i]['dest']
    for instr in instrs[i+1:]:
        if 'dest' in instr and instr['dest'] == dest:
            return True
    return False


def lvm():
    prog = json.load(sys.stdin)
    new_funcs = []
    for func in prog['functions']:
        blocks = form_blocks(func['instrs'])
        new_blocks = []
        for block in blocks:
            # Get all variables
            all_vars = get_vars(block)
            # Next value of fresh variable
            fresh_var_n = 0

            # table = mapping from value tuples to canonical variables, with each row numbered
            table = {}

            # var2num = mapping from variable names to their current value numbers (i.e. rows in table)
            var2num = {}
            # fresh_num = current row number of table
            fresh_num = 0
            num = 0
            for i, instr in enumerate(block):
                if 'op' not in instr:
                    continue
                val = [instr['op']]
                if 'args' in instr:
                    for arg in instr['args']:
                        val.append(var2num[arg])
                else:
                    val.append(instr['value'])

                val = tuple(val)
                if val in table:
                    num, var = table[val]
                    instr['op'] = 'id'
                    instr['args'] = [var]
                else:
                    # Newly computed value
                    num = fresh_num
                    fresh_num += 1

                    if 'dest' in instr:
                        if dest_overwritten(block, i):
                            dest, fresh_var_n = fresh_var(
                                all_vars, fresh_var_n)
                            instr['dest'] = dest
                        else:
                            dest = instr['dest']

                        table[val] = num, dest
                    new_args = []
                    if 'args' in instr:
                        print(var2num)
                        print(table)
                        print('args:')
                        for arg in instr['args']:
                            # print(instr['op'])
                            print(arg)
                            _, new_arg = table[(instr['op'], var2num[arg])]
                            new_args.append(new_arg)
                        instr['args'] = new_args
                    else:
                        _, new_value = table[(instr['op'], instr['value'])]
                        instr['value'] = new_value

                var2num[instr['dest']] = num

            new_blocks += block
        func['instrs'] = new_blocks
        new_funcs.append(func)
    prog['functions'] = new_funcs
    print(json.dumps(prog))


if __name__ == '__main__':
    lvm()
