import socket
from ApiRos import ApiRos

class MikroTikManager:
    def __init__(self, host, port=8728):
        self.host = host
        self.port = port
        self.connection = None
        self.api = None

    def connect(self, username, password):
        """Установка соединения с роутером"""
        try:
            self.connection = socket.socket()
            self.connection.connect((self.host, self.port))
            self.api = ApiRos(self.connection)
            
            if not self.api.login(username, password):
                raise ConnectionError("Ошибка аутентификации")
            return True
        except Exception as e:
            self.close()
            raise ConnectionError(f"Ошибка подключения: {str(e)}")

    def close(self):
        """Закрытие соединения"""
        if self.connection:
            try:
                self.connection.close()
            except:
                pass
        self.connection = None
        self.api = None

    def get_router_info(self):
        """Получение основной информации о роутере"""
        if not self.api:
            raise ConnectionError("Нет активного соединения")
        
        try:
            # Получаем системную информацию
            system_info = self.api.talk(["/system/resource/print"])[0][1]
            
            # Получаем идентификацию роутера
            identity = self.api.talk(["/system/identity/print"])[0][1].get('=name', 'N/A')
            
            # Получаем подробную информацию об интерфейсах
            interfaces = self._get_detailed_interfaces()
            
            return {
                "identity": identity,
                "cpu_load": system_info.get('=cpu-load', 'N/A'),
                "free_memory": system_info.get('=free-memory', 'N/A'),
                "uptime": system_info.get('=uptime', 'N/A'),
                "interfaces": interfaces
            }
        except Exception as e:
            raise RuntimeError(f"Ошибка получения информации: {str(e)}")

    def _get_detailed_interfaces(self):
        """Получение детальной информации о интерфейсах"""
        interfaces = []
        for iface in self.api.talk(["/interface/print"]):
            if iface[0] == '!re':
                interface_data = iface[1]
                interface = {
                    'name': interface_data.get('=name', 'N/A'),
                    'type': interface_data.get('=type', 'N/A'),
                    'mac_address': interface_data.get('=mac-address', 'N/A'),
                    'rx_byte': interface_data.get('=rx-byte', 'N/A'),
                    'tx_byte': interface_data.get('=tx-byte', 'N/A'),
                    'rx_packet': interface_data.get('=rx-packet', 'N/A'),
                    'tx_packet': interface_data.get('=tx-packet', 'N/A'),
                    'running': interface_data.get('=running', 'false') == 'true'
                }
                interfaces.append(interface)
        return interfaces

    def get_firewall_rules(self):
        """Получение списка правил фильтрации"""
        if not self.api:
            raise ConnectionError("Нет активного соединения")
        
        try:
            rules = []
            for rule in self.api.talk(["/ip/firewall/filter/print"]):
                if rule[0] == '=id':
                    rules.append({
                        'id': rule[1].get('=.id', 'N/A'),
                        'chain': rule[1].get('=chain', 'N/A'),
                        'dst_address': rule[1].get('=dst-address', 'N/A'),
                        'action': rule[1].get('=action', 'N/A'),
                        'comment': rule[1].get('=comment', '')
                    })
            return rules
        except Exception as e:
            raise RuntimeError(f"Ошибка получения правил: {str(e)}")

    def block_domain(self, domain):
        """Блокировка домена через добавление правила фильтрации"""
        if not self.api:
            raise ConnectionError("Нет активного соединения")
        
        try:
            ip = socket.gethostbyname(domain)
        except socket.gaierror:
            raise ValueError(f"Не удалось разрешить домен {domain} в IP")

        # Проверяем, не заблокирован ли уже этот IP
        rules = self.get_firewall_rules()
        for rule in rules:
            if rule['dst_address'] == ip and rule['action'] == 'drop':
                return False, f"Домен {domain} (IP: {ip}) уже заблокирован"

        # Добавляем правило блокировки
        try:
            self.api.talk([
                "/ip/firewall/filter/add",
                "=chain=forward",
                f"=dst-address={ip}",
                "=action=drop",
                f"=comment=Blocked: {domain}"
            ])
            return True, f"Домен {domain} (IP: {ip}) успешно заблокирован"
        except Exception as e:
            raise RuntimeError(f"Ошибка добавления правила: {str(e)}")

def print_interface_details(interfaces):
    """Функция для красивого вывода информации об интерфейсах"""
    print("\n=== Детальная информация об интерфейсах ===")
    for iface in interfaces:
        print(f"\nИнтерфейс: {iface['name']}")
        print(f"Тип: {iface['type']}")
        print(f"MAC-адрес: {iface['mac_address']}")
        print(f"Статус: {'Работает' if iface['running'] else 'Не работает'}")
        print("Трафик:")
        print(f"  Принято: {iface['rx_byte']} байт ({iface['rx_packet']} пакетов)")
        print(f"  Передано: {iface['tx_byte']} байт ({iface['tx_packet']} пакетов)")

def main():
    # Настройки подключения
    ROUTER_IP = '192.168.101.128'
    USERNAME = 'admin'
    PASSWORD = '180371'
    BLOCKED_DOMAINS = ["example.com", "test.com"]

    # Создаем экземпляр менеджера
    mikrotik = MikroTikManager(ROUTER_IP)

    try:
        # Подключаемся к роутеру
        mikrotik.connect(USERNAME, PASSWORD)
        print("Успешное подключение к роутеру")

        # Получаем информацию о роутере
        router_info = mikrotik.get_router_info()
        print("\n=== Основная информация о роутере ===")
        print(f"Имя: {router_info['identity']}")
        print(f"Загрузка CPU: {router_info['cpu_load']}%")
        print(f"Свободная память: {router_info['free_memory']}")
        print(f"Uptime: {router_info['uptime']}")

        # Выводим детальную информацию об интерфейсах
        print_interface_details(router_info['interfaces'])

        # Блокируем домены из списка
        print("\n=== Блокировка доменов ===")
        for domain in BLOCKED_DOMAINS:
            success, message = mikrotik.block_domain(domain)
            print(message)

    except Exception as e:
        print(f"\nОшибка: {str(e)}")
    finally:
        mikrotik.close()
        print("\nСоединение закрыто")

if __name__ == "__main__":
    main()