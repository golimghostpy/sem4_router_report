from flask import Flask, request, jsonify
from flask_cors import CORS
import socket
from ApiRos import ApiRos

app = Flask(__name__)
CORS(app)

DEFAULT_HOST = '192.168.88.1'
DEFAULT_PORT = 8728
NA_VALUE = 'N/A'

class MikroTikManager:
    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT):
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

    def _get_system_info(self):
        """Получение системной информации"""
        if not self.api:
            raise ConnectionError("Нет активного соединения")
        return self.api.talk(["/system/resource/print"])[0][1]

    def _get_identity(self):
        """Получение идентификатора роутера"""
        return self.api.talk(["/system/identity/print"])[0][1].get('=name', NA_VALUE)

    def _get_interfaces(self):
        """Получение информации о интерфейсах"""
        interfaces = []
        for iface in self.api.talk(["/interface/print"]):
            if iface[0] == '!re':
                interface_data = iface[1]
                interfaces.append({
                    'name': interface_data.get('=name', NA_VALUE),
                    'type': interface_data.get('=type', NA_VALUE),
                    'mac_address': interface_data.get('=mac-address', NA_VALUE),
                    'rx_byte': interface_data.get('=rx-byte', NA_VALUE),
                    'tx_byte': interface_data.get('=tx-byte', NA_VALUE),
                    'rx_packet': interface_data.get('=rx-packet', NA_VALUE),
                    'tx_packet': interface_data.get('=tx-packet', NA_VALUE),
                    'running': interface_data.get('=running', 'false') == 'true'
                })
        return interfaces

    def _get_wifi_security(self):
        """Получение настроек безопасности Wi-Fi"""
        wifi_security = []
        for wifi in self.api.talk(["/interface/wireless/security/print"]):
            if wifi[0] == '!re':
                wifi_security.append({
                    'name': wifi[1].get('=name', NA_VALUE),
                    'authentication': wifi[1].get('=authentication-types', NA_VALUE),
                    'encryption': wifi[1].get('=encryption', NA_VALUE)
                })
        return wifi_security

    def _get_blocked_resources(self):
        """Получение заблокированных ресурсов"""
        blocked = []
        for rule in self.api.talk(["/ip/firewall/filter/print"]):
            if rule[0] == '!re' and rule[1].get('=action') == 'drop':
                blocked.append({
                    'dst_address': rule[1].get('=dst-address', NA_VALUE),
                    'comment': rule[1].get('=comment', '')
                })
        return blocked

    def block_domain(self, domain):
        """Блокировка домена через добавление правила фильтрации"""
        if not self.api:
            raise ConnectionError("Нет активного соединения")
        
        try:
            ip = socket.gethostbyname(domain)
        except socket.gaierror:
            raise ValueError(f"Домен {domain} не существует")

        for rule in self.api.talk(["/ip/firewall/filter/print"]):
            if rule[0] == '!re' and rule[1].get('=dst-address') == ip and rule[1].get('=action') == 'drop':
                raise ValueError(f"Домен {domain} (IP: {ip}) уже заблокирован")

        try:
            self.api.talk([
                "/ip/firewall/filter/add",
                "=chain=forward",
                f"=dst-address={ip}",
                "=action=drop",
                f"=comment=Blocked: {domain}"
            ])
            return True, ip
        except Exception as e:
            raise RuntimeError(f"Ошибка добавления правила: {str(e)}")

@app.route('/api/report', methods=['POST'])
def generate_report():
    try:
        data = request.get_json()
        options = data.get('options', {})
        domains_to_block = data.get('domains_to_block', [])
        username = data.get('login')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({"status": "error", "message": "Username and password are required"}), 400
        
        mikrotik = MikroTikManager(data.get('host', DEFAULT_HOST))
        
        try:
            if not mikrotik.connect(username, password):
                return jsonify({"status": "error", "message": "Authentication failed"}), 401
            
            report_data = {}
            system_info = mikrotik._get_system_info()
            
            if options.get('name'):
                report_data['name'] = mikrotik._get_identity()
                report_data['model'] = system_info.get('=board-name', NA_VALUE)
            
            if options.get('interfaces'):
                report_data['interfaces'] = mikrotik._get_interfaces()
            
            if options.get('load'):
                report_data['cpu_load'] = system_info.get('=cpu-load', NA_VALUE)
                report_data['memory_usage'] = int(system_info.get('=free-memory', NA_VALUE)) // 8 // 1024
            
            if options.get('encryption'):
                report_data['encryption'] = mikrotik._get_wifi_security()
            
            blocked_results = []
            for domain in domains_to_block:
                try:
                    success, ip = mikrotik.block_domain(domain)
                    blocked_results.append({
                        'domain': domain,
                        'ip': ip,
                        'status': 'blocked',
                        'message': f"Домен {domain} (IP: {ip}) успешно заблокирован"
                    })
                except ValueError as e:
                    blocked_results.append({
                        'domain': domain,
                        'status': 'error',
                        'message': str(e)
                    })
                except Exception as e:
                    blocked_results.append({
                        'domain': domain,
                        'status': 'error',
                        'message': f"Ошибка при блокировке домена: {str(e)}"
                    })
            
            if options.get('blockedResources'):
                report_data['blockedResources'] = mikrotik._get_blocked_resources()
            
            return jsonify({
                "status": "success",
                "report": report_data,
                "blockedResults": blocked_results
            })
        
        finally:
            mikrotik.close()
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)