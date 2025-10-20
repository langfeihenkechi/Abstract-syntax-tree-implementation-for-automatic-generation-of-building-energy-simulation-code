import requests


class httpCommunication:

    #通过正则化实现替换httpCommunicate()方法
    describe = f'''
    import {httpCommunication.__class__.__name__}
    def __get_{httpCommunication.__class__.__name__}_Instance(self):
        instance = {httpCommunication.__class__.__name__}()
        self.instances.append(instance)
    '''


    def __init__(self):
        pass
    def connect(self, config):
        try:
            self.name = config.get("name")
            self.base_url = config.get("url")
            self.timeout = config.get("timeout")
            response = requests.get(self.base_url, timeout=self.timeout)
        except Exception as e:
            print('Error:', e)
        return True
    def get_data(self, url):
        try:
            response = requests.get(self.base_url, timeout=self.timeout)
        except Exception as e:
            print('Error:', e)

        data = response.json()
        return data['data']
     def close(self):
         pass