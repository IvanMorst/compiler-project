# MiniCompiler Formal Grammar Specification (Sprint 2)

## Notation
````
- EBNF (Extended Backus-Naur Form)
- `{ ... }` means zero or more repetitions
- `[ ... ]` means optional
- Terminals are token types from Sprint 1 (e.g., `KW_FN`, `IDENTIFIER`, `INT_LITERAL`)
- Non-terminals are in CamelCase
````
## Grammar Rules

### Program Structure
````
Program ::= { Declaration } EOF

Declaration ::= FunctionDecl
| StructDecl
| VarDecl

FunctionDecl ::= KW_FN IDENTIFIER "(" [ Parameters ] ")" [ "->" Type ] Block
StructDecl ::= KW_STRUCT IDENTIFIER "{" { VarDecl } "}"
VarDecl ::= Type IDENTIFIER [ "=" Expression ] ";"

Parameters ::= Parameter { "," Parameter }
Parameter ::= Type IDENTIFIER

Type ::= KW_INT
| KW_FLOAT
| KW_BOOL
| KW_VOID
| IDENTIFIER // struct name

````

### Statements
````
Statement ::= Block
| IfStmt
| WhileStmt
| ForStmt
| ReturnStmt
| ExprStmt
| VarDecl
| ";"

Block ::= "{" { Statement } "}"

IfStmt ::= KW_IF "(" Expression ")" Statement [ KW_ELSE Statement ]

WhileStmt ::= KW_WHILE "(" Expression ")" Statement

ForStmt ::= KW_FOR "(" [ ExprStmt ] ";" [ Expression ] ";" [ Expression ] ")" Statement

ReturnStmt ::= KW_RETURN [ Expression ] ";"

ExprStmt ::= Expression ";"


````
### Expressions (with precedence levels)
````
**Level 1: Primary (highest)**
Primary ::= Literal
| IDENTIFIER
| "(" Expression ")"
| Call

Call ::= IDENTIFIER "(" [ Arguments ] ")"
Arguments ::= Expression { "," Expression }


**Level 2: Unary (right-associative)**
Unary ::= ("-" | "!") Unary
| Primary



**Level 3: Multiplicative (left-associative)**
Multiplicative ::= Unary { ("*" | "/" | "%") Unary }



**Level 4: Additive (left-associative)**
Additive ::= Multiplicative { ("+" | "-") Multiplicative }


**Level 5: Relational (left-associative, non-associative)**
Relational ::= Additive { ("<" | "<=" | ">" | ">=") Additive }



**Level 6: Equality (left-associative, non-associative)**
Equality ::= Relational { ("==" | "!=") Relational }



**Level 7: Logical AND (left-associative)**
LogicalAnd ::= Equality { "&&" Equality }


**Level 8: Logical OR (left-associative)**
LogicalOr ::= LogicalAnd { "||" LogicalAnd }



**Level 9: Assignment (right-associative, lowest)**
Assignment ::= LogicalOr { ("=" | "+=" | "-=" | "*=" | "/=" | "%=") Assignment }



**Expression entry point:**
Expression ::= Assignment

````

### Literals
Literal ::= INT_LITERAL
| FLOAT_LITERAL
| STRING_LITERAL
| KW_TRUE
| KW_FALSE



## Precedence and Associativity Summary

| Level | Operator(s)              | Associativity |
|-------|--------------------------|---------------|
| 1     | `()` (parentheses), function call | n/a |
| 2     | unary `-`, `!`           | right         |
| 3     | `*`, `/`, `%`            | left          |
| 4     | `+`, `-`                 | left          |
| 5     | `<`, `<=`, `>`, `>=`     | non-assoc     |
| 6     | `==`, `!=`               | non-assoc     |
| 7     | `&&`                     | left          |
| 8     | `\|\|`                   | left          |
| 9     | `=`, `+=`, `-=`, `*=`, `/=`, `%=` | right |