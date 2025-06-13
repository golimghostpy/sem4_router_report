import React from 'react';
import { useLocation } from 'react-router-dom';

const ReportPage = () => {
    const { state } = useLocation();
    
    if (!state) {
        window.location.href = '/';
        return null;
    }

    const { report = {}, blockedResults = [], status, message } = state;

    if (status === 'error') {
        return (
            <div className="report-container">
                <h1>Ошибка</h1>
                <p>{message}</p>
                <button onClick={() => window.location.href = '/'} className="back-btn">
                    Вернуться к форме
                </button>
            </div>
        );
    }

    return (
        <div className="report-container">
            <h1>Отчёт о состоянии роутера</h1>
            
            {report.name && (
                <div className="report-section">
                    <h2>Информация о роутере</h2>
                    <p><strong>Имя:</strong> {report.name}</p>
                    <p><strong>Модель:</strong> {report.model}</p>
                </div>
            )}

            {report.interfaces && (
                <div className="report-section">
                    <h2>Сетевые интерфейсы</h2>
                    <div className="interfaces-grid">
                        {report.interfaces.map((iface, index) => (
                            <div key={index} className="interface-card">
                                <h3>{iface.name}</h3>
                                <p><strong>Тип:</strong> {iface.type}</p>
                                <p><strong>MAC:</strong> {iface.mac_address}</p>
                                <p><strong>Статус:</strong> 
                                    <span className={iface.running ? 'status-up' : 'status-down'}>
                                        {iface.running ? 'Работает' : 'Не работает'}
                                    </span>
                                </p>
                                <div className="traffic-stats">
                                    <h4>Трафик:</h4>
                                    <p><strong>Принято:</strong> {iface.rx_byte} байт ({iface.rx_packet} пакетов)</p>
                                    <p><strong>Передано:</strong> {iface.tx_byte} байт ({iface.tx_packet} пакетов)</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {report.cpu_load && (
                <div className="report-section">
                    <h2>Загруженность системы</h2>
                    <p><strong>Загрузка CPU:</strong> {report.cpu_load}%</p>
                    <p><strong>Свободная память:</strong> {report.memory_usage}KBytes</p>
                </div>
            )}

            {report.encryption && (
                <div className="report-section">
                    <h2>Настройки шифрования</h2>
                    {report.encryption.map((wifi, index) => (
                        <div key={index} className="wifi-security">
                            <h3>{wifi.name}</h3>
                            <p><strong>Аутентификация:</strong> {wifi.authentication}</p>
                            <p><strong>Шифрование:</strong> {wifi.encryption}</p>
                        </div>
                    ))}
                </div>
            )}

            {report.blockedResources && (
                <div className="report-section">
                    <h2>Заблокированные ресурсы</h2>
                    <table className="blocked-resources">
                        <thead>
                            <tr>
                                <th>IP адрес</th>
                                <th>Комментарий</th>
                            </tr>
                        </thead>
                        <tbody>
                            {report.blockedResources.map((resource, index) => (
                                <tr key={index}>
                                    <td>{resource.dst_address}</td>
                                    <td>{resource.comment}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {blockedResults.length > 0 && (
                <div className="report-section">
                    <h2>Результаты блокировки</h2>
                    <ul className="blocking-results">
                        {blockedResults.map((result, index) => (
                            <li key={index} className={result.status === 'error' ? 'error' : 'success'}>
                                {result.domain} {result.ip && `(${result.ip})`} - 
                                {result.status === 'error' ? ` Ошибка: ${result.message}` : ' Успешно заблокирован'}
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            <div className="report-actions">
                <button onClick={() => window.print()} className="save-btn">
                    Сохранить отчет
                </button>
                <button onClick={() => window.location.href = '/'} className="back-btn">
                    Вернуться к форме
                </button>
            </div>
        </div>
    );
};

export default ReportPage;