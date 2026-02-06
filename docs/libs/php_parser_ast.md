# PHP-Parser AST Structure

**Source**: Verified against `nikic/PHP-Parser` 4.x source code.

> [!IMPORTANT]
> **Data Types Definition**
> - **Subnodes (Node Children)**: Objects (instances of `Node`) or arrays of Objects. These represent the tree structure (Edges).
> - **Properties (Scalars)**: Primitive values (`int`, `string`, `bool`, `null`, `float`) or arrays of primitives. These represent data attributes.

## Core Node Structure

All nodes implement `PhpParser\Node`.
- **Attributes**: `startLine`, `endLine`, `startFilePos`, `endFilePos`, `startTokenPos`, `endTokenPos`, `comments`.

## Project and File (php-parser-py specific)

| Type | Subnodes (children) | Properties (scalars) |
|------|---------------------|----------------------|
| `Project` | `files[]` | `path` (absolute), `label` |
| `File` | `stmts[]` | `path` (relative), `filePath` (absolute), `label` |

## AST Nodes Reference

### Statements (Stmt_*)

| Type | Subnodes (children) | Properties (scalars) |
|------|---------------------|----------------------|
| `Stmt_Break` | `num` | - |
| `Stmt_Case` | `cond`, `stmts` | - |
| `Stmt_Catch` | `stmts`, `types`, `var` | - |
| `Stmt_Class` | `attrGroups`, `extends`, `implements`, `name`, `stmts` | `flags` |
| `Stmt_ClassConst` | `attrGroups`, `consts`, `type` | `flags` |
| `Stmt_ClassMethod` | `attrGroups`, `name`, `params`, `returnType`, `stmts` | `byRef`, `flags` |
| `Stmt_Const` | `consts` | - |
| `Stmt_Continue` | `num` | - |
| `Stmt_Declare` | `declares`, `stmts` | - |
| `Stmt_DeclareDeclare` | `key`, `value` | - |
| `Stmt_Do` | `cond`, `stmts` | - |
| `Stmt_Echo` | `exprs` | - |
| `Stmt_Else` | `stmts` | - |
| `Stmt_ElseIf` | `cond`, `stmts` | - |
| `Stmt_Enum` | `attrGroups`, `implements`, `name`, `scalarType`, `stmts` | - |
| `Stmt_EnumCase` | `attrGroups`, `expr`, `name` | - |
| `Stmt_Expression` | `expr` | - |
| `Stmt_Finally` | `stmts` | - |
| `Stmt_For` | `cond`, `init`, `loop`, `stmts` | - |
| `Stmt_Foreach` | `expr`, `keyVar`, `stmts`, `valueVar` | `byRef` |
| `Stmt_Function` | `attrGroups`, `name`, `namespacedName`, `params`, `returnType`, `stmts` | `byRef` |
| `Stmt_Global` | `vars` | - |
| `Stmt_Goto` | `name` | - |
| `Stmt_GroupUse` | `prefix`, `uses` | `type` |
| `Stmt_HaltCompiler` | - | `remaining` |
| `Stmt_If` | `cond`, `else`, `elseifs`, `stmts` | - |
| `Stmt_InlineHTML` | - | `value` |
| `Stmt_Interface` | `attrGroups`, `extends`, `name`, `stmts` | - |
| `Stmt_Label` | `name` | - |
| `Stmt_Namespace` | `name`, `stmts` | - |
| `Stmt_Nop` | - | - |
| `Stmt_Property` | `attrGroups`, `props`, `type` | `flags` |
| `Stmt_PropertyProperty` | `default`, `name` | - |
| `Stmt_Return` | `expr` | - |
| `Stmt_Static` | - | `vars` |
| `Stmt_StaticVar` | `default`, `var` | - |
| `Stmt_Switch` | `cases`, `cond` | - |
| `Stmt_Throw` | `expr` | - |
| `Stmt_Trait` | `attrGroups`, `name`, `stmts` | - |
| `Stmt_TraitUse` | `adaptations`, `traits` | - |
| `Stmt_TryCatch` | `catches`, `finally`, `stmts` | - |
| `Stmt_Unset` | `vars` | - |
| `Stmt_Use` | `uses` | `type` |
| `Stmt_UseUse` | `alias`, `name` | `type` |
| `Stmt_While` | `cond`, `stmts` | - |

### Expressions (Expr_*)

| Type | Subnodes (children) | Properties (scalars) |
|------|---------------------|----------------------|
| `Expr_Array` | `items` | - |
| `Expr_ArrayDimFetch` | `dim`, `var` | - |
| `Expr_ArrayItem` | `key`, `value` | `byRef`, `unpack` |
| `Expr_ArrowFunction` | `attrGroups`, `expr`, `params`, `returnType` | `byRef`, `static` |
| `Expr_Assign` | `expr`, `var` | - |
| `Expr_AssignOp_BitwiseAnd` | `var`, `expr` | - |
| `Expr_AssignOp_BitwiseOr` | `var`, `expr` | - |
| `Expr_AssignOp_BitwiseXor` | `var`, `expr` | - |
| `Expr_AssignOp_Coalesce` | `var`, `expr` | - |
| `Expr_AssignOp_Concat` | `var`, `expr` | - |
| `Expr_AssignOp_Div` | `var`, `expr` | - |
| `Expr_AssignOp_Minus` | `var`, `expr` | - |
| `Expr_AssignOp_Mod` | `var`, `expr` | - |
| `Expr_AssignOp_Mul` | `var`, `expr` | - |
| `Expr_AssignOp_Plus` | `var`, `expr` | - |
| `Expr_AssignOp_Pow` | `var`, `expr` | - |
| `Expr_AssignOp_ShiftLeft` | `var`, `expr` | - |
| `Expr_AssignOp_ShiftRight` | `var`, `expr` | - |
| `Expr_AssignRef` | `expr`, `var` | - |
| `Expr_BinaryOp_BitwiseAnd` | `left`, `right` | - |
| `Expr_BinaryOp_BitwiseOr` | `left`, `right` | - |
| `Expr_BinaryOp_BitwiseXor` | `left`, `right` | - |
| `Expr_BinaryOp_BooleanAnd` | `left`, `right` | - |
| `Expr_BinaryOp_BooleanOr` | `left`, `right` | - |
| `Expr_BinaryOp_Coalesce` | `left`, `right` | - |
| `Expr_BinaryOp_Concat` | `left`, `right` | - |
| `Expr_BinaryOp_Div` | `left`, `right` | - |
| `Expr_BinaryOp_Equal` | `left`, `right` | - |
| `Expr_BinaryOp_Greater` | `left`, `right` | - |
| `Expr_BinaryOp_GreaterOrEqual` | `left`, `right` | - |
| `Expr_BinaryOp_Identical` | `left`, `right` | - |
| `Expr_BinaryOp_LogicalAnd` | `left`, `right` | - |
| `Expr_BinaryOp_LogicalOr` | `left`, `right` | - |
| `Expr_BinaryOp_LogicalXor` | `left`, `right` | - |
| `Expr_BinaryOp_Minus` | `left`, `right` | - |
| `Expr_BinaryOp_Mod` | `left`, `right` | - |
| `Expr_BinaryOp_Mul` | `left`, `right` | - |
| `Expr_BinaryOp_NotEqual` | `left`, `right` | - |
| `Expr_BinaryOp_NotIdentical` | `left`, `right` | - |
| `Expr_BinaryOp_Plus` | `left`, `right` | - |
| `Expr_BinaryOp_Pow` | `left`, `right` | - |
| `Expr_BinaryOp_ShiftLeft` | `left`, `right` | - |
| `Expr_BinaryOp_ShiftRight` | `left`, `right` | - |
| `Expr_BinaryOp_Smaller` | `left`, `right` | - |
| `Expr_BinaryOp_SmallerOrEqual` | `left`, `right` | - |
| `Expr_BinaryOp_Spaceship` | `left`, `right` | - |
| `Expr_BitwiseNot` | `expr` | - |
| `Expr_BooleanNot` | `expr` | - |
| `Expr_Cast_Array` | `expr` | - |
| `Expr_Cast_Bool` | `expr` | - |
| `Expr_Cast_Double` | `expr` | - |
| `Expr_Cast_Int` | `expr` | - |
| `Expr_Cast_Object` | `expr` | - |
| `Expr_Cast_String` | `expr` | - |
| `Expr_Cast_Unset` | `expr` | - |
| `Expr_ClassConstFetch` | `class`, `name` | - |
| `Expr_Clone` | `expr` | - |
| `Expr_Closure` | `attrGroups`, `params`, `returnType`, `stmts`, `uses` | `byRef`, `static` |
| `Expr_ClosureUse` | `var` | `byRef` |
| `Expr_ConstFetch` | `name` | - |
| `Expr_Empty` | `expr` | - |
| `Expr_Error` | - | - |
| `Expr_ErrorSuppress` | `expr` | - |
| `Expr_Eval` | `expr` | - |
| `Expr_Exit` | `expr` | - |
| `Expr_FuncCall` | `args`, `name` | - |
| `Expr_Include` | `expr` | `type` |
| `Expr_Instanceof` | `class`, `expr` | - |
| `Expr_Isset` | `vars` | - |
| `Expr_List` | `items` | - |
| `Expr_Match` | `cond` | `arms` |
| `Expr_MethodCall` | `args`, `name`, `var` | - |
| `Expr_New` | `args`, `class` | - |
| `Expr_NullsafeMethodCall` | `args`, `name`, `var` | - |
| `Expr_NullsafePropertyFetch` | `name`, `var` | - |
| `Expr_PostDec` | `var` | - |
| `Expr_PostInc` | `var` | - |
| `Expr_PreDec` | `var` | - |
| `Expr_PreInc` | `var` | - |
| `Expr_Print` | `expr` | - |
| `Expr_PropertyFetch` | `name`, `var` | - |
| `Expr_ShellExec` | `parts` | - |
| `Expr_StaticCall` | `args`, `class`, `name` | - |
| `Expr_StaticPropertyFetch` | `class`, `name` | - |
| `Expr_Ternary` | `cond`, `else`, `if` | - |
| `Expr_Throw` | `expr` | - |
| `Expr_UnaryMinus` | `expr` | - |
| `Expr_UnaryPlus` | `expr` | - |
| `Expr_Variable` | `name` | - |
| `Expr_Yield` | `key`, `value` | - |
| `Expr_YieldFrom` | `expr` | - |

> **Note**: `Expr_AssignOp_*` and `Expr_BinaryOp_*` inherit from base classes. Their subnodes (`expr`/`var` or `left`/`right`) are consistent across the group.

### Scalars (Scalar_*)

| Type | Subnodes (children) | Properties (scalars) |
|------|---------------------|----------------------|
| `Scalar_DNumber` | - | `value` |
| `Scalar_Encapsed` | `parts` | - |
| `Scalar_EncapsedStringPart` | - | `value` |
| `Scalar_LNumber` | - | `value` |
| `Scalar_String` | - | `value` |

### Other Nodes

| Type | Subnodes (children) | Properties (scalars) |
|------|---------------------|----------------------|
| `Arg` | `name`, `unpack`, `value` | `byRef` |
| `ArrayItem` | `key`, `unpack`, `value` | `byRef` |
| `Attribute` | `args`, `name` | - |
| `AttributeGroup` | `attrs` | - |
| `ClosureUse` | `var` | `byRef` |
| `Const` | `name`, `value` | - |
| `DeclareItem` | `key`, `value` | - |
| `Identifier` | `name` | - |
| `InterpolatedStringPart` | - | `value` |
| `IntersectionType` | `types` | - |
| `MatchArm` | `body`, `conds` | - |
| `Name` | `parts[]` | - |
| `NullableType` | `type` | - |
| `Param` | `attrGroups`, `default`, `hooks`, `var`, `variadic` | `byRef`, `flags`, `type` |
| `PropertyHook` | `attrGroups`, `name`, `params` | `body`, `byRef`, `flags` |
| `PropertyItem` | `default`, `name` | - |
| `StaticVar` | `default`, `var` | - |
| `UnionType` | `types` | - |
| `UseItem` | `alias`, `name` | `type` |
| `VarLikeIdentifier` | `name` | - |
| `VariadicPlaceholder` | - | - |
