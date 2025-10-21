import ast
import inspect
import os
import re
from typing import Dict, List, Optional, Any
import logging
import yaml


def load_yaml(file_path: str) -> Dict[str, Any]:
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)
    return data
INOUT_CONFIG = load_yaml(os.path.join(os.path.dirname(__file__), 'INPUT_CONFIG.yaml'))
SETTINGS_CONFIG = load_yaml(os.path.join(os.path.dirname(__file__), 'SET_CONFIG.yaml'))
OUTPUT_CONFIG = load_yaml(os.path.join(os.path.dirname(__file__), 'OUTPUT_CONFIG.yaml'))

class CodeGenerator:
    """AST-based code generator"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def parse_template(self, template_code: str) -> ast.Module:
        """Template code syntax error AST"""
        try:
            return ast.parse(template_code)
        except SyntaxError as e:
            self.logger.error(f"error {e}")
            raise

    def find_replacement_markers(self, node: ast.AST) -> Dict[str, List[ast.AST]]:
        """Find all tokens that need to be replaced in the AST"""
        markers = {}

        class ReplacementFinder(ast.NodeVisitor):
            def __init__(self):
                self.markers = {}

            def visit_Expr(self, node):
                if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                 '''find {{...}} mode'''
                    matches = re.findall(r'\{\{(\w+)\}\}', node.value.value)
                    for marker in matches:
                        if marker not in self.markers:
                            self.markers[marker] = []
                        self.markers[marker].append(node)
                self.generic_visit(node)

            def visit_FunctionDef(self, node):
                # check if the function body contains a string literal
                for stmt in node.body:
                    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
                        if isinstance(stmt.value.value, str):
                            matches = re.findall(r'\{\{(\w+)\}\}', stmt.value.value)
                            for marker in matches:
                                if marker not in self.markers:
                                    self.markers[marker] = []
                                self.markers[marker].append(stmt)
                self.generic_visit(node)

            def visit_ClassDef(self, node):
                self.generic_visit(node)

        finder = ReplacementFinder()
        finder.visit(node)
        return finder.markers

    def generate_code_from_template(self, template_code: str, replacements: Dict[str, str]) -> str:
        """
        Generate code based on the template and replacement content

        Args:
            template_code
            replacements

        Returns:
            generated_code
        """
        try:
            tree = self.parse_template(template_code)


            markers = self.find_replacement_markers(tree)

            code_lines = template_code.split('\n')

            for marker_name, replacement_code in replacements.items():
                if marker_name in markers:
                    for node in markers[marker_name]:
                        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
                            lineno = node.lineno - 1

                            original_line = code_lines[lineno]
                            if f"{{{{{marker_name}}}}}" in original_line:
                                new_line = original_line.replace(
                                    f"{{{{{marker_name}}}}}",
                                    replacement_code
                                )
                                code_lines[lineno] = new_line
                            else:
                                code_lines[lineno] = replacement_code

            return '\n'.join(code_lines)

        except Exception as e:
            self.logger.error(f"fail: {e}")
            raise

    def generate_energyplus_code(self, config: Dict[str, Any]) -> str:
        """
            A method specifically for code generation for EnergyPlus co-simulation

        Args:
            config:

        Returns:
            generated_code:
        """
        template_path = config.get('template_path')
        with open(template_path, 'r', encoding='utf-8') as f:
            template_code = f.read()


        replacements = {}

        # initQueue
        if 'queues' in config:
            replacements['initQueue'] = self._generate_queue_init(config['queues'])

        # importInitInput
        if 'input_imports' in config:
            replacements['importInitInput'] = self._generate_input_imports(config['input_imports'])

        # inputLoad
        if 'input_loaders' in config:
            replacements['inputLoad'] = self._generate_input_loaders(config['input_loaders'])

        #  ExchangeLoad
        if 'exchange_handlers' in config:
            replacements['ExchangeLoad'] = self._generate_exchange_handlers(config['exchange_handlers'])

        #  import
        if 'imports' in config:
            replacements['import'] = self._generate_imports(config['imports'])

        #  call_back
        if 'callbacks' in config:
            replacements['call_back'] = self._generate_callbacks(config['callbacks'])

        # initStorgae
        if 'storage_init' in config:
            replacements['initStorgae'] = self._generate_storage_init(config['storage_init'])

        return self.generate_code_from_template(template_code, replacements)

    def _generate_queue_init(self, queues_config: List[Dict]) -> str:
        lines = []
        for queue_config in queues_config:
            name = queue_config['name']
            lines.append(f"        self.{name} = queue.Queue()")
        return '\n'.join(lines)

    def _generate_input_imports(self, imports_config: List[Dict]) -> str:
        lines = []
        for import_config in imports_config:
            module = import_config['module']
            class_name = import_config['class_name']
            instance_name = import_config.get('instance_name', class_name.lower())
            lines.append(f"        import {module}")
            lines.append(f"        self.instances['{instance_name}'] = {module}.{class_name}()")
        return '\n'.join(lines)

    def _generate_input_loaders(self, loaders_config: List[Dict]) -> str:
        lines = []
        for loader_config in loaders_config:
            module = loader_config['module']
            class_name = loader_config['class_name']
            package = __import__(module)
            object = getattr(package, class_name)
            description = object.description
            lines.append(description)
        return '\n'.join(lines)

    def _generate_imports(self, imports_config: List[str]) -> str:
        lines = []
        for import_line in imports_config:
            lines.append(f"        {import_line}")
        return '\n'.join(lines)

    def _generate_callbacks(self, callbacks_config: List[Dict]) -> str:

        lines = []
        for callback_config in callbacks_config:
            callback_type = callback_config['type']
            handler_method = callback_config['handler_method']
            lines.append(
                f"        api.runtime.callback_{callback_type}(state, self.energyplus_simulator.{handler_method})")
        return '\n'.join(lines)

    def _generate_storage_init(self, storage_config: Dict) -> str:

        if 'mysql_config' in storage_config:
            className = storage_config.get('class_name')
            package = __import__(className)
            object = getattr(package, className)
            return object.description
        else:
            return ''


def read_code_files(file_path):
    """ read main process code """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        return code
    except Exception as e:
        print(f"read code error: {e}")
        return None, None

def _get_config_from_request():
    """ get config from request """
    try:
        config = {}
        config.update('template_path', 'main.py')
        #INPUT_CONFIG
        config.update('INPUT_CONFIG')
        for input_config in INPUT_CONFIG:
            if input_config.get('type') == 'http':
                config['input_imports'].append({
                    'module': 'httpCommunicate',
                    'class_name': 'HTTPCommunicate'
                })

            elif input_config.get('type') == 'modbus':
                config['input_imports'].append({
                    'module': 'modbusCommunicate',
                    'class_name': 'ModbusCommunicate'
                })

            elif input_config.get('type') == 'websocket':
                config['input_imports'].append({
                    'module': 'websocketCommunicate',
                    'class_name': 'WebSocketCommunicate'
                })
        #SET_CONFIG
        config.update('queues')
        config.update('callbacks')
        config.update('exchange_handle')
        dataDict = preprocess(SET_CONFIG.get('exchange_file'))

        for data in dataDict:
            if data[-1] == 'set_weather_flag':
                config['callbacks'].append({
                'type': 'before_predictor',
                'handler_method': 'before_predictor_flag'
            })
                config['queues'].append({'name': 'weatherData'})
                config['exchange_handle'].append({
                    'name': 'weather_data'
                })
            elif data[-1] == 'set_hvac_manager_flag':
                config['callbacks'].append({
                'type': 'before_hvac_managers',
                'handler_method': 'before_hvac_managers_flag'
            })
                config['queues'].append({'name': 'sensorData'})
                config['exchange_handle'].append({
                    'name': 'hvac_manager_flag'
                })
            elif data[-1] == 'set_loop_flag':
                config['callbacks'].append({
                'type': 'itrator_loop_flag',
                'handler_method': 'itrator_loop_flag'
            })
                config['queues'].append({'name': 'controlData'})
                config['exchange_handle'].append({
                    'name': 'time_step_loop_flag'
                })

            elif data[-1] == 'set_heat_flag':
                config['callbacks'].append({
                'type': 'init_heat_flag',
                'handler_method': 'init_heat_flag'
                    })
                config['exchange_handle'].append({
                    'name': 'init_heat_flag'
                })
                config['queues'].append({'name': 'controlData'})
            else:
                pass
        #OUTPUT_CONFIG
        config.update('output_imports')
        for output_config in OUTPUT_CONFIG:
            if output_config.get('type') == 'mysql':
                config['output_imports'].append({
                    'module': 'mysqlCommunicate',
                    'class_name': 'HTTPCommunicate'
                })
        return config
    except Exception as e:
        print(f"get config error: {e}")
        return None

def main():
    generator = CodeGenerator()

    config = _get_config_from_request()
    template = read_code_files('main.py')



    try:
        generated_code = generator.generate_energyplus_code(config)

        output_path = 'generated_energyplus.py'
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(generated_code)

        print(f"code Generated: {output_path}")

        try:
            ast.parse(generated_code)
        except SyntaxError as e:
            print(f"error: {e}")

    except Exception as e:
        print(f"fail: {e}")


if __name__ == "__main__":
    main()
