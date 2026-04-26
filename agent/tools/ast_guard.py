import ast

ALLOWED_NODES = {
    ast.Module,
    ast.FunctionDef,
    ast.Assign,
    ast.Expr,
    ast.Call,
    ast.Name,
    ast.Load,
    ast.Constant,
    ast.BinOp,
    ast.Add,
}

def validate_code(code: str):
    tree = ast.parse(code)

    for node in ast.walk(tree):
        if type(node) not in ALLOWED_NODES:
            raise Exception(f"禁止構文: {type(node).__name__}")

    return True