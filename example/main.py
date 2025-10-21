import logging
import os
import queue
import subprocess
import sys
import tempfile
from datetime import time
from logging.handlers import RotatingFileHandler
from plistlib import Dict

import OUTPUT_CONFIG
import INPUT_CONFIG
import SET_CONFIG
import xlrd
from numba import Any

from pyenergyplus.api import EnergyPlusAPI


import yaml


def load_yaml(file_path: str) -> Dict[str, Any]:
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)
    return data
INOUT_CONFIG = load_yaml(os.path.join(os.path.dirname(__file__), 'INPUT_CONFIG.yaml'))
SETTINGS_CONFIG = load_yaml(os.path.join(os.path.dirname(__file__), 'SET_CONFIG.yaml'))
OUTPUT_CONFIG = load_yaml(os.path.join(os.path.dirname(__file__), 'OUTPUT_CONFIG.yaml'))

def setup_logging():
    """设置日志配置"""
    log_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 文件处理器
    file_handler = RotatingFileHandler(
        'energyplus_weather_integration.log',
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(logging.INFO)

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(logging.INFO)

    # 主日志器
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def preprocess(file_path):
    try:
        xls_table = xlrd.open_workbook(file_path)
        sheet = xls_table.sheet_by_index(0)
        rows = sheet.nrows
        l = sheet.row_values(0)
        if l[0] != 'id' or l[1] != 'component_type':
            return False
        for i in range(1, rows):
            line = sheet.row_values(i)
            if line[1] == 'Meter' or line[1] == 'Variable':
                output_dict.update({line[0]: line[1:]})
                data_dict.update({line[0]: line[1:]})
            else:
                data_dict.update({line[0]: line[1:]})
        print(data_dict)
        return True
    except:
        return False


logger = setup_logging()

api = EnergyPlusAPI()
state = api.state_manager.new_state()


data_dict = {}
output_dict = {}
dictFlag = {'window sading control': 'init_heat_balance_flag', 'thermal envelope': 'init_heat_balance_flag',
            'surface': 'init_heat_balance_flag', 'other side boundary condition': 'init_heat_balance_flag',
            'condfd surface material layer': 'init_heat_balance_flag',
            'Material': 'init_heat_balance_flag', 'Zone Infiltration': 'init_heat_balance_flag',
            'Zone Ventilation': 'init_heat_balance_flag',
            'ZoneMixing': 'init_heat_balance_flag', 'ZoneCrossMixing': 'init_heat_balance_flag',
            'ZoneRefDoorMixing': 'init_heat_balance_flag',
            'Zone Thermal Chimney': 'init_heat_balance_flag',
            'Zone': 'init_heat_balance_flag',
            'AirFlow Network Window/Door Opening': 'init_heat_balance_flag',
            'Lights': 'before_predictor_flag', 'ElectricEquipment': 'before_predictor_flag',
            'GasEquipment': 'before_predictor_flag',
            'HotWaterEquipment': 'before_predictor_flag', 'SteamEquipment': 'before_predictor_flag',
            'OtherEquipment': 'before_predictor_flag',
            'Pump': 'before_predictor_flag', 'ZoneBaseboard:OutdoorTemperatureControlled': 'before_predictor_flag',
            'ExteriorLights': 'before_predictor_flag',
            'System Node Setpoint': 'before_hvac_managers_flag',
            'Zone Temperature Control': 'before_hvac_managers_flag',
            'Zone Humidity Control': 'before_hvac_managers_flag',
            'Zone Comfort Control': 'before_hvac_managers_flag', 'Plant Loop Overall': 'before_hvac_managers_flag',
            'Supply Side Half Loop': 'before_hvac_managers_flag',
            'Supply Side Branch': 'before_hvac_managers_flag', 'Demand Side Branch': 'before_hvac_managers_flag',
            'Plant Component': 'before_hvac_managers_flag',
            'Outdoor Air System Node': 'before_havc_managers_flag', '“AirLoopHVAC': 'before_hvac_managers_flag',
            'Ideal Loads Air System': 'before_hvac_managers_flag',
            'Fan': 'before_hvac_managers_flag',
            '“Coil:Cooling:DX:SingleSpeed:ThermalStorage': 'before_hvac_managers_flag',
            'Unitary HVAC': 'itrator_loop_flag',
            'AirLoopHVAC:Unitary:Furnace:HeatOnly': 'itrator_loop_flag',
            'AirLoopHVAC:UnitaryHeatOnly': 'itrator_loop_flag',
            'AirLoopHVAC:Unitary:Furnace:HeatCool': 'itrator_loop_flag',
            'AirLoopHVAC:UnitaryHeatCool': 'itrator_loop_flag', 'UnitarySystem': 'itrator_loop_flag',
            'Coil Speed Control': 'itrator_loop_flag',
            'AirTerminal:SingleDuct:ConstantVolume:NoReheat': 'itrator_loop_flag',
            'itrator_loop_flag': 'itrator_loop_flag',
            'Outdoor Air Controller': 'itrator_loop_flag', 'Plant Equipment Operation': 'itrator_loop_flag',
            'Plant Load Profile': 'itrator_loop_flag',
            'Pump': 'itrator_loop_flag', 'Window Air Conditioner': 'itrator_loop_flag',
            'Hydronic Low Temp Radiant': 'itrator_loop_flag',
            'Constant Flow Low Temp Radiant': 'itrator_loop_flag',
            'Variable Refrigerant Flow Heat Pump': 'itrator_loop_flag',
            'Variable Refrigerant Flow Terminal Unit': 'itrator_loop_flag', 'Weather Data': 'set_weather_flag'}
produces = []
monitings = []

class Actuator_obj:
    def __init__(self, component_type, control_type, actuator_key, value):
        self.control_type = control_type
        self.actuator_key = actuator_key
        self.value = value
        self.component_type = component_type


class Config:
    def __init__(self, config):
        self.weather = config.get('weather_file')
        self.idf = config.get('idf_file')
        self.time = config.get('time')
        self.set_queues()

    def set_queues(self):
        {{initQueue}}
        '''self.weatherData = queue.Queue()'''
        pass


class InputCommunicate:

    """
    intputCommunicationModel - Automatically load the input for the corresponding requirement
    """

    def __init__(self):
        self.instances = {}
        self.inputs = []


        {{importInitInput}}
        "self.__get_HTTP_Instance()"

    def input_connect(self):
        try:
            for config in INPUT_CONFIG:
                self.inputs.append(self.instances[config.name].connect(config))
        except Exception as e:
            print('Error connecting to inputs: ', e)


    {{inputLoad}}
    '''
        import httpCommunicate
        def __get_httpCommunication_Instance(self):
            instance = httpCommunicate()
            self.instances.append(instance)
        '''

    def fetch_data(self):
        try:
            standeredDatas = []

            for input in self.inputs:
                data = input.get_data()
                for item in date:
                    if dataDict.__contains__(item):
                        tmp = dataDict[item]
                        obj = Actuator_obj(tmp[0], tmp[1], tmp[2], date[item])
                        standeredDatas.append(obj)
            return standeredDatas
        except Exception as e:
            print('Error fetching data: ', e)


class EnergyPlusSimulator:
    """
    EnergyPlusSimulator - Simulates EnergyPlus using the given IDF and weather file
    """

    def __init__(self, idf_file: str, weather_file: str, interval: int, config):
        """
        Initialising the EnergyPlus simulator

        """
        self.idf_file = idf_file
        self.weather_file = weather_file
        self.output_dir = tempfile.mkdtemp(prefix='energyplus_output_')
        self.simulation_thread = None
        self.is_running = False
        self.interval = interval
        self.config = config


    def set_actuator_value(state, component_type, control_type, actuator_key, value):
        handle = api.exchange.get_actuator_handle(state, component_type, control_type, actuator_key)

        if handle == -1:
            return

        api.exchange.set_actuator_value(state, handle, value)

    {{ExchangeLoad}}
    '''def time_step_weather(self, state):
        """
        Process the weather data at the beginning of the time step.
        """
        item = self.config.weatherData.get()

        for d in item:
            self.set_actuator_value(state, d.component_type, d.control_type, d.actuator_key, d.value)'''

    def time_step_reporting(self, state):
        time.sleep(self.interval)

    def _process_output_files(self):
        """

        Processing output file

        """
        try:
            # 查找CSV输出文件
            for file in os.listdir(self.output_dir):
                if file.endswith('.csv'):
                    csv_path = os.path.join(self.output_dir, file)
                    df = pd.read_csv(csv_path)
                    logger.info(f" {file} {len(df)}")
                    # 这里可以添加更多的输出处理逻辑
        except Exception as e:
            logger.error(f" {e}")

    def cleanup(self):
        """
        Clear temporary files
        """
        try:
            if os.path.exists(self.output_dir):
                shutil.rmtree(self.output_dir)
                logger.info(f"{self.output_dir}")
        except Exception as e:
            logger.error(f"{e}")

class EnergyPlusCaculation:
    """
    Real-time EnergyPlus system main controller
    """

    def __init__(self):
        """
        Initialise system

        """
        self.config = Config(SET_CONFIG)

        """self.input_communicate = InputCommunicate()"""
        {{importInput}}

        self.energyplus_simulator = EnergyPlusSimulator(self.config.idf, self.config.weather, self.config.time, self.input_communicate.inputs)
        {{importOutput}}
        """self.data_storage = DataStorage()"""

    def start(self):
        """start"""
        logger.info("Start EnergyPlus Simulate")
        self.is_running = True

        try:
            self.input_communicate.input_connect()
            self.run_simulation()
            self.data_storage.storage_output()
            self.energyplus_simulator.cleanup()
        except Exception as e:
            logger.error(f" {e}")

    def run_simulation(self) -> bool:
        """
        Run EnergyPlus simulation

        """
        try:
            {{call_back}}
            '''api.runtime.callback_begin_zone_timestep_before_set_current_weather(state, self.energyplus_simulator.time_step_weather)'''

            result = api.runtime.run_energyplus(state,
                                                [
                                                    '-w', self.energyplus_simulator.weather_file,
                                                    '-d', './out',
                                                    self.energyplus_simulator.idf_file
                                                ]
                                                )
            api.runtime.clear_callbacks()
            api.state_manager.reset_state(state)

            if result.returncode == 0:
                logger.info("EnergyPlus complete")
                self.energyplus_simulator._process_output_files()
                return True
            else:
                logger.error(f"EnergyPlus: {result.returncode}")
                logger.error(f"{result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("EnergyPlus Time out")
            return False
        except Exception as e:
            logger.error(f": {e}")
            return False


class DataStorage:
    """
    Data Storage Manager - Responsible for storing meteorological data and simulation results
    """

    def __init__(self, db_path: str = 'energyplus_weather.db'):

        self.MySQl_save_instanse()


    def storage_output(self):
        try:
            self.storages = self.instances.connect(OUTPUT_CONFIG)
        except Exception as e:
            print('Error connecting to inputs: ', e)

    {{initStorgae}}
'''    import MysqlCommunate
    def MySQl_save_instanse(self, result_data: Dict) -> bool:

        try:
            self.instances = MysqlCommunate()
            {{initStorage}}
            return True
        except:
            logger.error(f"{e}")
            return False'''

