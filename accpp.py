#!/usr/bin/python3

import re
import sys
import ast
from gmpy2 import mpz

USE_MPZ = False

def main(codeFile=None):
    if len(sys.argv) > 1:
        codeFile = sys.argv[1]
    elif codeFile is None:
        codeFile = input("Please supply a filename: ")
    try:
        with open(codeFile) as f:
            code = f.readlines()
        #print(code)
        #print(translate(accpp(code)))
        #return
        if len(sys.argv) > 2 and sys.argv[2] == '-c':
            print(end='\n'.join(compress(accpp(code)))[:-4])
            return
        if OPT_READWRITE:
            code = translate_opt(accpp(code))
            exec(opt_readwrite_code + code + opt_readwrite_end, {"a": [], "inputStream": inputStream(), "mpz": mpz,"debug":print,"deval":eval})
        else:
            code = translate(accpp(code))
            exec(code, {"inputStream": inputStream(), "mpz": mpz})
    except:
        print("Acc!!\n", file=sys.stderr)
        raise

def inputStream():
    buffer = ""
    while True:
        if buffer == "":
            try:
                buffer = input() + "\n"
            except EOFError:
                buffer = None
        if buffer is None:
            yield 0
        else:
            yield ord(buffer[0])
            buffer = buffer[1:]

OPT_READWRITE = False

# note: a is a byte array

opt_readwrite_code = """
_=0 # compat

def readByte(x, _=0):
    if x >= len(a): return 0
    return a[x]

def writeByte(x, y, _=0):
    if x >= len(a):
        a.extend([0] * (x - len(a) + 1))
    a[x] = y % 256


def readWord(x, _=0):
    return readByte(x) + readByte(x+1) * 256 + readByte(x+2) * 65536 + readByte(x+3) * 16777216

def writeWord(x, y, _=0):
    writeByte(x, y % 256)
    writeByte(x+1, (y // 256) % 256)
    writeByte(x+2, (y // 65536) % 256)
    writeByte(x+3, (y // 16777216) % 256)

def addv(x, y, _=0):
    writeWord(x, readWord(x) + y)

def write_null(x, _=0):
    writeWord(x, 0)

def write_dnull(x, _=0):
    writeWord(x, 0)
    writeWord(x+4, 0)

def write_qnull(x, _=0):
    writeWord(x, 0)
    writeWord(x+4, 0)
    writeWord(x+8, 0)
    writeWord(x+12, 0)

def write_dword(x, y, z, _=0):
    writeWord(x, y)
    writeWord(x+4, z)

def write_qword(x, y, z, w, v, _=0):
    writeWord(x, y)
    writeWord(x+4, z)
    writeWord(x+8, w)
    writeWord(x+12, v)

def alloc_ll_helper(x, p, _=0):
    writeByte(p, 2);
    writeWord(p+1, x);
    writeWord(p+5, 0);

def alloc_int_helper(x, p, _=0):
    writeByte(p, 0);
    writeWord(p+1, x);

def read_dword(x, _=0):
    return readWord(x) + readWord(x+4) * 2 ** 32

def write_dword_full(x, v, _=0):
    writeWord(x, v % 2 ** 32)
    writeWord(x+4, v // 2 ** 32)

def read_qword(x, _=0):
    return readWord(x) + readWord(x+4) * 2 ** 32 + readWord(x+8) * 2 ** 64 + readWord(x+12) * 2 ** 96

def write_qword_full(x, v, _=0):
    writeWord(x, v % 2 ** 32)
    writeWord(x+4, (v // 2 ** 32) % 2 ** 32)
    writeWord(x+8, (v // 2 ** 64) % 2 ** 32)
    writeWord(x+12, (v // 2 ** 96) % 2 ** 32)

def write_6word_full(x, v, _=0):
    writeWord(x, v % 2 ** 32)
    writeWord(x+4, (v // 2 ** 32) % 2 ** 32)
    writeWord(x+8, (v // 2 ** 64) % 2 ** 32)
    writeWord(x+12, (v // 2 ** 96) % 2 ** 32)
    writeWord(x+16, (v // 2 ** 128) % 2 ** 32)
    writeWord(x+20, (v // 2 ** 160) % 2 ** 32)

def dual_alloc_ll_helper(x, y, p, _=0):
    writeByte(p, 2);
    writeWord(p+1, x);
    writeWord(p+5, 0);
    writeByte(p+9, 2);
    writeWord(p+10, y);
    writeWord(p+14, 0);

def prepend_ll_helper(x, p, _=0):
    writeByte(p, 2);
    writeWord(p+1, x % 2 ** 32);
    writeWord(p+5, x // 2 ** 32);

def cond_write_null(x, y, _=0):
    writeWord(x, (1 - y) * readWord(x))

def addv2(x, y, z, _=0):
    addv(x, y)
    addv(x + 4, z)

def read_to_end(x, _=0):
    acc = 0
    for k in a[-1:x-1:-1]:
        acc = acc * 256 + k
    return acc

def read_n_bytes(x, n, _=0):
    acc = 0
    for k in a[x+n-1:x-1:-1]:
        acc = acc * 256 + k
    return acc
"""

opt_readwrite_end = """
import sys
debug('memory allocated:', len(a), 'bytes', 'actually', sys.getsizeof(a), 'bytes')
"""




def accpp(code):
    code = [q.strip(' ') + "\n" for q in re.sub("\\\\s*(#.*?)?\n","","".join(code)).split("\n")]
    code = re.sub(r"\/\*(.|\n)*?\*\/","","\n".join(code)).split("\n")
    #print('\n'.join(code))
    defs = []
    macros = []
    mlmacros = []

    def handle_opt(line):
        if line.startswith("IFOPT "):
            return [line[6:]] if OPT_READWRITE else []
        elif line.startswith("IFNOPT "):
            return [] if OPT_READWRITE else [line[7:]]
        else:
            return [line]

    code = [line for l in code for line in handle_opt(l)]

    for line in code:
        line = line.replace("^","**")
        if r := re.match(r"#def (\D\w*) (.+)", line):
            defs.append(r.groups())
        elif r := re.match(r"#def (\D\w*)\(((?:\D\w*,)*(?:\s*\D\w*)?)\) (.+)", line):
            macros.append(r.groups())
        elif r := re.match(r"#defm (\D\w*)\(((?:\D\w*,)*(?:\s*\D\w*)?)\) (.+)", line):
            mlmacros.append(r.groups())

    #print(macros)

    def handle_macros(line):
    #print('parsing line',line )
        fmt = "%s"
        if r := re.match(".ascii (.+)", line): # custom macro
            res = ['alloc_str()'] + [f"append_str({ord(c)})" for c in r.groups()[0]]
            return [t for b in res for t in handle_macros(b)]
        if "#" in line or line == "\n" or not line or line == "}": 
            return [line]
        if r := re.match(r"Count ([a-z]) while (.+) \{", line):
            n, s = r.groups()
            fmt = f"Count " + n +" while %s {"
            line = s
        elif r := re.match(r"Write (.+)", line):
            s = r.groups()[0]
            fmt = f"Write %s"
            line = s
        line = line.replace("^","**")
        
        line = ast.parse(line).body[0].value

        if isinstance(line, ast.Call):
            for name, args, body in mlmacros:
                if line.func.id == name:
                    if len(args) == 0: args = []
                    else: args = [a.strip() for a in args.split(",")]
                    if len(line.args) != len(args): continue
                    #print(line, ast.dump(line))
                    if fmt !=  "%s":
                        raise SyntaxError("macro %s is not allowed in this context" % name)
                    for arg, formal in zip(line.args, args):
                        body = re.sub(r"\b" + formal + r"\b", ast.unparse(arg), body)
                    body = [x.strip() for x in body.split(';')]
                    #print('body',body)
                    return [t for b in body for t in handle_macros(b)]
            if not any(line.func.id == name for name, args, body in macros):
                raise SyntaxError("Could not overload macro %s with %d arguments" % (line.func.id, len(line.args)))

        # Recursively replace all defined expressions in the AST expression
        def _recursive_replace(expr):
            #print("expr",expr, ast.dump(expr))
            if isinstance(expr, ast.Call): # macro
                if OPT_READWRITE and expr.func.id in ["readByte", "writeByte", "readWord", "writeWord", "addv","debug","deval","write_null","write_dnull","write_qnull","write_dword","write_qword","alloc_ll_helper","alloc_int_helper", "read_dword","write_dword_full","read_qword","write_qword_full","write_6word_full","dual_alloc_ll_helper","prepend_ll_helper","cond_write_null","addv2","read_to_end","read_n_bytes"]:
                    expr.args = [_recursive_replace(arg) for arg in expr.args]
                    return expr
                        
                for name, args, body in macros:
                    args = [a.strip() for a in args.split(",")]
                    if expr.func.id == name and len(args) == len(expr.args):
                        for arg, formal in zip(expr.args, args):
                            body = re.sub(r"\b" + formal + r"\b", "(" + ast.unparse(arg) + ")", body)
                        #print(body)
                        return _recursive_replace(ast.parse(body).body[0].value)
                raise SyntaxError("Could not overload macro %s with %d arguments" % (expr.func.id, len(expr.args)))
                                                
                if all(name != expr.func.id for name, args, body in mlmacros):
                    raise SyntaxError("unknown macro %s" % expr.func.id)
            elif isinstance(expr, ast.BinOp):
                expr.left = _recursive_replace(expr.left)
                expr.right = _recursive_replace(expr.right)
                return expr
            elif isinstance(expr, ast.UnaryOp):
                expr.operand = _recursive_replace(expr.operand)
                return expr
            elif isinstance(expr, ast.Name):

                for name, body in defs:
                    if expr.id == name:
                        return ast.parse(body).body[0].value
                return expr
            else:
                return expr

        #print('ruirhfie', ast.unparse(line), ast.unparse(_recursive_replace(line)))

        while ast.unparse(line) != ast.unparse((line := _recursive_replace(line))): pass
        #print(ast.unparse(line))

        return [fmt % ast.unparse(line)]

    return [line for l in code for line in handle_macros(l)]

# compresses preprocessed code
def compress(code):
    out = []
    for line in code:
        if line == "" or line[0] == "#" or line == "\n":
            continue
        fmt = "%s"
        if r := re.match(r"Count ([a-z]) while (.+) \{", line):
            n, s = r.groups()
            fmt = f"Count " + n +" while %s {"
            line = s
        elif r := re.match(r"Write (.+)", line):
            s = r.groups()[0]
            fmt = f"Write %s"
            line = s
        line = line.replace("**","^")
        line = line.replace(" ","")
        line = re.sub(r"\(\d+\*\d+\)", lambda x: str(eval(x.group())), line)
        line = line.replace("+-","-")
        line = re.sub(r"\b1\*2\^(\d+)",lambda x: f"2^{x.group(1)}",line)
        line = re.sub(r"\b2\*2\^(\d+)",lambda x: f"2^{int(x.group(1))+1}",line)
        line = re.sub(r"\b4\*2\^(\d+)",lambda x: f"2^{int(x.group(1))+2}",line)
        line = re.sub(r"\b8\*2\^(\d+)",lambda x: f"2^{int(x.group(1))+3}",line)
        line = re.sub(r"\b16\*2\^(\d+)",lambda x: f"2^{int(x.group(1))+4}",line)
        line = re.sub(r"\b2\^128\b","4^64",line)
        line = re.sub(r"\b2\^160\b","4^80",line)
        line = re.sub(r"\b2\^192\b","4^96",line)
        line = re.sub(r"\b2\^288\b","8^96",line)
        line = re.sub(r"\b18\*2\^352\b","9*2^353",line)
        line = re.sub(r"\b2\^258\b","8^86",line)
        line = re.sub(r"\b2\^144\b","4^72",line)
        #line = re.sub(r"\((\d+)\)", r"\1", line)
        out += [fmt % line]
    return out



def translate(accCode):
    indent = 0
    loopVars = []
    pyCode = ["_ = 0"]

    for lineNum, line in enumerate(accCode):
        if "#" in line:
            # Strip comments
            line = line[:line.index("#")]
        line = line.strip()
        if not line:
            continue
        lineNum += 1
        if line == "}":
            if indent:
                loopVar = loopVars.pop()
                pyCode.append(" "*indent + loopVar + " += 1")
                indent -= 1
                pyCode.append(" "*indent + "del " + loopVar)
            else:
                raise SyntaxError("Line %d: unmatched }" % lineNum)
        else:
            m = re.fullmatch(r"Count ([a-z]) while (.+) \{", line)
            if m:
                expression = validateExpression(m.group(2))
                if expression:
                    loopVar = m.group(1)
                    pyCode.append(" "*indent + loopVar + " = 0")
                    pyCode.append(" "*indent + "while " + expression + ":")
                    indent += 1
                    loopVars.append(loopVar)
                else:
                    raise SyntaxError("Line %d: invalid expression " % lineNum
                                      + m.group(2))
            else:
                m = re.fullmatch(r"Write (.+)", line)
                if m:
                    expression = validateExpression(m.group(1))
                    if expression:
                        pyCode.append(" "*indent
                                      + "print(chr(%s), end='')" % expression)
                    else:
                        raise SyntaxError("Line %d: invalid expression "
                                          % lineNum
                                          + m.group(1))
                else:
                    expression = validateExpression(line)
                    if expression:
                        pyCode.append(" "*indent + "_ = " + expression)
                    else:
                        raise SyntaxError("Line %d: invalid statement "
                                          % lineNum
                                          + line)
    if (USE_MPZ): pyCode = [re.sub(r"(\d+)", r"mpz(\1)", line) for line in pyCode]
    #print("\n".join('%d %s'%(e,l) for e,l in enumerate(pyCode)))
    return "\n".join(pyCode)

def translate_opt(accCode):
    indent = 0
    loopVars = []
    pyCode = ["a = []"]

    for lineNum, line in enumerate(accCode):
        if "#" in line:
            # Strip comments
            line = line[:line.index("#")]
        line = line.strip()
        if not line:
            continue
        lineNum += 1
        if line == "}":
            if indent:
                loopVar = loopVars.pop()
                pyCode.append(" "*indent + loopVar + " += 1")
                indent -= 1
                pyCode.append(" "*indent + "del " + loopVar)
            else:
                raise SyntaxError("Line %d: unmatched }" % lineNum)
        else:
            m = re.fullmatch(r"Count ([a-z]) while (.+) \{", line)
            if m:
                expression = tlx(m.group(2))
                if expression:
                    loopVar = m.group(1)
                    pyCode.append(" "*indent + loopVar + " = 0")
                    pyCode.append(" "*indent + "while " + expression + ":")
                    indent += 1
                    loopVars.append(loopVar)
                else:
                    raise SyntaxError("Line %d: invalid expression " % lineNum
                                      + m.group(2))
            else:
                m = re.fullmatch(r"Write (.+)", line)
                if m:
                    expression = tlx(m.group(1))
                    if expression:
                        pyCode.append(" "*indent
                                      + "print(chr(%s), end='')" % expression)
                    else:
                        raise SyntaxError("Line %d: invalid expression "
                                          % lineNum
                                          + m.group(1))
                else:
                    expression = tlx(line)
                    if expression:
                        pyCode.append(" "*indent + expression)
                    else:
                        raise SyntaxError("Line %d: invalid statement "
                                          % lineNum
                                          + line)
    if (USE_MPZ): pyCode = [re.sub(r"(\d+)", r"mpz(\1)", line) for line in pyCode]
    
    #print("\n".join('%d %s'%(e,l) for e,l in enumerate(pyCode)))
    return "\n".join(pyCode)

def tlx(expr):
    expr = expr.replace("^", "**")
    expr = expr.replace("/", "//")
    # Replace N with a call to get the next input character
    expr = expr.replace("N", "next(inputStream)")
    return expr

def validateExpression(expr):
    "Translates expr to Python expression or returns None if invalid."
    expr = expr.strip()
    if re.search(r"[^ 0-9a-z_N()*/%^+-]", expr):
        # Expression contains invalid characters
        return None
    elif re.search(r"[a-zN_]\w+", expr):
        # Expression contains multiple letters or underscores in a row
        return None
    else:
        # Not going to check validity of all identifiers or nesting of parens--
        # let the Python code throw an error if problems arise there
        # Replace short operators with their Python versions
        expr = expr.replace("^", "**")
        expr = expr.replace("/", "//")
        # Replace N with a call to get the next input character
        expr = expr.replace("N", "next(inputStream)")
        return expr

if __name__ == "__main__":
    main()