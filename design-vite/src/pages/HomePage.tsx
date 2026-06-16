import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const HomePage: React.FC = () => {
    const navigate = useNavigate();
    const { user } = useAuth();
    const [selectedDocType, setSelectedDocType] = useState<string>('lab');
    const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
    const [isDragging, setIsDragging] = useState<boolean>(false);

    const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
        const files = event.target.files;
        if (files) {
            setUploadedFiles(prev => [...prev, ...Array.from(files)]);
        }
    };

    const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
        event.preventDefault();
        setIsDragging(false);
        const files = event.dataTransfer.files;
        if (files) {
            setUploadedFiles(prev => [...prev, ...Array.from(files)]);
        }
    };

    const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
        event.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = () => {
        setIsDragging(false);
    };

    const removeFile = (index: number) => {
        setUploadedFiles(prev => prev.filter((_, i) => i !== index));
    };

    const handleCreateReport = () => {
        if (uploadedFiles.length === 0) {
            alert('Пожалуйста, загрузите хотя бы один файл');
            return;
        }
        sessionStorage.setItem('docType', selectedDocType);
        sessionStorage.setItem('uploadedFiles', JSON.stringify(
            uploadedFiles.map(f => ({ name: f.name, size: f.size, type: f.type }))
        ));
        navigate('/wizard');
    };

    /*const getDocTypeName = () => {
        switch (selectedDocType) {
            case 'lab': return 'лабораторная работа';
            case 'report': return 'отчёт';
            case 'coursework': return 'курсовая работа';
            default: return 'документ';
        }
    };*/

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-50 to-purple-50">
            <div className="bg-white shadow-sm border-b border-purple-100">
                <div className="max-w-5xl mx-auto px-4 py-6">
                    <h1 className="text-3xl font-bold text-gray-800">Оформлятор AI</h1>
                    <p className="text-gray-500 mt-1">Создавайте отчёты, лабораторные и курсовые работы за минуты</p>
                </div>
            </div>

            <div className="max-w-4xl mx-auto px-4 py-10">
                <div className="max-w-4xl mx-auto px-4 py-10">
                    {/* Приветствие пользователя */}
                    <div className="mb-6">
                        <h2 className="text-2xl font-bold text-gray-800">
                            Добро пожаловать, {user?.name || 'пользователь'}!
                        </h2>
                        <p className="text-gray-500">Создайте новый документ или продолжите работу над предыдущими</p>
                    </div>
                </div>
                <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
                    <div className="bg-gradient-to-r from-purple-700 to-purple-500 px-6 py-4">
                        <h2 className="text-xl font-semibold text-white">Создать новый проект</h2>
                        <p className="text-purple-100 text-sm">Загрузите файлы и выберите тип документа</p>
                    </div>

                    <div className="p-6 space-y-6">
                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-2">
                                Тип документа
                            </label>
                            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                                <button
                                    onClick={() => setSelectedDocType('lab')}
                                    className={`
                    text-left p-4 rounded-xl border-2 transition-all
                    ${selectedDocType === 'lab'
                                            ? 'border-purple-500 bg-purple-50 ring-2 ring-purple-200'
                                            : 'border-gray-200 hover:border-purple-300 hover:bg-purple-50'
                                        }
                  `}
                                >
                                    <div className="font-semibold text-gray-800">Лабораторная работа</div>
                                    <div className="text-xs text-gray-500 mt-1">Структура: цель, оборудование, ход работы, выводы</div>
                                </button>
                                <button
                                    onClick={() => setSelectedDocType('report')}
                                    className={`
                    text-left p-4 rounded-xl border-2 transition-all
                    ${selectedDocType === 'report'
                                            ? 'border-purple-500 bg-purple-50 ring-2 ring-purple-200'
                                            : 'border-gray-200 hover:border-purple-300 hover:bg-purple-50'
                                        }
                  `}
                                >
                                    <div className="font-semibold text-gray-800">Отчёт</div>
                                    <div className="text-xs text-gray-500 mt-1">Структура: введение, анализ, результаты, заключение</div>
                                </button>
                                <button
                                    onClick={() => setSelectedDocType('coursework')}
                                    className={`
                    text-left p-4 rounded-xl border-2 transition-all
                    ${selectedDocType === 'coursework'
                                            ? 'border-purple-500 bg-purple-50 ring-2 ring-purple-200'
                                            : 'border-gray-200 hover:border-purple-300 hover:bg-purple-50'
                                        }
                  `}
                                >
                                    <div className="font-semibold text-gray-800">Курсовая работа</div>
                                    <div className="text-xs text-gray-500 mt-1">Структура: введение, главы, заключение, библиография</div>
                                </button>
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-2">
                                Загрузите файлы
                            </label>
                            <div
                                onDrop={handleDrop}
                                onDragOver={handleDragOver}
                                onDragLeave={handleDragLeave}
                                className={`
                  border-2 border-dashed rounded-xl p-8 text-center transition-all cursor-pointer
                  ${isDragging
                                        ? 'border-purple-500 bg-purple-50'
                                        : 'border-gray-300 bg-gray-50 hover:bg-purple-50'
                                    }
                `}
                                onClick={() => document.getElementById('fileInput')?.click()}
                            >
                                <input
                                    id="fileInput"
                                    type="file"
                                    multiple
                                    className="hidden"
                                    onChange={handleFileUpload}
                                />
                                <svg className="w-10 h-10 mx-auto mb-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                                </svg>
                                <p className="text-gray-600">
                                    {isDragging ? 'Отпустите файлы для загрузки' : 'Перетащите файлы сюда или кликните для выбора'}
                                </p>
                                <p className="text-gray-400 text-sm mt-1">Поддерживаются: .docx, .jpg, .png, .pdf</p>
                            </div>

                            {uploadedFiles.length > 0 && (
                                <div className="mt-4 space-y-2">
                                    <p className="text-sm font-medium text-gray-700">Загружено файлов: {uploadedFiles.length}</p>
                                    <div className="max-h-40 overflow-y-auto space-y-1">
                                        {uploadedFiles.map((file, idx) => (
                                            <div key={idx} className="flex items-center justify-between bg-gray-100 rounded-lg px-3 py-2 text-sm">
                                                <span className="text-gray-700 truncate flex-1">{file.name}</span>
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        removeFile(idx);
                                                    }}
                                                    className="text-purple-600 hover:text-purple-800 ml-2"
                                                >
                                                    Удалить
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>

                        <div className="pt-4">
                            <button
                                onClick={handleCreateReport}
                                className="w-full bg-gradient-to-r from-purple-600 to-purple-500 text-white py-3 rounded-xl font-semibold text-lg shadow-lg hover:from-purple-700 hover:to-purple-600 transition-all transform hover:scale-[1.02]"
                            >
                                Создать отчёт
                            </button>
                            <p className="text-center text-gray-400 text-xs mt-3">
                                Искусственный интеллект проанализирует файлы и сгенерирует структурированный документ
                            </p>
                        </div>
                    </div>
                </div>

                <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="bg-white rounded-xl p-5 shadow-md text-center hover:shadow-lg transition-shadow">
                        <div className="text-3xl mb-2 text-purple-600">1</div>
                        <h3 className="font-semibold text-gray-800">Загрузите файлы</h3>
                        <p className="text-sm text-gray-500 mt-1">Исходные данные, фото, сканы, таблицы</p>
                    </div>
                    <div className="bg-white rounded-xl p-5 shadow-md text-center hover:shadow-lg transition-shadow">
                        <div className="text-3xl mb-2 text-purple-600">2</div>
                        <h3 className="font-semibold text-gray-800">Выберите тип</h3>
                        <p className="text-sm text-gray-500 mt-1">Лабораторная, отчёт или курсовая</p>
                    </div>
                    <div className="bg-white rounded-xl p-5 shadow-md text-center hover:shadow-lg transition-shadow">
                        <div className="text-3xl mb-2 text-purple-600">3</div>
                        <h3 className="font-semibold text-gray-800">Получите результат</h3>
                        <p className="text-sm text-gray-500 mt-1">Готовый документ с разметкой и иллюстрациями</p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default HomePage;