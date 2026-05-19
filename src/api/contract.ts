/**
 * Контракт REST API между frontend и backend.
 * При изменении API на backend обновите типы в client.ts и этот файл.
 */
export const API_ROUTES = {
  health: '/health',
  projectsUpload: '/projects/upload',
  project: (id: string) => `/projects/${id}`,
  projectFiles: (id: string) => `/projects/${id}/files`,
  projectProcess: (id: string) => `/projects/${id}/process`,
  projectSuggestions: (id: string) => `/projects/${id}/suggestions`,
  projectSuggestionsApply: (id: string) => `/projects/${id}/suggestions/apply`,
  projectDownload: (id: string) => `/projects/${id}/download`,
  projectAnalysis: (id: string) => `/projects/${id}/analysis`,
  projectAnalyze: (id: string) => `/projects/${id}/analyze`,
  tasksExtract: '/tasks/extract',
  taskReport: (taskId: string) => `/tasks/${taskId}/report`,
  tasksList: '/tasks',
} as const;

/** Поля формы шага 2 мастера → POST /projects/{id}/process (multipart/form-data) */
export const PROCESS_FORM_FIELDS = [
  'user_id',
  'faculty',
  'department',
  'student_group',
  'lab_title',
  'lab_number',
  'student_name',
  'reviewer_name',
  'discipline',
] as const;
