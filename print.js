list = {
    h: { h: 5, t: { h: 7, t: null } },
    t: { h: { h: 3, t: null }, t: { h: 2, t: null } }//{h:null,t:{h: {h: null,t: {h: null,t:null}}, t: null}}
}

NULL = null

pl = l => {
    let o = '', stack = []
    stack.push(l);
    if (typeof l !== 'number') o += '('
    while (stack.length) {
        let n = stack.at(-1);
        if (typeof n == "number" || n == NULL) {
            o += n ?? ')';
            stack.pop();
            if (stack.at(-1) !== NULL && stack.length) o += ' ';
        } else {
            stack.push(stack.pop().t)
            stack.push(n.h)
            if (typeof n.h !== 'number') o += '('
        }
    }
    return o;
}

pl(list)

'"'.charCodeAt()

str = `(q ((1 2)(3 4)))`

parse = s => {
    s = [...s];
    let isnum = true, stack = [[]], ctoken = '';
    while (s.length) {
        let char = s.shift();
        if ('() \n'.includes(char)) {
            if (ctoken) {
                stack.at(-1).push(isnum ? +ctoken : ctoken)
                ctoken = '', isnum = true;
            }
        } else {
            ctoken += char
            isnum &&= '0123456789'.includes(ctoken)
        }

        if (char == '(') {
            let n = [];
            stack.at(-1).push(n);
            stack.push(n);
        } else if (char == ')') {
            stack.pop();
        }
    }
    return stack[0]
}

JSON.stringify(parse(str))