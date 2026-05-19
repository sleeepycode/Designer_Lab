import { Link } from 'react-router-dom';
import { BrandLogo } from '@/components/BrandLogo';
import { useAuth } from '@/context/AuthContext';

export function HomePage() {
  const { user } = useAuth();

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <header className="space-y-2">
        <div className="flex items-center gap-3">
          <BrandLogo size="lg" />
          <h1 className="text-3xl font-bold tracking-tight text-zinc-900">Оформлятор</h1>
        </div>
        <p className="mt-2 text-zinc-600">
          Оформление лабораторной работы в DOCX: шесть шагов — загрузка, реквизиты, изображения, ГОСТ, проверка и
          скачивание.
        </p>
      </header>

      {user && (
        <p className="card-panel-muted border-brand/20 bg-gradient-to-r from-violet-50/90 to-white/80 text-zinc-800">
          Вы вошли в аккаунт. Создайте документ через
          «+» на панели слева или кнопку ниже.
        </p>
      )}

      <section className="card-panel p-6">
        <h2 className="text-lg font-semibold text-zinc-900">Как пользоваться</h2>
        <ol className="mt-3 list-decimal space-y-2 pl-5 text-zinc-600">
          <li>Войдите в аккаунт.</li>
          <li>Откройте «Создать новый проект» и пройдите шесть шагов мастера.</li>
          <li>На шаге с изображениями добавьте рисунки, если они нужны в работе.</li>
          <li>После обработки скачайте готовый документ.</li>
        </ol>
      </section>

      {!user && (
        <section className="card-panel border-brand/20 bg-gradient-to-br from-violet-50/80 to-white/90 p-6">
          <h2 className="text-lg font-semibold text-zinc-900">Авторизация</h2>
          <p className="mt-2 text-zinc-600">Войдите или зарегистрируйтесь, чтобы создавать и скачивать документы.</p>
          <Link to="/login" className="btn-primary mt-4 inline-flex">
            Перейти к входу
          </Link>
        </section>
      )}

      {user && (
        <Link to="/project/new" className="btn-primary inline-flex">
          Создать новый проект
        </Link>
      )}
    </div>
  );
}
