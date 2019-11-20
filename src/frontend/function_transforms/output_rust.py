

import sys

try:
    import gelpia_logging as logging
    import color_printing as color
except ModuleNotFoundError:
    sys.path.append("../")
    import gelpia_logging as logging
    import color_printing as color

from expression_walker import walk
from pass_utils import INFIX, BINOPS, UNOPS

logger = logging.make_module_logger(color.cyan("output_rust"),
                                    logging.HIGH)




def output_rust(exp, inputs, consts, assigns):
    DIFF_DECL = ["extern crate gr;\n"
                 "use gr::*;\n"
                 "\n"
                 "#[allow(unused_parens)]\n"
                 "#[no_mangle]\n"
                 "pub extern \"C\"\n"
                 "fn gelpia_func(_x: &Vec<GI>, _c: &Vec<GI>) -> (GI, Option<Vec<GI>>) {\n"]
    DECL = ["extern crate gr;\n"
            "use gr::*;\n"
            "\n"
            "#[no_mangle]\n"
            "pub extern \"C\"\n"
            "fn gelpia_func(_x: &Vec<GI>, _c: &Vec<GI>) -> (GI) {\n"]
    START = DECL
    input_mapping = {name:str(i) for name,i in zip(inputs, range(len(inputs)))}
    const_mapping = {name:str(i) for name,i in zip(consts, range(len(consts)))}
    seen_assigns = set()
    body = list()


    def _e_variable(work_stack, count, exp):
        #logger("expand_variable: {}", exp)
        assert(exp[0] == "Variable")
        assert(len(exp) == 2)
        assert(exp[1] in assigns)
        if exp[1] in seen_assigns:
            work_stack.append((True, count, [exp[1]]))
            return
        seen_assigns.add(exp[1])
        work_stack.append((True,  count, exp[0]))
        work_stack.append((True,  2,     exp[1]))
        work_stack.append((False, 2,     assigns[exp[1]]))

    def _input(work_stack, count, exp):
        #logger("expand_input: {}", exp)
        assert(exp[0] == "Input")
        assert(len(exp) == 2)
        index = input_mapping[exp[1]]
        work_stack.append((True, count, ["_x[", index, "]"]))

    def _const(work_stack, count, exp):
        #logger("expand_const: {}", exp)
        assert(exp[0] == "Const")
        assert(len(exp) == 2)
        index = const_mapping[exp[1]]
        work_stack.append((True, count, ["_c[", index, "]"]))

    my_expand_dict = {"Input"    : _input,
                      "Const"    : _const,
                      "Variable" : _e_variable}

    def _c_variable(work_stack, count, args):
        nonlocal body
        #logger("variable: {}", args)
        assert(args[0] == "Variable")
        assert(len(args) == 3)
        name = args[1]
        value = args[2]
        body += ["    let ", name, " = "] + value + [";\n"]
        work_stack.append((True, count, [name]))

    def _infix(work_stack, count, args):
        #logger("infix: {}", args)
        assert(args[0] in INFIX)
        assert(len(args) == 3)
        op = args[0]
        l = args[1]
        r = args[2]
        work_stack.append((True, count, l + [" ", op, " "] + r))

    def _binop(work_stack, count, args):
        #logger("binop: {}", args)
        assert(args[0] in BINOPS or args[0] == "powi")
        assert(len(args) == 3)
        op = args[0]
        first = args[1]
        secon = args[2]
        work_stack.append((True, count, [op, "("] + first + [", "] + secon + [")"]))

    def _pow(work_stack, count, args):
        #logger("pow: {}", args)
        assert(args[0] == "pow")
        assert(len(args) == 3)
        base = args[1]
        expo = args[2]
        assert(expo[0] == "Integer")
        work_stack.append((True, count, ["pow("] + base + [", ", expo[1] + ")"]))

    def _unop(work_stack, count, args):
        #logger("unop: {}", args)
        assert(args[0] in UNOPS)
        assert(len(args) == 2)
        op = args[0]
        arg = args[1]
        work_stack.append((True, count, [op, "("] + arg + [")"]))

    def _box(work_stack, count, args):
        #logger("box: {}", args)
        assert(args[0] == "Box")
        if len(args) == 1:
            work_stack.append((True, count, ["None"]))
            return
        box = ["Some(vec!["]
        for sub in args[1:]:
            box += sub + [", "]
        box = box[0:-1] + ["])"]
        work_stack.append((True, count, box))

    def _tuple(work_stack, count, args):
        nonlocal START
        #logger("tuple: {}", args)
        assert(args[0] == "Tuple")
        assert(len(args) == 3)
        START = DIFF_DECL
        work_stack.append((True, count, ["("] + args[1] + [", "] + args[2] + [")"]))

    def _return(work_stack, count, args):
        #logger("Return: {}", args)
        assert(args[0] == "Return")
        assert(len(args) == 2)
        return ["    "] + args[1]

    my_contract_dict = dict()
    my_contract_dict.update(zip(BINOPS,
                                [_binop for _ in BINOPS]))
    my_contract_dict.update(zip(UNOPS,
                                [_unop for _ in UNOPS]))
    my_contract_dict.update(zip(INFIX,
                                [_infix for _ in INFIX]))
    my_contract_dict["pow"] = _pow
    my_contract_dict["Variable"] = _c_variable
    my_contract_dict["Box"] = _box
    my_contract_dict["Tuple"] = _tuple
    my_contract_dict["Return"] = _return

    retval = walk(my_expand_dict, my_contract_dict, exp, assigns)

    return "".join(START + body + retval + ["\n}"])




def main(argv):
    logging.set_log_filename(None)
    logging.set_log_level(logging.HIGH)
    try:
        from function_to_lexed import function_to_lexed
        from lexed_to_parsed import lexed_to_parsed
        from pass_lift_inputs_and_inline_assigns import lift_inputs_and_inline_assigns
        from pass_utils import get_runmain_input
        from pass_simplify import simplify
        from pass_reverse_diff import reverse_diff
        from pass_lift_consts import lift_consts
        from pass_single_assignment import single_assignment

        data = get_runmain_input(argv)
        logging.set_log_level(logging.NONE)

        tokens = function_to_lexed(data)
        tree = lexed_to_parsed(tokens)
        exp, inputs = lift_inputs_and_inline_assigns(tree)
        exp = simplify(exp, inputs)
        d, diff_exp = reverse_diff(exp, inputs)
        diff_exp = simplify(diff_exp, inputs)
        c, diff_exp, consts = lift_consts(diff_exp, inputs)
        diff_exp, assigns = single_assignment(diff_exp, inputs)

        logging.set_log_level(logging.HIGH)
        logger("raw: \n{}\n", data)
        logger("inputs:")
        for name, interval in inputs.items():
            logger("  {} = {}", name, interval)
        logger("consts:")
        for name, val in consts.items():
            logger("  {} = {}", name, val)
        logger("assigns:")
        for name, val in assigns.items():
            logger("  {} = {}", name, val)
        logger("expression:")
        logger("  {}", diff_exp)

        rust_function = output_rust(diff_exp, inputs, consts, assigns)

        logger("rust_function: \n{}", rust_function)

        return 0

    except KeyboardInterrupt:
        logger(color.green("Goodbye"))
        return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
