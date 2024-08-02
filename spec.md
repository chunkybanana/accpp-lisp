# AccSM spec:
- signed (ish) 32-bit ints
- memory layout: first 64 bytes are registers, then 2^16 bytes ROM, hen 2^16 bytes stack, then unlimited heap (it's all linked lists) (note: can't have fragmented memory due to it all being a single int)

- registers:
- `ip` - instruction pointer, avoid direct manipulation
- `rax`, `rbx`, `rcx`, `drx` - general purpose
- `rsi`, `rdi` - source and destination index
- `rsp`, `rbp` - stack pointer and base pointer
- `r9x`, `r10x`, `r11x`, `r12x`, `r13x`, `r14x`, `r15x` - general purpose
- `NULL` is stored at address 0
Instrs:
- `print addr` - print the value at `addr`




Value formats:
- int: `0x00 [4-byte int]`
- str: `0x01 [string] 0x00`
- list: `0x02 [head pointer] [tail pointer]`



Before: `null`
Append `tobes`: `[-> tobes, null]`



Before: `[-> null, null] null`
Append `tobes`: `[-> [1], null] [-> tobes, null]`, r11: `[-> [1], null]`
Append `2`: `[-> [1], null] [-> 2, null]` r11: `[-> [1], null]`

Before: `[-> null, null] null`
Append `null`: `[-> [1], null] [-> null, null] null`, r11: `[-> [1], null]`



Global dict: linked list of names, linked list of value pointers

Builtins point to register space:
- `c` - `0x01` (prepend_ll)
- `h` - `0x02` (head_ll)
- `t` - `0x03` (tail_ll)
- `s` - `0x04` (subtract)
- `l` - `0x05` (less_than)
- `e` - `0x06` (equal; todo)
- `v` - `0x07` (eval; todo)
- `q` - `0x08` (return first AST; todo)
- `i` - `0x09` (if; todo)
- `d` - `0x0a` (define; todo)
- `_print` - `0x0b` - invisible print, only used top-level by `eval`
- `_id` - `0x0c` magic id function - `(v arg) ()` => `(_id)` `(arg)`
Call stack stores function address, then eval'd args, then uneval'd args
`(s 5 (e (s 4 1) 3))`:

- Push `()`, `(s 5 (e (s 4 1) 3))`
- Evaluate `s` - lookup in global dict, return `->s`, update to `(->s)`, `(5 (e (s 4 1) 3))`
- Evaluate `5` to `5`, update to `(->s 5)`, `((e (s 4 1) 3))`
- Evaluate `(e (s 4 1) 3)`:
- Push `()`, `(e (s 4 1) 3)`
- Evaluate `e` - lookup in global dict, return `->e`, update to `(->e)`, `((s 4 1) 3)`
- Evaluate `s 4 1`:
- Push `()`, `(s 4 1)`
- Evaluate `s` - lookup in global dict, return `->s`, update to `(->s)`, `(4 1)`
- Evaluate `4` to `4`, update to `(->s 4)`, `(1)`
- Evaluate `1` to `1`, update to `(->s 4 1)`, `()`
- Evaluate `->s` (builtin) - result `3`, pop `(->s 4 1), ()`, update previous to `(->e 3)`, `(3)`
- Evaluate `3` to `3`, update to `(->e 3 3)`, `()`
- Evaluate `e` (builtin) - result `1`, pop `(->e 3 3), ()`, update previous to `(->s 5 1)`, `()`
- Evaluate `s` (builtin) - result `4`, pop `(->s 5 1), ()`, return `4`

Note: Once again, we need to append to linked lists - this time I'll just do it with a loop

(note: `f` is a function defined as `(d f (q ((x) (s x 1))))`) evaluating `(f 3)`:

- Push `()`, `(f 3)`
- Evaluate `f` - lookup in global dict, return `((x) (s x 1))`, update to `(((x) (s x 1)))`, `(3)`
- Evaluate `3` to `3`, update to `(((x) (s x 1)) 3)`, `()`
- Replace with `()`, `(s x 1)`)
- Evaluate `(s x 1)`:
- Evaluate `s` - lookup in global dict, return `->s`, update to `(->s)`, `(x 1)`
- Evaluate `x` - lookup in local dict, return `3`, update to `(->s 3)`, `(1)`
- Evaluate `1` to `1`, update to `(->s 3 1)`, `()`
- Evaluate `->s` (builtin) - result `2`, pop `(->s 3 1), ()`, update previous to `(((x) (s x 1)) 2)`, `()`


Push `()`, input

- If there is one eval'd arg (the function):
  - Check if it's a macro:
    - If it's a builtin, check if corresponding function is a macro
    - If it's a user-defined function, check if first item is (), if so replace function with rest of list
  - If so, move uneval'd args to eval'd args

- If uneval'd args is nonempty, evaluate the first one and push it to eval'd args:
  - If it's a number, return it
  - If it's a string, look it up in global/local dicts
  - If it's a list, push `()` and it to the call stack
  
- If uneval'd args is empty, evaluate the function:
  - If it's a builtin, call the corresponding function
  - Push the result to eval'd args of previous call stack item, or to a register if call stack is empty; pop the call stack
  - If it's a user-defined function, push `()` and function body to call stack




TCO: If the last instruction is a non-builtin function call, replace it in the call stack instead of removing it.


todo: 
- [x] eq impl
- [x] def impl
- [x] function calls 
- [x] local dict lookup
- [x?] tco
- [x] eval all top-level exprs
- concurrent write calls
- [x] modify print to only use puts once
- [x] Replace dict load with a single int
- more concurrent write calls


Alloc pattern: for char in `chtslevqid`, starting at `[st]` :
`[st]             [st+9]          [st+18] [st+23]  [st+26]`
`2 [i+1] [st+26*i+26] 2 [st+26*i+23] [st+26*i+35] 0 [w1] [char] 1`

https://tio.run/##xVpLc9s2EL7rV/DiGYIYjAgIpMBz7732Jo9jq5YS@RHbadPp@Le7eAMLLuhHmjYHmQQWwD4/7C5zcXn56dPLyy93326fmkPz5@F42jcHxvvm79U5bcWg6KETO0XFbruhrVLCvEvStXqwp/2u37UTO@h3uRtGTSV7QmjLh86@j50d6SIdFcNWj3EpaTsquZWbaSunvl@Lfnc4Ez2dJmLmlT5CDOOuVaN0J66eNUOc842e3gxCH6XUZkPHSb@LybyLUbjXgY8rKNH5Wi8S/Zn51UwfnHS/sjSuzLH60Yxzttn0QolJ6Z2k0jRtvgE5M6dthJbKjkup3LjdjgvzNkorhlCekd89I35JJKI93Jtpbe0E@90xyO2Oo4wbjtLvd50JZuc1O5CZrr22q1swTDnpFHEU7gyE5poOnkp5Dfktza/lqxfGDLlqoGbs4DQ6vnhPMxomFUHEeg68hFX68C7sPrilmicKBhiU2D7TwTmId7q6goh1cJqPdd4P8FPtj3bKMJpYmCloxiSy1oleTlBwdDBNC8iYjEbsemgAmr9RmSkhUlgPoJPTkma29GITT4NihV70o7PRj9nEef/YBx9NwaBfo@Z8MGCWCMGPufV8PzYLL67Dq6ubE7OI1YfBHxd6V1noebsoz8UQ7VLGFkLC8nGrdaXMolG6GSHTjJDOWU1QcO7A2ABwhx2RhXjyvUyHZxZ/cT8HI3SyOG@3ZFPmx561uR@nCcqV9zAIgDnZepSZnrCdWXIXj6hjDxUbfClKPcrk89HRUpS6bVyU5rEVQqawT4zsMo7WBrwTqvDJE5IO5yzD4iAkzcIYn5sf20FI0/aB80xp/w4hDSXL3KIrJSE@iIMYkR9/jlPLh2VoC65pCc0kd2RwJgJrbNIy1hiOWrergadMuImrApGKRGxxzw6fIwVS6xTLIFGhhvcHg4uu2yy6okr63W0JQ5EnDnUg@ZjwOmZP9ylp4Sn6A63PEJwU9/okt2jvFwERmOr2ZL1N15VKnrCfYWW2SPszEN9mB076aSxThuhVbT6cybq24AAvCY8NKqGtfk7pCMAIT5TtmD8mNCjIhwKQ50DkkB3e0wXIBxf5GG6DIyM2e3zJUpSNALYtbBpSBRXv7z3Lbagsx2a5Nxc4ttsjyas/sPSBORzP1Du@RbtWwGudCOTCBSDNc18@4mBdw1CfcZyJhW1yFCw9apR4IEbV2me9Kq4Lexd0weWx0PSbwGjOzT1bkEfyIVq9yKIAWseyKofrWGIt0lnjHGgO23rowOBZrix7zrJ11S9n62gKnc6nEGWGDJr7EGMgQ/4Zl0hIpoXYUmAJg1tIPmWZXLBc5l/Vu2OGO3UHR@EW3jXlDY5dN0K9ipIF5YBBK1m4@u4hOx70GeflxXQK/g8VGT3PK5KWuaOR7KR3@e3h@LRvZJ80HUhqWba3fjFR1ofU5/vDmNVfWAMjln/56tnlOa8R0XgqdAKugL7EhFNU4g3Udtq1390kHfFYLN0gDRhP6wg@59UUcrwm/jzLLfYMwRWeF1@OEYRqn3obFlwhF3meg@jhcxXU0uHmh9NFEjPKkcaB4@VuVl/WttAc3SWlD1Gao9@B9@wYdXeX52Uh9ee2LXe0Tm/@ErilohjxGXf3kr2b2HtKaWZLacQ16v2NeW8hBUruc1p9yZyn5KWvO/Zrt9Q8r5ubA5RGpRS@QEYmC00UyIRrtYAplIgU8egwyynfaMkNazOe14t65A5i9roqM5lNvQSCVx5tuWBLVw7p0Ll4Pwds32poL9Bfyu0UJPFkek@P/zFzCDdILXOwvU2B7IM0HNiWStDnJCD/gZdRbDqFw/Cq4zwmHU66hyCdQmV7mN23Y//qfYuUgCTr2TkrmG6fTU80lIFGm0W3rjUSgXGLR4QhQ6BimC334/ny@RDaXvWaWA8da/m63YDqidnFVNuEyjVQXNfO6TxDi/sQpw1NuHyerc@wznUEp4cETiPLWdsVNq2gnksP4tcB7ApBCqwOAMUaOqP9FMCKxIeBvtZC1zTDiqJrOgWE@5JfPvgBWvYvTvbUL4o5WEzKUpstx78ih8uSu0kUvYqqzk6IzuIF0YLGAhJmbDnAsHPZe9TJnDqXpCZ4ioYqyCfHN9bu7@fD2qiqkKouymoZgytXLSNWsrcOtnh4A9bltamVbJkLQ6SrsLegJqI4XcuQekQsOq7xFJdXIR9uzs/mqFJ@/4FFYGFPtIoyeoXNkQp66Z2lHqndjilWef0KTYjjbrzwYajI77PqcJ6a1Dp69RI8NKg@luz8980QVOi3dEZCPvF/dEaq6v83WiWLpf6UKn2Eo3p/AW01VPIyAAIFzexzU1cLcPOfI9KWr3RrymY4geiCzDqX9R9c0KiIuxR@W6UCeMctPJ1/NI9/s5cin8/f6zPRR4PvPFbaRP4rzOOs67nYi44h/cMta@LjfrPlvRr4VsqRb7NYzzt2z@kjcAG5xbeCmCa9@/tv@RkB5bwGIzlJ/PxbustriJ7OXKBki5Hd4XMzHMnLCHuP3OdGfWtg8jFE5oS4o5@2oak8VtSCM@60HJ0ZWa43fxVqZf@M4DefXGedy9K/wxe3AW@MhAhVWGMETBo35@8BiAKxQ/jTcIk/v7y0V83F1VXTfm3a9nvzF2nax@a7@en1i/m3WmmS0/62W1miVdO0p@PjU3NxefnthpjXY8PdHzOunzSBJTdPT3aQuJfHhrud3Vo7an/su34gTa/f9QTxh8Iz7Wlmb7tpol2ZQUvJG9FsLNOrdu9H2gvSmGIOvDmxDhcP149OdmKkPjTfvchu5qvdTr/@YYkumyHsIog9x9I@NptGKkPX6zfyDw