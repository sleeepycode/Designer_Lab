import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  applySuggestions,
  downloadProjectBlob,
  extractDocx,
  type ExtractResponse,
  type ImageSuggestion,
  type ProcessPayload,
  getSuggestions,
  processProject,
  uploadProject,
  uploadProjectFile,
  fetchTaskReportJson,
} from '@/api/client';
import { DocxPreview } from '@/components/DocxPreview';
import { TITLE_DEFAULT_FACULTY, TITLE_UNIVERSITY_LINES } from '@/constants/titlePage';
import { useAuth } from '@/context/AuthContext';

const STEPS = [
  { n: 1, title: 'Загрузка', desc: 'Исходный DOCX' },
  { n: 2, title: 'Текст и структура', desc: 'Титульные данные и абзацы' },
  { n: 3, title: 'Изображения', desc: 'Подсказки по вставке' },
  { n: 4, title: 'Оформление', desc: 'ГОСТ на сервере' },
  { n: 5, title: 'Проверка', desc: 'Отчёт и предпросмотр' },
  { n: 6, title: 'Скачать', desc: 'Готовый файл' },
];

function isReportSuccessful(report: Record<string, unknown>): boolean {
  const status = report.status;
  const code = typeof status === 'string' ? status : '';
  if (code === 'failed' || code === 'error') return false;
  if (Array.isArray(report.errors) && report.errors.length > 0) return false;
  return true;
}

function ReportSummary({ report }: { report: Record<string, unknown> }) {
  const ok = isReportSuccessful(report);

  return (
    <div
      className={`rounded-xl border px-4 py-4 ${ok ? 'border-emerald-200 bg-emerald-50/80' : 'border-amber-200 bg-amber-50/80'}`}
    >
      <p className="text-sm font-medium text-zinc-800">
        {ok ? 'Документ успешно обработан. Можно переходить к скачиванию.' : 'Обработка завершилась с замечаниями.'}
      </p>
      {!ok && typeof report.message === 'string' && report.message.trim() && (
        <p className="mt-2 text-sm text-zinc-600">{report.message}</p>
      )}
    </div>
  );
}

function isProcessPayloadComplete(p: ProcessPayload): boolean {
  return Boolean(
    p.faculty.trim() &&
      p.department.trim() &&
      p.student_group.trim() &&
      p.lab_title.trim() &&
      p.student_name.trim() &&
      p.reviewer_name.trim() &&
      p.discipline.trim(),
  );
}

export function NewProjectPage() {
  const { user } = useAuth();
  const [step, setStep] = useState(1);
  const [maxReachedStep, setMaxReachedStep] = useState(1);

  const goToStep = useCallback(
    (n: number) => {
      if (n < 1 || n > STEPS.length) return;
      if (n > maxReachedStep) return;
      setErr('');
      setStep(n);
    },
    [maxReachedStep],
  );

  const advanceToStep = useCallback((n: number) => {
    setMaxReachedStep((m) => Math.max(m, n));
    setStep(n);
  }, []);
  const [docFile, setDocFile] = useState<File | null>(null);
  const [projectId, setProjectId] = useState<string | null>(null);
  const [extracted, setExtracted] = useState<ExtractResponse | null>(null);
  const [suggestions, setSuggestions] = useState<ImageSuggestion[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(() => new Set());
  const [report, setReport] = useState<Record<string, unknown> | null>(null);
  const [previewBlob, setPreviewBlob] = useState<Blob | null>(null);
  const [downloadBlob, setDownloadBlob] = useState<Blob | null>(null);
  const [downloadName, setDownloadName] = useState('');
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');

  const [payload, setPayload] = useState<ProcessPayload>(() => ({
    faculty: TITLE_DEFAULT_FACULTY,
    department: 'Кафедра',
    student_group: '',
    lab_title: '',
    lab_number: '1',
    student_name: '',
    reviewer_name: '',
    discipline: '',
  }));

  useEffect(() => {
    if (!downloadBlob) {
      setDownloadUrl(null);
      return;
    }
    const url = URL.createObjectURL(downloadBlob);
    setDownloadUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [downloadBlob]);

  useEffect(() => {
    if (step !== 5 || !report || !user?.userId || !projectId) {
      if (step !== 5) setPreviewBlob(null);
      return;
    }
    let cancelled = false;
    void downloadProjectBlob(projectId, user.userId)
      .then(({ blob }) => {
        if (!cancelled) setPreviewBlob(blob);
      })
      .catch(() => {
        if (!cancelled) setPreviewBlob(null);
      });
    return () => {
      cancelled = true;
    };
  }, [step, report, user, projectId]);

  const loadExtract = useCallback(async () => {
    if (!user || !docFile) return;
    setBusy(true);
    setErr('');
    try {
      const data = await extractDocx(docFile, user.userId);
      setExtracted(data);
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Ошибка извлечения');
    } finally {
      setBusy(false);
    }
  }, [user, docFile]);

  useEffect(() => {
    if (step === 2 && projectId && docFile && !extracted && user) {
      void loadExtract();
    }
  }, [step, projectId, docFile, extracted, user, loadExtract]);

  async function onUploadStep() {
    if (!user || !docFile) return;
    setBusy(true);
    setErr('');
    try {
      const res = await uploadProject(docFile, user.userId);
      setProjectId(res.project_id);
      advanceToStep(2);
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Ошибка загрузки');
    } finally {
      setBusy(false);
    }
  }

  const refreshSuggestions = useCallback(async () => {
    if (!user || !projectId) return;
    setBusy(true);
    setErr('');
    try {
      const res = await getSuggestions(projectId, user.userId);
      setSuggestions(res.suggestions);
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Ошибка подсказок');
    } finally {
      setBusy(false);
    }
  }, [user, projectId]);

  useEffect(() => {
    if (step === 3 && projectId && user) {
      void refreshSuggestions();
    }
  }, [step, projectId, user, refreshSuggestions]);

  async function onAddImages(files: FileList | null) {
    if (!user || !projectId || !files?.length) return;
    setBusy(true);
    setErr('');
    try {
      for (const f of Array.from(files)) {
        if (!/\.(png|jpg|jpeg)$/i.test(f.name)) {
          setErr('Для этого шага используйте .png или .jpg');
          setBusy(false);
          return;
        }
        await uploadProjectFile(projectId, f, user.userId);
      }
      await refreshSuggestions();
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Ошибка загрузки файла');
    } finally {
      setBusy(false);
    }
  }

  function toggleSuggestion(id: string) {
    setSelectedIds((prev) => {
      const n = new Set(prev);
      if (n.has(id)) n.delete(id);
      else n.add(id);
      return n;
    });
  }

  async function runProcess() {
    if (!user || !projectId) return;
    if (!isProcessPayloadComplete(payload)) {
      setErr('Заполните все обязательные поля на шаге 2.');
      return;
    }
    setErr('');
    setBusy(true);
    try {
      const res = await processProject(projectId, user.userId, payload);
      const rep = res.report as { status?: string };
      if (rep?.status === 'failed') {
        setErr('Не удалось обработать документ. Проверьте файл и заполненные поля.');
        setBusy(false);
        return;
      }
      if (selectedIds.size > 0) {
        try {
          await applySuggestions(projectId, user.userId, [...selectedIds]);
        } catch {
          /* optional */
        }
      }
      try {
        const r = await fetchTaskReportJson(res.task_id, user.userId);
        setReport(r);
      } catch {
        setReport({ info: 'Краткий отчёт недоступен, но обработка завершена. Скачайте файл на следующем шаге.' });
      }
      advanceToStep(5);
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Ошибка обработки');
    } finally {
      setBusy(false);
    }
  }

  async function handleDownload() {
    if (!user || !projectId) return;
    if (downloadUrl && downloadBlob) {
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = downloadName || 'document.docx';
      a.click();
      return;
    }
    setBusy(true);
    setErr('');
    try {
      const { blob, filename } = await downloadProjectBlob(projectId, user.userId);
      setDownloadBlob(blob);
      setDownloadName(filename);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Файл ещё не готов');
    } finally {
      setBusy(false);
    }
  }

  if (!user) {
    return (
      <div className="card-panel mx-auto max-w-lg p-8 text-center">
        <p className="text-zinc-600">Войдите в аккаунт, чтобы создать документ.</p>
        <Link className="mt-4 inline-block font-medium text-brand" to="/login">
          Перейти к авторизации
        </Link>
      </div>
    );
  }

  const fileLabel = docFile?.name;

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="flex flex-wrap gap-2">
        {STEPS.map((s) => {
          const reachable = s.n <= maxReachedStep;
          return (
            <button
              key={s.n}
              type="button"
              title={s.desc}
              disabled={!reachable}
              onClick={() => goToStep(s.n)}
              className={`flex min-w-[100px] flex-1 flex-col rounded-xl border px-3 py-2 text-left text-xs transition-all md:text-sm ${
                step === s.n
                  ? 'border-brand bg-violet-50/90 text-brand-dark shadow-sm shadow-brand/10'
                  : reachable
                    ? 'cursor-pointer border-violet-200/80 bg-white/80 text-zinc-600 hover:border-brand/40 hover:shadow-sm'
                    : 'cursor-not-allowed border-violet-100/60 bg-white/40 text-zinc-400'
              }`}
            >
              <span className="font-bold">{s.n}</span>
              <span className="font-medium">{s.title}</span>
            </button>
          );
        })}
      </div>

      <div className="card-panel p-6 md:p-8">
        {err && (
          <div className="mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800 whitespace-pre-wrap">
            {err}
          </div>
        )}

        {step === 1 && (
          <div className="space-y-6">
            <p className="text-sm text-zinc-600">
              Лабораторная работа в формате DOCX: цель, оборудование, ход работы, выводы.
            </p>
            <div>
              <h2 className="text-lg font-semibold">Загрузите DOCX</h2>
              <label
                className="dropzone mt-3"
                onDragOver={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                }}
                onDrop={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  const f = e.dataTransfer.files?.[0];
                  if (f && f.name.toLowerCase().endsWith('.docx')) {
                    setDocFile(f);
                    setErr('');
                  } else {
                    setErr('Нужен файл .docx');
                  }
                }}
              >
                <span className="text-brand">
                  <svg className="mx-auto h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                </span>
                <p className="mt-2 text-center text-sm font-medium text-zinc-700">
                  Перетащите файл сюда или нажмите для выбора
                </p>
                <p className="mt-1 text-center text-xs text-zinc-500">Только .docx</p>
                <input
                  type="file"
                  accept=".docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                  className="hidden"
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    setDocFile(f ?? null);
                    setErr('');
                  }}
                />
              </label>
              {docFile && <p className="mt-2 text-sm text-zinc-600">Выбран: {docFile.name}</p>}
            </div>
            <div className="flex justify-end">
              <button
                type="button"
                disabled={!docFile || busy}
                onClick={() => void onUploadStep()}
                className="rounded-full bg-brand px-6 py-2.5 text-sm font-semibold text-white shadow disabled:opacity-50"
              >
                Далее →
              </button>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-6">
            <div className="rounded-xl bg-violet-50 px-4 py-2 text-sm text-zinc-800">
              Лабораторная работа · Файл: {fileLabel ?? '—'}
            </div>
            <div>
              <h2 className="text-lg font-semibold">Титульные данные</h2>
              <p className="mt-1 text-sm text-zinc-500">Заполните поля, как на титульном листе работы.</p>
              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                <div className="sm:col-span-2">
                  <ReadonlyUniversityBlock />
                </div>
                <Field label="Факультет *" v={payload.faculty} on={(v) => setPayload({ ...payload, faculty: v })} />
                <Field label="Кафедра *" v={payload.department} on={(v) => setPayload({ ...payload, department: v })} />
                <Field label="Студент *" v={payload.student_name} on={(v) => setPayload({ ...payload, student_name: v })} />
                <Field label="Группа *" v={payload.student_group} on={(v) => setPayload({ ...payload, student_group: v })} />
                <Field label="Тема работы *" v={payload.lab_title} on={(v) => setPayload({ ...payload, lab_title: v })} />
                <Field label="Преподаватель *" v={payload.reviewer_name} on={(v) => setPayload({ ...payload, reviewer_name: v })} />
                <div className="sm:col-span-2">
                  <Field label="Дисциплина *" v={payload.discipline} on={(v) => setPayload({ ...payload, discipline: v })} />
                </div>
                <Field label="Номер работы *" v={payload.lab_number} on={(v) => setPayload({ ...payload, lab_number: v })} />
              </div>
            </div>
            <div>
              <h2 className="text-lg font-semibold">Текст документа (абзацы)</h2>
              {busy && !extracted && <p className="mt-2 text-sm text-zinc-500">Загрузка структуры…</p>}
              {extracted && (
                <div className="mt-3 max-h-72 space-y-2 overflow-y-auto rounded-xl border border-zinc-200 bg-zinc-50 p-4 text-sm">
                  {extracted.paragraphs.length === 0 && <p className="text-zinc-500">Нет непустых абзацев.</p>}
                  {extracted.paragraphs.map((p, i) => (
                    <p key={i} className="border-b border-zinc-200/80 pb-2 text-zinc-800 last:border-0">
                      {p}
                    </p>
                  ))}
                </div>
              )}
            </div>
            <div className="flex justify-between">
              <button type="button" className="text-sm font-medium text-zinc-600 hover:text-zinc-900" onClick={() => goToStep(1)}>
                ← Назад
              </button>
              <button
                type="button"
                disabled={!extracted || busy}
                onClick={() => {
                  if (!isProcessPayloadComplete(payload)) {
                    setErr('Заполните все обязательные поля.');
                    return;
                  }
                  setErr('');
                  advanceToStep(3);
                }}
                className="rounded-full bg-brand px-6 py-2.5 text-sm font-semibold text-white disabled:opacity-50"
              >
                Далее →
              </button>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-6">
            <h2 className="text-lg font-semibold">Изображения к работе</h2>
            <p className="text-sm text-zinc-600">
              Добавьте иллюстрации к работе. Отметьте подсказки, которые хотите учесть при оформлении.
            </p>
            <label className="dropzone py-8">
              <span className="text-sm font-medium text-brand">+ Добавить изображения</span>
              <input type="file" accept=".png,.jpg,.jpeg" multiple className="hidden" onChange={(e) => void onAddImages(e.target.files)} />
            </label>
            <div className="space-y-3">
              {suggestions.length === 0 && <p className="text-sm text-zinc-500">Пока нет загруженных изображений.</p>}
              {suggestions.map((s) => (
                <div
                  key={s.id}
                  className={`flex flex-col gap-2 rounded-xl border p-4 sm:flex-row sm:items-start ${
                    selectedIds.has(s.id) ? 'border-brand bg-violet-50/40' : 'border-zinc-200'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={selectedIds.has(s.id)}
                    onChange={() => toggleSuggestion(s.id)}
                    className="mt-1 h-4 w-4 rounded border-zinc-300 text-brand"
                  />
                  <div className="min-w-0 flex-1 text-sm">
                    <p className="font-medium text-zinc-900">{s.image_name}</p>
                    {s.caption && <p className="mt-1 text-sm text-zinc-600">{s.caption}</p>}
                    {s.suggested_insertion && (
                      <p className="mt-2 text-sm text-zinc-500">{s.suggested_insertion}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
            <div className="flex justify-between">
              <button type="button" className="text-sm font-medium text-zinc-600" onClick={() => goToStep(2)}>
                ← Назад
              </button>
              <button
                type="button"
                onClick={() => advanceToStep(4)}
                className="rounded-full bg-brand px-6 py-2.5 text-sm font-semibold text-white"
              >
                Далее →
              </button>
            </div>
          </div>
        )}

        {step === 4 && (
          <div className="space-y-6">
            <h2 className="text-lg font-semibold">Оформление по ГОСТ</h2>
            <p className="text-sm text-zinc-600">
              Будут применены стандартные параметры оформления: Times New Roman, 14 pt, полуторный интервал, отступ абзаца
              1,25 см.
            </p>
            <p className="text-sm text-zinc-600">Нажмите «Запустить обработку», чтобы оформить документ.</p>
            <div className="flex justify-between">
              <button type="button" className="text-sm font-medium text-zinc-600" onClick={() => goToStep(3)}>
                ← Назад
              </button>
              <button
                type="button"
                disabled={busy}
                onClick={() => void runProcess()}
                className="rounded-full bg-brand px-6 py-2.5 text-sm font-semibold text-white disabled:opacity-50"
              >
                {busy ? 'Обработка…' : 'Запустить обработку'}
              </button>
            </div>
          </div>
        )}

        {step === 5 && (
          <div className="space-y-6">
            <h2 className="text-lg font-semibold">Проверка и предпросмотр</h2>
            {report ? (
              <ReportSummary report={report} />
            ) : (
              <p className="text-sm text-zinc-600">Отчёт появится после обработки на шаге 4.</p>
            )}
            <div>
              <h3 className="mb-2 text-sm font-medium text-zinc-700">Предпросмотр документа</h3>
              <DocxPreview blob={previewBlob} />
            </div>
            <div className="flex flex-wrap justify-between gap-3">
              <button type="button" className="text-sm font-medium text-zinc-600 hover:text-zinc-900" onClick={() => goToStep(4)}>
                ← Назад
              </button>
              <button
                type="button"
                disabled={!report}
                onClick={() => advanceToStep(6)}
                className="rounded-full bg-brand px-6 py-2.5 text-sm font-semibold text-white disabled:opacity-50"
              >
                Далее →
              </button>
            </div>
          </div>
        )}

        {step === 6 && (
          <div className="flex flex-col items-center gap-6 py-12">
            <button
              type="button"
              className="btn-primary px-10 py-3 text-base"
              disabled={busy}
              onClick={() => void handleDownload()}
            >
              {busy ? 'Загрузка…' : 'Скачать документ'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

function ReadonlyUniversityBlock() {
  return (
    <div>
      <p className="mb-1 text-xs font-medium text-zinc-600">Университет (ВУЗ)</p>
      <div className="rounded-xl border border-zinc-200 bg-zinc-50/90 px-3 py-3 text-center text-xs leading-relaxed text-zinc-700">
        {TITLE_UNIVERSITY_LINES.map((line) => (
          <p key={line}>{line}</p>
        ))}
      </div>
    </div>
  );
}

function Field({ label, v, on }: { label: string; v: string; on: (v: string) => void }) {
  return (
    <div>
      <label className="mb-1 block text-xs font-medium text-zinc-600">{label}</label>
      <input
        className="input-field"
        value={v}
        onChange={(e) => on(e.target.value)}
      />
    </div>
  );
}
