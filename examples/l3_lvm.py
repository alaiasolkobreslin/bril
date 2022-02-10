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
        if 'args' in instr and dest in instr['args']:
            return False
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
            # table_list = list representation of table, indexed by LVN
            table_list = []
            # var2num = mapping from variable names to their current value numbers (i.e. rows in table)
            var2num = {}
            # fresh_num = current row number of table
            fresh_num = 0
            # number of the next expression
            num = 0
            for i, instr in enumerate(block):
                if 'op' not in instr:
                    continue
                val = [instr['op']]
                if 'args' in instr:
                    for arg in instr['args']:
                        val.append(var2num[arg])
                elif 'value' in instr:
                    val.append(instr['value'])
                else:
                    continue
                val = tuple(val)
                # print(val)
                if val in table:
                    num, var = table[val]
                    instr['op'] = 'id'
                    instr['args'] = [var]
                    if 'value' in instr:
                        instr.pop('value')
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

                        # Remove old stores in case of clobbering
                        if dest in var2num:
                            _, v1, v2 = table_list[var2num[dest]]
                            table.pop(v1)
                            table.pop(v2)

                        table[val] = num, dest
                        table[('id', num)] = num, dest
                        table_list.append((dest, val, ('id', num)))
                    new_args = []
                    if 'args' in instr:
                        for arg in instr['args']:
                            new_arg, _, _ = table_list[var2num[arg]]
                            new_args.append(new_arg)
                        instr['args'] = new_args
                if 'dest' in instr:
                    var2num[instr['dest']] = num
            new_blocks += block
        func['instrs'] = new_blocks
        new_funcs.append(func)
    prog['functions'] = new_funcs
    print(json.dumps(prog))


if __name__ == '__main__':
    lvm()
