import ast
import pandas as pd
import numpy as np

FORBIDDEN_IMPORTS = {
    "os",
    "subprocess",
    "socket",
    "requests",
    "shutil",
    "sys",
    "multiprocessing",
    "threading"
}

FORBIDDEN_FUNCTIONS = {
    "eval",
    "exec",
    "compile",
    "open",
    "__import__",
    "input",
    "globals",
    "locals"
}

FORBIDDEN_NODES = (
    ast.Attribute,
    ast.With,
    ast.Lambda,
    ast.ClassDef,
    ast.FunctionDef,
    ast.Try
)


def validate_code(code: str):
    """Проверка кода на безопасность"""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise ValueError(f"Syntax error in code: {e}")

    for node in ast.walk(tree):
        # Проверяем импорты
        if isinstance(node, ast.Import):
            for name in node.names:
                if name.name.split('.')[0] in FORBIDDEN_IMPORTS:
                    raise ValueError(f"Forbidden import: {name.name}")

        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.split('.')[0] in FORBIDDEN_IMPORTS:
                raise ValueError(f"Forbidden import: {node.module}")

        # Проверяем вызовы опасных функций
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in FORBIDDEN_FUNCTIONS:
                    raise ValueError(f"Forbidden function call: {node.func.id}")

    return True


def execute_python_on_df(code: str, df):
    """Выполняет Python код"""
    # Валидация кода
    validate_code(code)

    # Подготовка окружения
    safe_globals = {
        '__builtins__': {
            'print': print,
            'len': len,
            'range': range,
            'int': int,
            'float': float,
            'str': str,
            'list': list,
            'dict': dict,
            'set': set,
            'tuple': tuple,
            'sum': sum,
            'min': min,
            'max': max,
            'abs': abs,
            'round': round,
            'sorted': sorted,
            'enumerate': enumerate,
            'zip': zip,
            'any': any,
            'all': all,
            'bool': bool,
        },
        'pd': pd,
        'np': np,
        'df': df
    }

    local_vars = {}

    try:
        exec(code, safe_globals, local_vars)

        # Получение результатов
        result_lines = []
        for key, value in local_vars.items():
            if not key.startswith('_'):
                if isinstance(value, pd.DataFrame):
                    result_lines.append(f"{key}:\n{value.head(10).to_string()}")
                elif isinstance(value, pd.Series):
                    result_lines.append(f"{key}:\n{value.head(10).to_string()}")
                else:
                    result_lines.append(f"{key}: {value}")

        if not result_lines:
            return "Code executed successfully (no output variables)"

        return "\n\n".join(result_lines)

    except Exception as e:
        return f"Error executing code: {e}"