import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const RouterForm = () => {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        host: '192.168.88.1',
        login: '',
        password: '',
    });
    const [selectedOptions, setSelectedOptions] = useState({
        name: false,
        interfaces: false,
        load: false,
        encryption: false,
        blockedResources: false,
    });
    const [domainsToBlock, setDomainsToBlock] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData({ ...formData, [name]: value });
    };

    const handleToggleChange = (name) => {
        setSelectedOptions({ ...selectedOptions, [name]: !selectedOptions[name] });
    };

    const handleDomainsChange = (e) => {
        setDomainsToBlock(e.target.value);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setError(null);

        try {
            const domainsArray = domainsToBlock.split('\n')
                .map(domain => domain.trim())
                .filter(domain => domain.length > 0);

            const response = await fetch('http://localhost:5000/api/report', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    host: formData.host,
                    login: formData.login,
                    password: formData.password,
                    options: selectedOptions,
                    domains_to_block: domainsArray
                }),
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || 'Ошибка при генерации отчета');
            }

            navigate('/report', { state: data });
        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="form-container">
            <h1>Настройка отчёта для роутера</h1>
            {error && <div className="error-message">{error}</div>}
            <form onSubmit={handleSubmit}>
                <div className="form-group">
                    <label>IP адрес роутера:</label>
                    <input
                        type="text"
                        name="host"
                        value={formData.host}
                        onChange={handleInputChange}
                        required
                    />
                </div>
                <div className="form-group">
                    <label>Логин:</label>
                    <input
                        type="text"
                        name="login"
                        value={formData.login}
                        onChange={handleInputChange}
                    />
                </div>
                <div className="form-group">
                    <label>Пароль:</label>
                    <input
                        type="password"
                        name="password"
                        value={formData.password}
                        onChange={handleInputChange}
                    />
                </div>

                <div className="options-group">
                    <h3>Выберите данные для отчёта:</h3>
                    {Object.entries(selectedOptions).map(([key, value]) => (
                        <div key={key} className="toggle-switch">
                            <label>
                                {key === 'name' && 'Название роутера'}
                                {key === 'interfaces' && 'Сетевые интерфейсы'}
                                {key === 'load' && 'Загруженность CPU/RAM'}
                                {key === 'encryption' && 'Настройки шифрования'}
                                {key === 'blockedResources' && 'Заблокированные ресурсы'}
                                <input
                                    type="checkbox"
                                    checked={value}
                                    onChange={() => handleToggleChange(key)}
                                    className="toggle-input"
                                />
                                <span className="toggle-slider"></span>
                            </label>
                        </div>
                    ))}
                </div>

                <div className="form-group">
                    <label>Домены для блокировки (по одному на строку):</label>
                    <textarea
                        name="domainsToBlock"
                        value={domainsToBlock}
                        onChange={handleDomainsChange}
                        rows={4}
                        placeholder="example.com"
                    />
                </div>

                <button type="submit" className="submit-btn" disabled={isLoading}>
                    {isLoading ? 'Формирование отчета...' : 'Сформировать отчёт'}
                </button>
            </form>
        </div>
    );
};

export default RouterForm;