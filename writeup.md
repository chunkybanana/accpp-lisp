It's done. I'm tired. This took four weeks.

In _optimised mode_ (using a byte array instead of a massive int, see below) the final testcase took 17 minutes 39 seconds and allocated 58MB of RAM (actually 486MB of RAM). I don't have the patience to run the unoptimised version, but as it has to perform arithmetic on 100-million-digit ints millions of times, I'd be surprised if it finished in under a year. Python already struggles to even _allocate_ one of these values, let alone perform arithmetic on it.

## Acc++

Writing this project purely in *Acc!!* would've been a nightmare, so I created a language called Acc++ that compiles to *Acc!!*. You can find the interpreter/compiler for it, alongside other test files, in [the github repository for this project](). Its main features are comments, a hacked-together macro system using the python `ast` module, and an _optimised mode_ which uses a byte array instead of a massive int, speeding things up by many orders of magnitude.

This program basically treats the accumulator, an arbitrarily large integer that's the only way to store data, as an arbitrarily long array of bytes. By dividing it by the appropriate power of 2 with `_/2^(x*8)%2^32`, I can fairly easily read bytes/32-bit words, and then multiply by said power of 2 again to write them with `_+(v-_/2^(x*8)%2^32)`. I can define macros `readWord`, `writeWord`, `readByte`, `writeByte` to do these. One nice consequence of this is that, as long as these are the only ways I'm interacting with memory, I can add a flag to replace these with custom functions that interact with a byte array, speeding things up a huge amount. I ended up adding a bunch more of these for various purposes.

The program memory is split into three parts: 64 bytes of register space containing 16(ish) 4-bit registers, 800 bytes of stack space and an unbounded heap. While most of the registers are general-purpose, a few have specific purposes:
- `hp` points to just after the end of the heap, and gets increased any time something's allocated.
- `sp` points to the top of the stack during evaluation.
- `sp2`, when in use, points to the top of the "second stack" - an extra stack allocated on top of the heap, used for printing and checking equality.
- `rf` stores the source code during evaluation.
- `gd` contains a pointer to the global dict, formatted as a pair `[names, values]`. This is actually not used in the golfed version, since as it's constant I can just put in the address at compile-time.

I also created a few useful macros. *Acc!!*'s while loop syntax increments a variable starting from `0` and loops while a certain expression is true:

```c
Count i while [expr] {
[code]
}
```

So I can make an if statement with:

```c
Count i while [expr]*0^i {
    [code]
}
```

(0^i is 1 if i is 0 and 0 otherwise. I'll use it a lot). *Acc!!* doesn't allow nested while loops using the same variable, so I've defined `If`, `If2` ... `If10` all with different variables to get around this. I've also defined `While` through `While5` for similar reasons. The other utility macros I've defined are `conc`, which executes a sequence of statements, and `mov`, which is effectively a `writeWord(x, readWord(y))`.

You can find the Acc++ source for this project in [`def.acc`](), although be aware that it's a hacky mess and contains a ton of obsolete code.

## Storage

Since tinylisp is a dynamically-typed language, values need to include their types. I ended up with the following format:

- Integers are stored as a `0x00` byte followed by a signed 32-bit int. The high bit of the int controls whether it's negative, so this supports signed ints between `-2^31` and `2^31-`, which coincedentally is exactly what this challenge requires. Overflowing them will probably break things.
- Strings (names) are stored as an `0x01` byte followed by the byte values of the string and a null terminator. One nice thing about tinylisp is that strings are immutable, and furthermore all strings that'll ever be used at runtime are allocated during parsing.
- All lists are stored as linked lists - an `0x02` byte followed by a 32-bit head (first item) pointer and a 32-bit tail (rest of the list) pointer. There are several advantages to this:
  - Tinylisp inherently uses linked lists - the `h`ead and `t`ail operations correspond to the same parts of a linked list, and the `c`ons operation constructs a list with a given head and tail pointer.
  - Linked lists have to be (in most cases) immutable since one tail pointer can be pointed to by multiple head pointers. This means we never have to value about memory management, which is both a blessing and a curse - There are several places in this program where I allocate linked lists that are later impractical to clean up, and this results in slightly ridiculous memory usage. The tail of the last item of a list is a null pointer (see below) - for example, `(3 5 4)` is stored as `[3, [5, [4, NULL]]]`.
  - While initially I planned to use traditional arrays for this, they're extremely poorly suited to the task due to memory management being a pain.
  One other decision I've made is that all empty lists `()` are referred to by the `NULL` pointer - a pointer to address 0. While this has quite a few advantages, primarily making it easy to check if a value is null, it does result in some weird shenaniganry any time I want to append to a list, which thankfully isn't particularly often.


## Evaluation

Since, as before, we have no access to any sort of recursion, we have to emulate a call stack. Each stack frame is a pair of (pointers to) lists: A list of evaluated arguments, and a list of unevaluated arguments. When evaluating a list (S-expression), the evaluated arguments list starts at `()`, and the unevaluated arguments list starts with the list. One quirk of this is, as the call stack is set up to only evaluate lists, we can't directly evaluate non-list values, but I've found ways around that.

To evaluate a value from the arguments list:
- If it's an integer or `NULL`, it's passed as normal.
- If it's a string, it's looked up, first in the local dictionary (obtained by looking upwards through the call stack until we hit a function), and then in the global dictionary. An undefined variable name will (probably) return null.
- If it's a list, we push `()` and it onto the call stack.

The first item of a list is the function to call, and is always evaluated. After that, we check if it's a macro (`q` or starts with an empty list), and if so push the rest of its arguments to the evaluated stack. While `i` and `d` are also macros, they need some special handling:

- `i` needs to have its first argument, the condition, evaluated regardless, but once that's been evaluated we push the other two arguments to the evaluated stack.
- `d` needs to have its first argument (the name) left unevaluated, so we push that to the evaluated stack unchanged, but it does need the second argument (the value) evaluated, so we leave that alone.

One trick I've used is to have builtins point to addresses in the register space: `c` points to address `1`, `h` to address `2`, etc. This makes it easy to distinguish builtins from regular functions, and also makes it very easy to concisely check what a builtin is.

Also, I mentioned before that I can't directly evaluate non-list values. To get around this, I've defined two builtins that are only accessible by the interpreter itself:
- `print` (address `11`) is used at the top-level to print the result of an expression. It uses a fairly simple algorithm with the second stack to print a value. If given a builtin, it'll attempt to print the value at that index, which is undefined behaviour.
- `id` (address `12`) simply takes one argument and evaluates it. While this sounds useless, it's actually quite powerful: Certain builtins can rearrange the call stack to control what they evaluate, by replacing calls to themselves with a call to `id`. I'll explain this more shortly.

Once a function call has had all its arguments evaluated (/ otherwise dealt with), we check what the first argument, the function, is. If it's a builtin:

- `h`ead, `t`ail, and `c`ons correspond to getting the head/tail of a linked list and constructing a new list respectively, all of which are operations I've already defined.
- `s`ubtract and `l`essthan are also quite simple to implement. However, they share a lot of the same code: They both need to subtract their arguments, then `s` allocates a new int with that value, and `l` allocates a new int with whether that value is negative.
- Since `e`qual has to perform a deep equality check, it uses the "second stack" allocated on top of the heap. For performance reasons and to catch nulls, it first checks if the pointers to two values are equal, meaning that checking two equivalent builtins for equality will actually work. Checking a builtin and any other value (including another builtin) could return 1, return 0, or crash depending on the exact values of certain registers at the time.
- `q` (and `id`) simply return their argument.

If one of the above is called, its return value is pushed to the evaluated args list of the previous stack frame, and the expression itself is popped from the evaluated args list. The remainder of the builtins require special handling:

- `d` needs to _not_ be able to redefine existing values. As dictionary lookup starts from the beginning, prepending the given name and value to the global dictionary would actually succeed, so we instead append them, and then return the given name wrapped in `id`.
- `v` simply replaces itself with a call to `id`.
- `i` checks if its first argument is truthy (not NULL, not the integer 0), and replaces itself with a call to `id` containing either the second or third argument depending on the first. For TCO reasons (see below), if it's itself the result of a call to `id` we squash that call.

Otherwise, the value is a function, and the eval'd stack is structured as `((names body) args)`. We push `body` to the stack wrapped in a call to `id`. When looking up the local dictionary, if `names` is a singleton list, we wrap it and `args` in a list to treat it as a single variable. 

This makes TCO very easy - we can simply check if the item two steps back on the stack is a function call, _and_ the item after that is a call to `id`, then we can simply remove both of those calls.

Then, to evaluate a piece of code, we simply parse it (the [parser]() uses a simple one-pass algorithm) and evaluate+print all its expressions.

## Golfing

It's difficult to portray just how much effort went into golfing this. The original compiled version was around 30KB, and I've spent over two weeks golfing it down to the 9.5KB version here. I'll list some of the tricks I used here.

Before I start, to put some sizes into context:
- Reading the cheapest register, `ra`, is 10 bytes: `_/2^32%2^32`. Some of the other registers are 11 bytes due to having a 3-digit address.
- Writing to `ra` is 22 bytes: `_+(v-_/2^32%2^32)*2^32`. For the same reasons as above, some registers are 24 bytes.
- An if statement has an overhead of 25 bytes: `Count v while (cond)*0^v {\ncode\n}`

Also, because I'm using a macro system, macros that use an argument multiple times will simply have that argument placed multiple times within their code. For example, I have the following macro `head_ll(x)` that gets the head pointer of a linked list:

```c
#defm head_ll(x) 0^0^x * readWord(x+1)
```

However, this specific macro is _null-safe_: The `0^0^x*` at the start ensures that the macro returns `0` when given `0` (which isn't guaranteed otherwise), but this comes at the cost of having to use `x` twice. If an already large expression is passed to `head_ll`, it'll double in length, and stacking `head_ll` multiple times blows up the size exponentially. There are two ways around this - one way is to, where possible, use the following _unsafe_ version that only uses `x` once:

```c
#defm u_head_ll(x) readWord(x+1)
```

The other way is to extract expensive expressions into registers:

```c
writeWord(ra, [expensive expression])
head_ll(rax)
```

One important thing is that we're not limited to just 32-bit read/writes. By simply replacing `32` with `64` in read/write calls, I can read/write two words at once for almost the same byte count. When reading/writing to consecutive addresses, this both saves a ton of bytes and improves performance (since the overhead of interacting with a massive int is so large). For example, as the registers `ra` and `rb` are consecutive in memory, I can replace `writeWord(ra, 5) ; writeWord(rb, 6)` with `write_dword(ra, 5, 6)` and save a ton of bytes in the compiled result.

Perhaps unsurprisingly, though, the largest golfs came from logic optimisations. For example, I need to search through both the local and global dictionaries when looking up a variable name. Originally, this required two separate but almost-identical pieces of code to search through the dictionaries, but by looping twice, searching through the local dictionary on the first iteration and the global dictionary on the second iteration, I can remove almost half the code.

Another of these "logic optimisation"s is initialising the global dictionary. It's stored as 

4^x
**Parallel writes**

All calls involving writing memory amount to `_+[x]`. If I have multiple write calls in a row that don't rely on each other `_+[x], _+[y], _+[z]` I can merge them into `_+[x]+[y]+[z]`, saving two bytes per use. This doesn't sound like much, but it has another advantage.

As I mentioned before, an if statement has an overhead of 25 bytes. If I have a paralellised write call `_+[x]+[y]+[z]` wrapped in a conditional, I can remove the if statement entirely and replace it with `_+([x]+[y]+[z])*[cond]`. This saves 22 bytes - 20 if `cond` needs to be in brackets, and 16 if `cond` needs to be converted to `1` or `0`.