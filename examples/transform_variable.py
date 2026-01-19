"""AST transformation helper for php-parser-py.

Example: Transform $data to function($data)
"""
from php_parser_py import parse, PrettyPrinter


def transform_variable_to_function_call(ast, var_name: str, func_name: str):
    """Transform a variable to a function call.
    
    Example: $data → function($data)
    
    Args:
        ast: The AST to modify
        var_name: Variable name (without $)
        func_name: Function name to wrap with
    """
    # Find all variable nodes with the given name
    var_nodes = [
        node for node in ast.nodes()
        if node.node_type == "Expr_Variable" and node.get("name") == var_name
    ]
    
    for var_node in var_nodes:
        # Find parent edge
        parent_edges = [
            e for e in ast._storage.get_edges()
            if e[1] == var_node.id and e[2] == "PARENT_OF"
        ]
        
        if not parent_edges:
            continue
            
        parent_id, _, _ = parent_edges[0]
        edge_props = ast._storage.get_edge_props(parent_edges[0])
        field_name = edge_props.get("field")
        
        # Create new nodes for function call
        # We need: FuncCall -> Name + Args -> Arg -> Variable
        
        # 1. Create Name node (function name)
        name_id = f"node_new_name_{var_node.id}"
        ast._storage.add_node(name_id)
        ast._storage.set_node_props(name_id, {
            "nodeType": "Name",
            "parts": [func_name],
            "startLine": var_node.start_line,
            "endLine": var_node.end_line,
        })
        
        # 2. Create Arg node (argument wrapper)
        arg_id = f"node_new_arg_{var_node.id}"
        ast._storage.add_node(arg_id)
        ast._storage.set_node_props(arg_id, {
            "nodeType": "Arg",
            "name": None,
            "byRef": False,
            "unpack": False,
            "startLine": var_node.start_line,
            "endLine": var_node.end_line,
        })
        
        # 3. Create FuncCall node
        funccall_id = f"node_new_funccall_{var_node.id}"
        ast._storage.add_node(funccall_id)
        ast._storage.set_node_props(funccall_id, {
            "nodeType": "Expr_FuncCall",
            "startLine": var_node.start_line,
            "endLine": var_node.end_line,
        })
        
        # 4. Connect the nodes
        # FuncCall -> Name (name field)
        ast._storage.add_edge((funccall_id, name_id, "PARENT_OF"))
        ast._storage.set_edge_props(
            (funccall_id, name_id, "PARENT_OF"),
            {"field": "name"}
        )
        
        # FuncCall -> Arg (args field, index 0)
        ast._storage.add_edge((funccall_id, arg_id, "PARENT_OF"))
        ast._storage.set_edge_props(
            (funccall_id, arg_id, "PARENT_OF"),
            {"field": "args", "index": 0}
        )
        
        # Arg -> Variable (value field)
        ast._storage.add_edge((arg_id, var_node.id, "PARENT_OF"))
        ast._storage.set_edge_props(
            (arg_id, var_node.id, "PARENT_OF"),
            {"field": "value"}
        )
        
        # 5. Replace parent's reference
        # Remove old edge
        ast._storage.remove_edge((parent_id, var_node.id, "PARENT_OF"))
        
        # Add new edge to FuncCall
        ast._storage.add_edge((parent_id, funccall_id, "PARENT_OF"))
        ast._storage.set_edge_props(
            (parent_id, funccall_id, "PARENT_OF"),
            edge_props
        )
    
    return ast


# Example usage
if __name__ == "__main__":
    # Original code
    code = """<?php
    echo $data;
    $result = $data + 1;
    """
    
    ast = parse(code)
    print("Original code:")
    print(code)
    
    # Transform $data to sanitize($data)
    transform_variable_to_function_call(ast, "data", "sanitize")
    
    # Generate modified code
    printer = PrettyPrinter()
    generated = printer.print(ast)
    
    print("\nTransformed code:")
    print(generated)
