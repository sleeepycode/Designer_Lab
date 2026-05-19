import { useEffect, useRef, useState } from 'react';
import { renderAsync } from 'docx-preview';

type DocxPreviewProps = {
  blob: Blob | null;
  className?: string;
};

export function DocxPreview({ blob, className = '' }: DocxPreviewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    if (!blob) {
      el.innerHTML = '';
      setError(null);
      setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);
    el.innerHTML = '';

    void renderAsync(blob, el, undefined, {
      className: 'docx-preview',
      inWrapper: true,
      ignoreWidth: false,
      ignoreHeight: false,
      breakPages: true,
    })
      .then(() => {
        if (!cancelled) setLoading(false);
      })
      .catch(() => {
        if (!cancelled) {
          setLoading(false);
          setError('Не удалось показать предпросмотр. Файл можно будет скачать на следующем шаге.');
        }
      });

    return () => {
      cancelled = true;
    };
  }, [blob]);

  if (!blob) {
    return (
      <p className={`text-sm text-zinc-500 ${className}`}>
        Предпросмотр появится после обработки документа на шаге 4.
      </p>
    );
  }

  return (
    <div className={className}>
      {loading && <p className="mb-2 text-sm text-zinc-500">Загрузка предпросмотра…</p>}
      {error && <p className="mb-2 text-sm text-amber-800">{error}</p>}
      <div
        ref={containerRef}
        className="max-h-[min(70vh,640px)] overflow-auto rounded-xl border border-zinc-200 bg-white p-4 shadow-inner docx-preview-host"
      />
    </div>
  );
}
