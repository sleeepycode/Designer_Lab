import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios, { type AxiosInstance } from 'axios';

type Step = 'title' | 'analysis' | 'images' | 'result';

interface TitlePageData {
    university: string;
    department: string;
    subject: string;
    theme: string;
    studentName: string;
    group: string;
    teacherName: string;
    city: string;
    year: string;
}

interface ImageData {
    id: string;
    name: string;
    previewUrl: string;
    type: 'graph' | 'table' | 'diagram' | 'photo' | 'formula';
    recognizedText: string;
    suggestedPlace: string;
    suggestedCaption: string;
    customCaption: string;
    isApplied: boolean;
    isSkipped: boolean;
}

// Тип для истории проектов
interface ProjectHistory {
    id: string;
    createdAt: string;
    docType: string;
    studentName: string;
    group: string;
    university: string;
    imagesCount: number;
    filesCount: number;
    status: 'completed' | 'draft';
}

interface ApiResponse {
    success: boolean;
    message: string;
    documentId?: string;
    data?: any;
}

const apiClient: AxiosInstance = axios.create({
    baseURL: 'http://localhost:3000/api',
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json',
    },
});

const WizardPage: React.FC = () => {
    const navigate = useNavigate();
    const [currentStep, setCurrentStep] = useState<Step>('title');
    const [docType, setDocType] = useState<string>('');
    const [uploadedFiles, setUploadedFiles] = useState<{ name: string; size: number; type: string }[]>([]);

    const [titleData, setTitleData] = useState<TitlePageData>({
        university: 'МТУСИ',
        department: '',
        subject: '',
        theme: '',
        studentName: '',
        group: '',
        teacherName: '',
        city: 'Москва',
        year: new Date().getFullYear().toString(),
    });

    const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
    const [submitError, setSubmitError] = useState<string | null>(null);
    const [submitSuccess, setSubmitSuccess] = useState<boolean>(false);

    const [analysisStatus, setAnalysisStatus] = useState<string>('ожидание');
    const [analysisProgress, setAnalysisProgress] = useState<number>(0);

    const [images, setImages] = useState<ImageData[]>([]);
    const [editingCaptionId, setEditingCaptionId] = useState<string | null>(null);
    const [tempCaption, setTempCaption] = useState<string>('');

    // Состояние для истории проектов
    const [projectHistory, setProjectHistory] = useState<ProjectHistory[]>([]);
    const [showHistory, setShowHistory] = useState<boolean>(false);
    const [isDownloading, setIsDownloading] = useState<boolean>(false);

    useEffect(() => {
        const savedDocType = sessionStorage.getItem('docType');
        const savedFiles = sessionStorage.getItem('uploadedFiles');

        if (savedDocType) setDocType(savedDocType);
        if (savedFiles) setUploadedFiles(JSON.parse(savedFiles));

        initializeImages();
        loadProjectHistory();
    }, []);

    const initializeImages = () => {
        const mockImages: ImageData[] = [
            {
                id: '1',
                name: 'график_зависимости.png',
                previewUrl: 'https://via.placeholder.com/120x80/9333EA/white?text=Graph',
                type: 'graph',
                recognizedText: 'Зависимость температуры от времени. По оси X: время (с), по оси Y: температура (°C).',
                suggestedPlace: 'После раздела 2.1 «Теоретические основы»',
                suggestedCaption: 'Рисунок 2.1 - Зависимость температуры от времени',
                customCaption: '',
                isApplied: false,
                isSkipped: false,
            },
            {
                id: '2',
                name: 'таблица_результатов.jpg',
                previewUrl: 'https://via.placeholder.com/120x80/10B981/white?text=Table',
                type: 'table',
                recognizedText: 'Таблица результатов измерений. Номер опыта: 1, 2, 3. Значения: 10.2, 10.5, 10.3.',
                suggestedPlace: 'После раздела 3.2 «Результаты измерений»',
                suggestedCaption: 'Таблица 1 - Результаты измерений',
                customCaption: '',
                isApplied: false,
                isSkipped: false,
            },
            {
                id: '3',
                name: 'схема_установки.png',
                previewUrl: 'https://via.placeholder.com/120x80/3B82F6/white?text=Diagram',
                type: 'diagram',
                recognizedText: 'Схема экспериментальной установки. Компоненты: источник питания, измерительный прибор.',
                suggestedPlace: 'После раздела 2.0 «Экспериментальная установка»',
                suggestedCaption: 'Рисунок 2 - Схема экспериментальной установки',
                customCaption: '',
                isApplied: false,
                isSkipped: false,
            },
            {
                id: '4',
                name: 'фото_эксперимента.jpg',
                previewUrl: 'https://via.placeholder.com/120x80/EF4444/white?text=Photo',
                type: 'photo',
                recognizedText: 'Фотография экспериментального стенда.',
                suggestedPlace: 'После раздела 2.0 «Экспериментальная установка»',
                suggestedCaption: 'Фото 1 - Экспериментальный стенд',
                customCaption: '',
                isApplied: false,
                isSkipped: false,
            },
        ];
        setImages(mockImages);
    };

    // Загрузка истории проектов из localStorage
    const loadProjectHistory = () => {
        const saved = localStorage.getItem('projectHistory');
        if (saved) {
            setProjectHistory(JSON.parse(saved));
        } else {
            // Демо-данные для истории
            const demoHistory: ProjectHistory[] = [
                {
                    id: 'proj_001',
                    createdAt: '2026-04-28T10:30:00',
                    docType: 'lab',
                    studentName: 'Анна Смирнова',
                    group: 'БПИ2404',
                    university: 'МТУСИ',
                    imagesCount: 3,
                    filesCount: 2,
                    status: 'completed',
                },
                {
                    id: 'proj_002',
                    createdAt: '2026-04-25T14:15:00',
                    docType: 'report',
                    studentName: 'Дмитрий Козлов',
                    group: 'БПИ2404',
                    university: 'МТУСИ',
                    imagesCount: 5,
                    filesCount: 4,
                    status: 'completed',
                },
            ];
            setProjectHistory(demoHistory);
            localStorage.setItem('projectHistory', JSON.stringify(demoHistory));
        }
    };

    // Сохранение текущего проекта в историю
    const saveCurrentProjectToHistory = () => {
        const appliedImages = images.filter(img => img.isApplied);
        const newProject: ProjectHistory = {
            id: `proj_${Date.now()}`,
            createdAt: new Date().toISOString(),
            docType: docType,
            studentName: titleData.studentName,
            group: titleData.group,
            university: titleData.university,
            imagesCount: appliedImages.length,
            filesCount: uploadedFiles.length,
            status: 'completed',
        };

        const updatedHistory = [newProject, ...projectHistory].slice(0, 10); // Храним последние 10 проектов
        setProjectHistory(updatedHistory);
        localStorage.setItem('projectHistory', JSON.stringify(updatedHistory));
    };

    // Получение читаемого названия изменений
    const getAppliedChanges = () => {
        const changes: string[] = [];

        changes.push(`Тип документа: ${getDocTypeName()}`);
        changes.push(`Студент: ${titleData.studentName} (${titleData.group})`);
        changes.push(`Университет: ${titleData.university}`);

        if (titleData.theme) changes.push(`Тема: ${titleData.theme}`);
        if (titleData.subject) changes.push(`Дисциплина: ${titleData.subject}`);
        if (titleData.teacherName) changes.push(`Преподаватель: ${titleData.teacherName}`);

        const appliedImages = images.filter(img => img.isApplied);
        changes.push(`Добавлено изображений: ${appliedImages.length}`);

        appliedImages.forEach(img => {
            const caption = img.customCaption || img.suggestedCaption;
            changes.push(`  - ${img.name} → ${caption}`);
        });

        changes.push(`Всего обработано файлов: ${uploadedFiles.length}`);

        return changes;
    };

    // Симуляция скачивания документа
    const handleDownload = async () => {
        setIsDownloading(true);

        // Имитируем задержку скачивания
        await new Promise(resolve => setTimeout(resolve, 1500));

        // Создаём JSON-представление документа
        const documentData = {
            title: getDocTypeName(),
            student: titleData.studentName,
            group: titleData.group,
            university: titleData.university,
            department: titleData.department,
            subject: titleData.subject,
            theme: titleData.theme,
            teacher: titleData.teacherName,
            year: titleData.year,
            city: titleData.city,
            images: images.filter(img => img.isApplied).map(img => ({
                name: img.name,
                caption: img.customCaption || img.suggestedCaption,
                place: img.suggestedPlace,
            })),
            createdAt: new Date().toISOString(),
        };

        const blob = new Blob([JSON.stringify(documentData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${getDocTypeName().toLowerCase().replace(/\s/g, '_')}_${titleData.group}_${Date.now()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        setIsDownloading(false);
        alert('Документ успешно скачан!');
    };

    const submitTitlePageToBackend = async (data: TitlePageData) => {
        setIsSubmitting(true);
        setSubmitError(null);
        setSubmitSuccess(false);

        try {
            const response = await apiClient.post<ApiResponse>('/title-page', {
                ...data,
                documentType: docType,
                files: uploadedFiles,
                timestamp: new Date().toISOString(),
            });

            if (response.data.success) {
                setSubmitSuccess(true);
                if (response.data.documentId) {
                    sessionStorage.setItem('documentId', response.data.documentId);
                }
                return { success: true };
            } else {
                throw new Error(response.data.message || 'Неизвестная ошибка');
            }
        } catch (error) {
            console.error('Ошибка при отправке:', error);
            setSubmitError('Сервер не отвечает. Данные сохранены локально.');
            return { success: false };
        } finally {
            setIsSubmitting(false);
        }
    };

    const goToNextStep = async () => {
        switch (currentStep) {
            case 'title':
                if (!titleData.studentName || !titleData.group || !titleData.university) {
                    alert('Пожалуйста, заполните обязательные поля');
                    return;
                }
                await submitTitlePageToBackend(titleData);
                setCurrentStep('analysis');
                startAnalysis();
                break;
            case 'analysis':
                if (analysisStatus === 'завершено') {
                    setCurrentStep('images');
                }
                break;
            case 'images':
                const hasAppliedImages = images.some(img => img.isApplied);
                if (hasAppliedImages) {
                    saveCurrentProjectToHistory();
                    setCurrentStep('result');
                } else {
                    alert('Пожалуйста, примените хотя бы одно изображение');
                }
                break;
            default:
                break;
        }
    };

    const startAnalysis = () => {
        setAnalysisStatus('обработка');
        setAnalysisProgress(0);

        const interval = setInterval(() => {
            setAnalysisProgress(prev => {
                if (prev >= 100) {
                    clearInterval(interval);
                    setAnalysisStatus('завершено');
                    return 100;
                }
                return prev + 10;
            });
        }, 300);
    };

    const getTypeLabel = (type: ImageData['type']) => {
        const labels = { graph: 'График', table: 'Таблица', diagram: 'Схема', photo: 'Фото', formula: 'Формула' };
        return labels[type];
    };

    const getTypeColor = (type: ImageData['type']) => {
        const colors = {
            graph: 'bg-blue-100 text-blue-700',
            table: 'bg-green-100 text-green-700',
            diagram: 'bg-purple-100 text-purple-700',
            photo: 'bg-yellow-100 text-yellow-700',
            formula: 'bg-orange-100 text-orange-700',
        };
        return colors[type];
    };

    const handleApplyImage = (id: string) => {
        setImages(prev => prev.map(img =>
            img.id === id ? { ...img, isApplied: true, isSkipped: false } : img
        ));
    };

    const handleSkipImage = (id: string) => {
        setImages(prev => prev.map(img =>
            img.id === id ? { ...img, isSkipped: true, isApplied: false } : img
        ));
    };

    const handleApplyAll = () => {
        setImages(prev => prev.map(img => ({ ...img, isApplied: true, isSkipped: false })));
    };

    const handleSkipAll = () => {
        if (confirm('Вы уверены, что хотите пропустить все изображения?')) {
            setImages(prev => prev.map(img => ({ ...img, isSkipped: true, isApplied: false })));
        }
    };

    const startEditCaption = (id: string, currentCaption: string) => {
        setEditingCaptionId(id);
        setTempCaption(currentCaption);
    };

    const saveCaption = (id: string) => {
        setImages(prev => prev.map(img =>
            img.id === id ? { ...img, customCaption: tempCaption } : img
        ));
        setEditingCaptionId(null);
        setTempCaption('');
    };

    const cancelEditCaption = () => {
        setEditingCaptionId(null);
        setTempCaption('');
    };

    const getDisplayCaption = (img: ImageData) => img.customCaption || img.suggestedCaption;
    const getStatusBadge = (img: ImageData) => {
        if (img.isApplied) return <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full">Применено</span>;
        if (img.isSkipped) return <span className="text-xs bg-gray-100 text-gray-500 px-2 py-1 rounded-full">Пропущено</span>;
        return <span className="text-xs bg-yellow-100 text-yellow-700 px-2 py-1 rounded-full">Ожидает</span>;
    };

    const getDocTypeName = () => {
        switch (docType) {
            case 'lab': return 'Лабораторная работа';
            case 'report': return 'Отчёт';
            case 'coursework': return 'Курсовая работа';
            default: return 'Документ';
        }
    };

    const formatDate = (dateString: string) => {
        const date = new Date(dateString);
        return date.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
    };

    const isFieldInvalid = (field: keyof TitlePageData, required: boolean = true): boolean => {
        if (!required) return false;
        return !titleData[field] && titleData[field] !== '';
    };

    // Шаг 1: Титульный лист (сокращён для краткости)
    const TitleStep = () => (
        <div className="space-y-5">
            <div className="bg-purple-50 rounded-lg p-3">
                <p className="text-sm text-purple-800">Тип документа: {getDocTypeName()} | Файлов: {uploadedFiles.length}</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">Университет *</label>
                    <input type="text" value={titleData.university} onChange={(e) => setTitleData({ ...titleData, university: e.target.value })} className={`w-full px-4 py-2 border rounded-lg ${isFieldInvalid('university') ? 'border-red-400 bg-red-50' : 'border-gray-300'}`} />
                </div>
                <div><label className="block text-sm font-medium text-gray-700 mb-1">Студент *</label><input type="text" value={titleData.studentName} onChange={(e) => setTitleData({ ...titleData, studentName: e.target.value })} className={`w-full px-4 py-2 border rounded-lg ${isFieldInvalid('studentName') ? 'border-red-400 bg-red-50' : 'border-gray-300'}`} /></div>
                <div><label className="block text-sm font-medium text-gray-700 mb-1">Группа *</label><input type="text" value={titleData.group} onChange={(e) => setTitleData({ ...titleData, group: e.target.value })} className={`w-full px-4 py-2 border rounded-lg ${isFieldInvalid('group') ? 'border-red-400 bg-red-50' : 'border-gray-300'}`} /></div>
                <div><label className="block text-sm font-medium text-gray-700 mb-1">Тема работы</label><input type="text" value={titleData.theme} onChange={(e) => setTitleData({ ...titleData, theme: e.target.value })} className="w-full px-4 py-2 border border-gray-300 rounded-lg" /></div>
                <div><label className="block text-sm font-medium text-gray-700 mb-1">Преподаватель</label><input type="text" value={titleData.teacherName} onChange={(e) => setTitleData({ ...titleData, teacherName: e.target.value })} className="w-full px-4 py-2 border border-gray-300 rounded-lg" /></div>
                <div><label className="block text-sm font-medium text-gray-700 mb-1">Дисциплина</label><input type="text" value={titleData.subject} onChange={(e) => setTitleData({ ...titleData, subject: e.target.value })} className="w-full px-4 py-2 border border-gray-300 rounded-lg" /></div>
            </div>
            {submitSuccess && <div className="bg-green-50 p-3 rounded-lg"><p className="text-sm text-green-700">✓ Данные отправлены</p></div>}
            {submitError && <div className="bg-red-50 p-3 rounded-lg"><p className="text-sm text-red-700">{submitError}</p></div>}
        </div>
    );

    // Шаг 2: Анализ
    const AnalysisStep = () => (
        <div className="bg-gray-50 rounded-xl p-6 text-center">
            {analysisStatus === 'ожидание' && <p className="text-gray-500">Нажмите «Далее» для начала анализа</p>}
            {analysisStatus === 'обработка' && (
                <div>
                    <div className="flex justify-center mb-4"><svg className="w-12 h-12 text-purple-600 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path></svg></div>
                    <p className="text-gray-700 font-medium">ИИ анализирует ваши файлы...</p>
                    <div className="mt-4 w-full bg-gray-200 rounded-full h-2"><div className="bg-purple-600 h-2 rounded-full transition-all duration-300" style={{ width: `${analysisProgress}%` }}></div></div>
                    <p className="text-sm text-gray-500 mt-2">{analysisProgress}%</p>
                </div>
            )}
            {analysisStatus === 'завершено' && (
                <div><svg className="w-12 h-12 text-green-500 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg><p className="text-green-600 font-medium">Анализ завершён!</p><p className="text-sm text-gray-500 mt-1">Найдено {images.length} изображений</p></div>
            )}
        </div>
    );

    // Шаг 3: Изображения
    const ImagesStep = () => {
        const stats = { total: images.length, applied: images.filter(i => i.isApplied).length, skipped: images.filter(i => i.isSkipped).length };
        return (
            <div className="space-y-6">
                <div className="flex items-center justify-between flex-wrap gap-3 pb-3 border-b">
                    <div className="flex gap-4 text-sm"><span>Всего: {stats.total}</span><span className="text-green-600">Применено: {stats.applied}</span><span className="text-gray-400">Пропущено: {stats.skipped}</span></div>
                    <div className="flex gap-2"><button onClick={handleApplyAll} className="px-3 py-1 text-sm bg-purple-600 text-white rounded-lg">Применить все</button><button onClick={handleSkipAll} className="px-3 py-1 text-sm border border-gray-300 rounded-lg">Пропустить все</button></div>
                </div>
                <div className="space-y-4 max-h-96 overflow-y-auto">
                    {images.map((img) => (
                        <div key={img.id} className={`border rounded-lg p-4 ${img.isApplied ? 'border-green-300 bg-green-50' : img.isSkipped ? 'border-gray-200 bg-gray-50 opacity-60' : 'border-purple-200'}`}>
                            <div className="flex flex-col md:flex-row gap-4">
                                <img src={img.previewUrl} alt={img.name} className="w-32 h-20 object-cover rounded-lg border" />
                                <div className="flex-1 space-y-2">
                                    <div className="flex items-center gap-2 flex-wrap"><span className="font-medium">{img.name}</span><span className={`text-xs px-2 py-0.5 rounded-full ${getTypeColor(img.type)}`}>{getTypeLabel(img.type)}</span>{getStatusBadge(img)}</div>
                                    <div className="bg-gray-100 rounded p-2"><p className="text-xs text-gray-500">Распознанный текст:</p><p className="text-sm text-gray-700">{img.recognizedText}</p></div>
                                    <div className="flex items-start gap-2"><svg className="w-4 h-4 text-gray-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" /></svg><p className="text-sm text-gray-600"><span className="font-medium">Место:</span> {img.suggestedPlace}</p></div>
                                    <div className="flex items-start gap-2 flex-wrap">
                                        <svg className="w-4 h-4 text-gray-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
                                        {editingCaptionId === img.id ? (
                                            <div className="flex items-center gap-2 flex-1"><input type="text" value={tempCaption} onChange={(e) => setTempCaption(e.target.value)} className="flex-1 px-3 py-1 text-sm border rounded-lg" autoFocus /><button onClick={() => saveCaption(img.id)} className="px-2 py-1 text-xs bg-green-600 text-white rounded">Сохранить</button><button onClick={cancelEditCaption} className="px-2 py-1 text-xs border rounded">Отмена</button></div>
                                        ) : (
                                            <div className="flex-1"><p className="text-sm text-gray-700"><span className="font-medium">Подпись:</span> {getDisplayCaption(img)}</p>{!img.isApplied && !img.isSkipped && <button onClick={() => startEditCaption(img.id, getDisplayCaption(img))} className="text-xs text-purple-600">Изменить подпись</button>}</div>
                                        )}
                                    </div>
                                </div>
                                <div className="flex flex-row md:flex-col gap-2 justify-end">
                                    {!img.isApplied && !img.isSkipped && (<><button onClick={() => handleApplyImage(img.id)} className="px-4 py-2 text-sm bg-green-600 text-white rounded-lg">Применить</button><button onClick={() => handleSkipImage(img.id)} className="px-4 py-2 text-sm border rounded-lg">Пропустить</button></>)}
                                    {img.isApplied && <button onClick={() => handleSkipImage(img.id)} className="px-4 py-2 text-sm border border-yellow-300 text-yellow-600 rounded-lg">Отменить</button>}
                                    {img.isSkipped && <button onClick={() => handleApplyImage(img.id)} className="px-4 py-2 text-sm border border-purple-300 text-purple-600 rounded-lg">Восстановить</button>}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        );
    };

    // Шаг 4: Финальный экран с историей
    const ResultStep = () => {
        //const appliedImages = images.filter(img => img.isApplied);
        const changes = getAppliedChanges();

        return (
            <div className="space-y-6">
                {/* Статус "Документ готов" */}
                <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl p-6 text-center border border-green-200">
                    <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
                        <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                    </div>
                    <h3 className="text-2xl font-bold text-gray-800 mb-2">Документ готов</h3>
                    <p className="text-gray-600">Ваш документ успешно создан и готов к скачиванию</p>
                </div>

                {/* Список применённых изменений */}
                <div className="bg-gray-50 rounded-xl p-5">
                    <h4 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                        <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                        </svg>
                        Применённые изменения
                    </h4>
                    <ul className="space-y-2">
                        {changes.map((change, index) => (
                            <li key={index} className="text-sm text-gray-700 flex items-start gap-2">
                                {change.startsWith('  -') ? (
                                    <>
                                        <span className="text-purple-400 ml-4">•</span>
                                        <span className="text-gray-600">{change.substring(3)}</span>
                                    </>
                                ) : (
                                    <>
                                        <svg className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                        </svg>
                                        <span>{change}</span>
                                    </>
                                )}
                            </li>
                        ))}
                    </ul>
                </div>

                {/* Кнопка скачать и действия */}
                <div className="flex flex-col sm:flex-row gap-3 justify-center">
                    <button
                        onClick={handleDownload}
                        disabled={isDownloading}
                        className={`px-8 py-3 rounded-xl font-semibold text-white transition-all flex items-center justify-center gap-2 ${isDownloading ? 'bg-gray-400 cursor-not-allowed' : 'bg-gradient-to-r from-purple-600 to-purple-500 hover:from-purple-700 hover:to-purple-600'
                            }`}
                    >
                        {isDownloading ? (
                            <>
                                <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
                                </svg>
                                Подготовка...
                            </>
                        ) : (
                            <>
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                </svg>
                                Скачать документ
                            </>
                        )}
                    </button>
                    <button onClick={() => navigate('/')} className="px-8 py-3 border-2 border-purple-600 text-purple-600 rounded-xl font-semibold hover:bg-purple-50 transition">
                        Создать новый документ
                    </button>
                </div>

                {/* История проектов */}
                <div className="border-t border-gray-200 pt-5 mt-3">
                    <button
                        onClick={() => setShowHistory(!showHistory)}
                        className="flex items-center gap-2 text-purple-600 hover:text-purple-800 transition-colors"
                    >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span className="font-medium">{showHistory ? 'Скрыть историю' : 'Показать историю проектов'}</span>
                    </button>

                    {showHistory && (
                        <div className="mt-4 space-y-2 max-h-64 overflow-y-auto">
                            {projectHistory.length === 0 ? (
                                <p className="text-gray-500 text-sm text-center py-4">История проектов пуста</p>
                            ) : (
                                projectHistory.map((project) => (
                                    <div key={project.id} className="bg-gray-50 rounded-lg p-3 hover:bg-gray-100 transition">
                                        <div className="flex items-center justify-between flex-wrap gap-2">
                                            <div className="flex-1">
                                                <div className="flex items-center gap-2 flex-wrap">
                                                    <span className="font-medium text-gray-800">
                                                        {project.docType === 'lab' ? 'Лабораторная работа' : project.docType === 'report' ? 'Отчёт' : 'Курсовая работа'}
                                                    </span>
                                                    <span className="text-xs text-gray-500">{project.studentName} | {project.group}</span>
                                                </div>
                                                <p className="text-xs text-gray-400 mt-1">{formatDate(project.createdAt)}</p>
                                                <p className="text-xs text-gray-500 mt-1">{project.university} • {project.imagesCount} изобр. • {project.filesCount} файлов</p>
                                            </div>
                                            <button
                                                onClick={() => {
                                                    alert(`Загрузка проекта ${project.id}\nСтудент: ${project.studentName}\nДата: ${formatDate(project.createdAt)}`);
                                                }}
                                                className="px-3 py-1 text-sm text-purple-600 border border-purple-300 rounded-lg hover:bg-purple-50 transition"
                                            >
                                                Загрузить
                                            </button>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    )}
                </div>
            </div>
        );
    };

    const renderStep = () => {
        switch (currentStep) {
            case 'title': return <TitleStep />;
            case 'analysis': return <AnalysisStep />;
            case 'images': return <ImagesStep />;
            case 'result': return <ResultStep />;
            default: return null;
        }
    };

    const getNextButtonText = () => {
        switch (currentStep) {
            case 'title': return isSubmitting ? 'Отправка...' : 'Начать анализ →';
            case 'analysis': return analysisStatus === 'завершено' ? 'Далее →' : 'Анализ...';
            case 'images': return 'Создать документ →';
            default: return 'Далее';
        }
    };

    const isNextDisabled = () => {
        if (currentStep === 'title') return isSubmitting;
        if (currentStep === 'analysis') return analysisStatus !== 'завершено';
        return false;
    };

    const getStepTitle = () => {
        const titles = { title: 'Титульный лист', analysis: 'Анализ файлов', images: 'Работа с изображениями', result: 'Результат' };
        return titles[currentStep];
    };

    const getStepNumber = () => {
        const numbers = { title: 1, analysis: 2, images: 3, result: 4 };
        return numbers[currentStep];
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-50 to-purple-50">
            <div className="bg-white shadow-sm border-b border-purple-100">
                <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between">
                    <div><h1 className="text-2xl font-bold text-gray-800">GenDoc AI</h1><p className="text-gray-500 text-sm">Создание документа</p></div>
                    <button onClick={() => navigate('/')} className="text-purple-600 hover:text-purple-800 text-sm">← На главную</button>
                </div>
            </div>

            <div className="max-w-4xl mx-auto px-4 py-8">
                <div className="bg-white rounded-2xl shadow-xl p-6">
                    {currentStep !== 'result' && (
                        <div className="flex items-center gap-3 mb-6 pb-4 border-b border-gray-200">
                            <div className="w-10 h-10 rounded-full bg-purple-600 text-white flex items-center justify-center font-bold">{getStepNumber()}</div>
                            <h2 className="text-xl font-semibold text-gray-800">{getStepTitle()}</h2>
                        </div>
                    )}

                    <div className="mt-4">{renderStep()}</div>

                    {currentStep !== 'result' && (
                        <div className="flex justify-between mt-8 pt-4 border-t border-gray-200">
                            {currentStep !== 'title' && <button onClick={() => { const steps: Step[] = ['title', 'analysis', 'images', 'result']; const idx = steps.indexOf(currentStep); if (idx > 0) setCurrentStep(steps[idx - 1]); }} className="px-5 py-2 border border-gray-300 text-gray-600 rounded-lg hover:bg-gray-50">← Назад</button>}
                            {currentStep === 'title' && <div></div>}
                            <button onClick={goToNextStep} disabled={isNextDisabled()} className={`px-6 py-2 rounded-lg font-medium ml-auto ${isNextDisabled() ? 'bg-gray-300 text-gray-500 cursor-not-allowed' : 'bg-purple-600 text-white hover:bg-purple-700'}`}>{getNextButtonText()}</button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default WizardPage;