#!/usr/bin/env python3
"""
Script to download and analyze PHP-Parser AST nodes directly from GitHub source.
Parses PHPDoc types to distinguish Node children from Scalar properties.

Usage:
    uv run python scripts/generate_ast_docs.py
"""

import os
import re
import json
import urllib.request
from pathlib import Path
from collections import defaultdict

# Configuration
GITHUB_API_BASE = "https://api.github.com/repos/nikic/PHP-Parser/contents/lib/PhpParser/Node"
REF = "4.x"
CACHE_DIR = Path(".ast_cache")
HEADERS = {"User-Agent": "PHP-Parser-Docs-Generator"}

# Categories
CATEGORIES = {
    "Stmt": "Statements",
    "Expr": "Expressions",
    "Scalar": "Scalars",
    "": "Other"
}

def fetch_file_list(path=""):
    """Fetch list of files from GitHub API."""
    url = f"{GITHUB_API_BASE}/{path}?ref={REF}"
    # print(f"Fetching {url}...")
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read())
    except Exception as e:
        print(f"Error fetching {path}: {e}")
        return []

def download_file(download_url, local_path):
    """Download file content to local path."""
    if local_path.exists():
        return local_path.read_text()
    
    # print(f"Downloading {local_path.name}...")
    req = urllib.request.Request(download_url, headers=HEADERS)
    with urllib.request.urlopen(req) as response:
        content = response.read().decode('utf-8')
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_text(content)
        return content

def parse_php_class(content, filename=""):
    """
    Parse a PHP node file to extract:
    - Class name
    - Abstract status
    - Local properties with their types from docblocks
    - Subnode names from getSubNodeNames
    """
    # 1. Check class definition
    class_match = re.search(r'(abstract\s+)?class\s+(\w+)\s+extends\s+(\w+)', content)
    if not class_match:
        return None
    
    is_abstract = bool(class_match.group(1))
    class_name = class_match.group(2)
    
    if is_abstract:
        return None

    # 2. Extract getSubNodeNames
    subnodes_list = []
    subnode_match = re.search(r'function getSubNodeNames\(\)\s*:\s*array\s*\{\s*return\s*\[(.*?)\];', content, re.DOTALL)
    if subnode_match:
        raw_names = subnode_match.group(1)
        subnodes_list = re.findall(r"['\"](\w+)['\"]", raw_names)
    
    # 3. Extract properties and their docblock types
    props_map = {}
    lines = content.split('\n')
    current_docblock = ""
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('/**') or stripped.startswith('*'):
            current_docblock += stripped + " "
        elif stripped.startswith('public $'):
            match = re.search(r'public\s+\$(\w+)', stripped)
            if match:
                prop_name = match.group(1)
                type_match = re.search(r'@var\s+([^\s]+)', current_docblock)
                prop_type = type_match.group(1) if type_match else "unknown"
                props_map[prop_name] = prop_type
            current_docblock = "" 
        elif 'function' in stripped or 'class' in stripped:
             if 'class' in stripped and 'extends' in stripped:
                 pass 
             else:
                 current_docblock = ""
             
    # 4. Classify properties
    real_subnodes = []
    scalar_props = []
    
    # Track processed subnodes
    processed_subnodes = set()

    # Process all found properties
    for prop_name, prop_type in props_map.items():
        if prop_name == 'attributes': continue
        
        is_node = False
        
        # Explicit Node types in docblock
        if 'Node' in prop_type or 'Expr' in prop_type or 'Stmt' in prop_type or 'Name' in prop_type or 'Identifier' in prop_type or 'Arg' in prop_type:
            is_node = True
        elif '[]' in prop_type:
            base_type = prop_type.replace('[]', '').replace('|null', '')
            if 'Node' in base_type or 'Expr' in base_type or 'Stmt' in base_type or 'Arg' in base_type or 'Case' in base_type or 'Catch' in base_type or 'Declare' in base_type or 'Use' in base_type or 'Property' in base_type:
                is_node = True
                
        # Known fields override
        if prop_name in ['flags', 'type', 'byRef', 'variadic', 'unpack', 'remaining', 'value']:
            pass # Keep scalar logic priority
        elif prop_name in ['stmts', 'params', 'args', 'implements', 'extends', 'uses', 'expr', 'var', 'name', 'parts', 'items', 'cond', 'left', 'right', 'init', 'loop', 'else', 'elseifs', 'finally', 'catches', 'cases', 'keyVar', 'valueVar']:
            is_node = True
        
        # If it's in getSubNodeNames list, it's structurally a subnode, 
        # BUT we distinguish "Scalar Subnodes" (like flags) vs "Node Subnodes".
        # We want "Subnodes" column to be Node objects, "Properties" to be Scalars.
        
        if is_node:
            real_subnodes.append(prop_name)
            processed_subnodes.add(prop_name)
        else:
            scalar_props.append(prop_name)

    # 5. Handle Subnodes NOT found in properties (fallback)
    # This catches cases where our regex missed the property but it's in getSubNodeNames
    for sub in subnodes_list:
        if sub not in processed_subnodes and sub != 'attributes' and sub not in scalar_props:
            # If we missed the property definition, we assume it's a Node Subnode 
            # unless it's a known scalar name
            if sub in ['flags', 'type', 'byRef', 'mode']:
                if sub not in scalar_props: scalar_props.append(sub)
            else:
                real_subnodes.append(sub)

    return {
        "name": class_name,
        "subnodes": sorted(list(set(real_subnodes))),
        "properties": sorted(list(set(scalar_props)))
    }

def main():
    CACHE_DIR.mkdir(exist_ok=True)
    all_nodes = defaultdict(list)
    dirs_to_scan = ["", "Stmt", "Expr", "Scalar", "Expr/BinaryOp", "Expr/AssignOp", "Expr/Cast"]
    
    files_to_process = []
    for subdir in dirs_to_scan:
        items = fetch_file_list(subdir)
        for item in items:
            if item['type'] == 'file' and item['name'].endswith('.php'):
                files_to_process.append({
                    "url": item['download_url'],
                    "path": Path(subdir) / item['name'],
                    "subdir": subdir
                })
    
    print(f"Analyzing {len(files_to_process)} files...")
    
    for file_info in files_to_process:
        local_path = CACHE_DIR / file_info['path']
        content = download_file(file_info['url'], local_path)
        node_data = parse_php_class(content, file_info['path'].name)
        
        if node_data:
            path_str = str(file_info['path'])
            category = "Other"
            name = node_data['name']
            
            if path_str.startswith("Stmt"):
                category = "Stmt"
                name = "Stmt_" + name
            elif path_str.startswith("Expr"):
                category = "Expr"
                if "BinaryOp" in path_str: name = "Expr_BinaryOp_" + name
                elif "AssignOp" in path_str: name = "Expr_AssignOp_" + name
                elif "Cast" in path_str: name = "Expr_Cast_" + name
                else: name = "Expr_" + name
            elif path_str.startswith("Scalar"):
                category = "Scalar"
                name = "Scalar_" + name
            
            if name.endswith("_"): name = name[:-1]
            if name == "Expr_BinaryOp": continue
            
            node_data['full_name'] = name
            all_nodes[category].append(node_data)

    print("\n" + "="*50)
    print("ANALYSIS RESULT WITH TYPES")
    print("="*50 + "\n")
    
    for category in ["Stmt", "Expr", "Scalar", "Other"]:
        if category not in all_nodes: continue
        nodes = sorted(all_nodes[category], key=lambda x: x['full_name'])
        print(f"### {CATEGORIES.get(category, category)} ({len(nodes)} types)")
        print()
        print("| Type | Subnodes (children) | Properties (scalars) |")
        print("|------|---------------------|----------------------|")
        for node in nodes:
            sub = ", ".join([f"`{s}`" for s in node['subnodes']]) if node['subnodes'] else "-"
            props = ", ".join([f"`{p}`" for p in node['properties']]) if node['properties'] else "-"
            print(f"| `{node['full_name']}` | {sub} | {props} |")
        print()

if __name__ == "__main__":
    main()
