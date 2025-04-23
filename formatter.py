import re, ast
from typing import Callable, Any

# test methods for formatter
def bool_format(b, _type: str) -> str:
    if _type == "y/n":
        return "Yes" if b else "No"
    elif _type == "d/e":
        return "Enabled" if b else "Disabled"

def bold(s) -> str:
    return f"**{s}**"


class TemplateFormatter:
    func_mapping: dict[str, Callable]

    def __init__(self, allowed_funcs: list[Callable] | dict[str, Callable]) -> None:
        self.placeholder_regex: re.Pattern[str] = re.compile(r'\{(.*?)\}')

        # generates dict of {name: callable}
        if not allowed_funcs:
            raise ValueError("allowed_funcs argument cannot be empty")
        
        if isinstance(allowed_funcs, dict):
            self.func_mapping = allowed_funcs

        elif isinstance(allowed_funcs, tuple | set | list):
            self.func_mapping = {func.__name__: func for func in allowed_funcs}

        else:
            raise TypeError("allowed_funcs is not a dict or an array")
 
    def _safe_eval(self, value: Any, functions: list[tuple[str, dict]]) -> str:
        for func_name, kwargs in functions:

            # tries to get safe function
            if not (formatter := self.func_mapping.get(func_name)):
                continue
            
            # runs the function
            try:
                value = formatter(value, **kwargs)
            except:
                return value
    
        return value
    
    def _resolve_placeholder(self, placeholder: str) -> tuple[str, list]:
        expr: ast.expr = ast.parse(placeholder, mode="eval").body
        
        # plain placeholder, should be ignored
        if not isinstance(expr, ast.Call):
            return placeholder, []

        funcs: list[tuple[str, dict[str, Any]]] = []
        node: ast.AST = expr
        key: Any = None

        # walk down the left-most chain of calls
        while isinstance(node, ast.Call):

            if isinstance(node.func, ast.Name):
                func_name = node.func.id
    
            else:
                continue

            # pull out keyword arguments
            kwargs: dict[str, Any] = {}

            for kw in node.keywords:
                if kw.arg is None:
                    raise ValueError("**kwargs not supported in placeholders")

                kwargs[kw.arg] = ast.literal_eval(kw.value)

            funcs.append(
                (func_name, kwargs)
            )


            # now descend into the first positional argument, if it's another Call
            if node.args:
                first: ast.expr = node.args[0]

                if isinstance(first, ast.Call):
                    node = first
                    continue
               
                # if it's a Name or a literal, that's our key
                elif isinstance(first, ast.Name):
                    key = first.id

                elif isinstance(first, ast.Constant):
                    key = first.value

                else:
                    raise ValueError("Unsupported argument type for key: " + ast.dump(first))
            break

        if key is None:
            raise ValueError("Could not find an inner key in placeholder")

        # reverse and return
        funcs.reverse()
        return key, funcs

    def render_string(self, s: str, context: dict[str, str]) -> str:
        print(f"Got string: {s}")
        
        for placeholder in self.placeholder_regex.findall(s):
            print("\nNew placeholder:", placeholder)
            
            # resolve placeholder
            key, functions = self._resolve_placeholder(placeholder)
            print("Resolved:", key, functions)

            # format it
            formatted: str = self._safe_eval(context.get(key), functions)
            print("Formatted value:", formatted)

            if formatted != placeholder:
                s = s.replace("{" + placeholder + "}", str(formatted))

        return s

formatter = TemplateFormatter([bool_format, bold])
new_string: str = formatter.render_string(
    "This is {bold(bool_format(place1, _type='y/n'))} and {place2}", 
    context = {"place1": True, "place2": 35297}
)

print("\nFormatted:", new_string)
