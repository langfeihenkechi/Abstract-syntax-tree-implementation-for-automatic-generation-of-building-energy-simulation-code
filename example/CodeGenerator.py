import ast
import inspect
import os
import re
from typing import Dict, List, Optional, Any
import logging


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
                # 检查函数体中的字符串表达式
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
        template_path = config.get('template_path', 'energyplus_template.py')
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
            method_name = loader_config.get('method_name', 'get_instance')
            lines.append(f"    import {module}")
            lines.append(f"    def __get_{class_name.lower()}_instance(self):")
            lines.append(f"        instance = {module}.{class_name}()")
            lines.append(f"        self.instances['{class_name.lower()}'] = instance")
        return '\n'.join(lines)

    def _generate_exchange_handlers(self, handlers_config: List[Dict]) -> str:

        lines = []
        for handler_config in handlers_config:
            name = handler_config['name']
            component_type = handler_config['component_type']
            control_type = handler_config['control_type']
            lines.append(f"    def {name}(self, state):")
            lines.append(f'        """')
            lines.append(f"        Process {name} data")
            lines.append(f'        """')
            lines.append(f"        item = self.config.{name}.get()")
            lines.append(f"        for d in item:")
            lines.append(
                f"            self.set_actuator_value(state, '{component_type}', '{control_type}', d.actuator_key, d.value)")
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
        lines = []
        if 'mysql_config' in storage_config:
            mysql_config = storage_config['mysql_config']
            lines.append("    def init_mysql_storage(self):")
            lines.append('        """init MySQL """')
            lines.append(f"        host = '{mysql_config.get('host', 'localhost')}'")
            lines.append(f"        user = '{mysql_config.get('user', 'root')}'")
            lines.append(f"        password = '{mysql_config.get('password', '')}'")
            lines.append(f"        database = '{mysql_config.get('database', 'energyplus')}'")
            lines.append("        # 这里添加 MySQL 连接代码")
        return '\n'.join(lines)


def main():
    generator = CodeGenerator()

    config = {
        'template_path': 'energyplus_template.py',
        'queues': [
            {'name': 'weatherData'},
            {'name': 'sensorData'},
            {'name': 'controlData'}
        ],
        'input_imports': [
            {
                'module': 'httpCommunicate',
                'class_name': 'HTTPCommunicate',
                'instance_name': 'http'
            },
            {
                'module': 'modbusCommunicate',
                'class_name': 'ModbusCommunicate',
                'instance_name': 'modbus'
            }
        ],
        'input_loaders': [
            {
                'module': 'mqttCommunicate',
                'class_name': 'MQTTCommunicate'
            }
        ],
        'exchange_handlers': [
            {
                'name': 'time_step_weather',
                'component_type': 'Weather Data',
                'control_type': 'Outdoor Dry Bulb'
            },
            {
                'name': 'time_step_sensor',
                'component_type': 'Sensor',
                'control_type': 'Reading'
            }
        ],
        'imports': [
            "self.input_communicate = InputCommunicate()",
            "self.data_storage = DataStorage()"
        ],
        'callbacks': [
            {
                'type': 'begin_zone_timestep_before_set_current_weather',
                'handler_method': 'time_step_weather'
            },
            {
                'type': 'after_component_get_input',
                'handler_method': 'time_step_sensor'
            }
        ],
        'storage_init': {
            'mysql_config': {
                'host': 'localhost',
                'user': 'energyplus_user',
                'password': 'password123',
                'database': 'energyplus_data'
            }
        }
    }

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