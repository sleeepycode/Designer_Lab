import React, { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import axios from 'axios';

interface User {
    id: string;
    email: string;
    name: string;
    group?: string;
    role: 'student' | 'teacher' | 'admin';
    avatar?: string;
}

interface AuthContextType {
    user: User | null;
    isLoading: boolean;
    isAuthenticated: boolean;
    login: (email: string, password: string) => Promise<void>;
    register: (name: string, email: string, password: string, group?: string) => Promise<void>;
    logout: () => void;
    updateUser: (data: Partial<User>) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

interface AuthProviderProps {
    children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(true);

    // Проверка сохранённой сессии при загрузке
    useEffect(() => {
        const checkAuth = async () => {
            const token = localStorage.getItem('accessToken');
            const savedUser = localStorage.getItem('user');

            if (token && savedUser) {
                try {
                    // Настройка заголовка для всех запросов
                    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
                    setUser(JSON.parse(savedUser));
                } catch (error) {
                    console.error('Ошибка восстановления сессии:', error);
                    localStorage.removeItem('accessToken');
                    localStorage.removeItem('user');
                }
            }
            setIsLoading(false);
        };

        checkAuth();
    }, []);

    // Функция входа
    const login = async (email: string, password: string) => {
        setIsLoading(true);
        try {
            // Имитация API-запроса
            // const response = await axios.post('http://localhost:3000/api/auth/login', { email, password });

            // Демо-данные (заменить на реальный API)
            await new Promise(resolve => setTimeout(resolve, 1000));

            if (email === 'demo@example.com' && password === '123456') {
                const mockUser: User = {
                    id: '1',
                    email: 'demo@example.com',
                    name: 'Иван Петров',
                    group: 'БПИ2404',
                    role: 'student',
                };
                const mockToken = 'mock-jwt-token-' + Date.now();

                setUser(mockUser);
                localStorage.setItem('accessToken', mockToken);
                localStorage.setItem('user', JSON.stringify(mockUser));
                axios.defaults.headers.common['Authorization'] = `Bearer ${mockToken}`;
            } else {
                throw new Error('Неверный email или пароль');
            }
        } catch (error) {
            throw error;
        } finally {
            setIsLoading(false);
        }
    };

    // Функция регистрации
    const register = async (name: string, email: string, _password: string, group?: string) => {
        setIsLoading(true);
        try {
            // Имитация API-запроса
            // const response = await axios.post('http://localhost:3000/api/auth/register', { name, email, password, group });

            await new Promise(resolve => setTimeout(resolve, 1000));

            const mockUser: User = {
                id: Date.now().toString(),
                email,
                name,
                group,
                role: 'student',
            };
            const mockToken = 'mock-jwt-token-' + Date.now();

            setUser(mockUser);
            localStorage.setItem('accessToken', mockToken);
            localStorage.setItem('user', JSON.stringify(mockUser));
            axios.defaults.headers.common['Authorization'] = `Bearer ${mockToken}`;
        } catch (error) {
            throw error;
        } finally {
            setIsLoading(false);
        }
    };

    // Выход из системы
    const logout = () => {
        setUser(null);
        localStorage.removeItem('accessToken');
        localStorage.removeItem('user');
        delete axios.defaults.headers.common['Authorization'];
    };

    // Обновление данных пользователя
    const updateUser = (data: Partial<User>) => {
        if (user) {
            const updatedUser = { ...user, ...data };
            setUser(updatedUser);
            localStorage.setItem('user', JSON.stringify(updatedUser));
        }
    };

    return (
        <AuthContext.Provider
            value={{
                user,
                isLoading,
                isAuthenticated: !!user,
                login,
                register,
                logout,
                updateUser,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
};