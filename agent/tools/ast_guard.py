import ast

ALLOWED_NODES = {
    ast.Module,
    ast.FunctionDef,
    ast.Assign,
    ast.Expr,
    ast.Call,
    ast.Name,
    ast.Load,
    ast.Store,
    ast.Constant,
    ast.BinOp,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Return,
    ast.If,
    ast.Compare,
    ast.Eq,
    ast.arguments,
    ast.arg,
    ast.Import,
    ast.ImportFrom,
    ast.alias,
    ast.ClassDef,
    ast.Attribute,
    ast.Pass,
    ast.Tuple,
    ast.AnnAssign,
    ast.Subscript,
    ast.Index,
    ast.Slice,
    ast.List,
    ast.Dict,
    ast.Set,
    ast.With,
    ast.withitem,
    ast.Assert,
    ast.IfExp,
    ast.ListComp,
    ast.DictComp,
    ast.SetComp,
    ast.GeneratorExp,
    ast.Try,
    ast.ExceptHandler,
    ast.Raise,
}

def validate_code(code: str):
    tree = ast.parse(code)

    for node in ast.walk(tree):
        if type(node) not in ALLOWED_NODES:
            raise Exception(f"禁止構文: {type(node).__name__}")

    return True