import { FormEvent, useMemo, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { BrandLogo } from '@/components/BrandLogo';
import { useAuth } from '@/context/AuthContext';

export function LoginPage() {
  const { login, register } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const isRegister = params.get('mode') === 'register';

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const title = useMemo(() => (isRegister ? 'Регистрация' : 'Вход'), [isRegister]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');
    const trimmed = email.trim();
    if (!trimmed.includes('@')) {
      setError('Введите корректный email.');
      return;
    }
    if (password.length < 6) {
      setError('Пароль должен быть не короче 6 символов.');
      return;
    }
    setSubmitting(true);
    try {
      if (isRegister) {
        await register(trimmed, password);
      } else {
        await login(trimmed, password);
      }
      navigate('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось войти');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto flex max-w-md flex-col gap-8">
      <div className="card-panel p-8">
        <div className="flex flex-col items-center gap-3">
          <BrandLogo size="lg" />
          <h1 className="text-center text-2xl font-bold">Оформлятор</h1>
        </div>
        <p className="mt-1 text-center text-sm text-zinc-500">
          {isRegister ? 'Создайте аккаунт на сервере' : 'Войдите в свой аккаунт'}
        </p>

        <form onSubmit={(e) => void onSubmit(e)} className="mt-8 space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-zinc-700">Email</label>
            <input
              type="email"
              autoComplete="email"
              placeholder="you@example.com"
              className="input-field"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={submitting}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-zinc-700">Пароль</label>
            <input
              type="password"
              autoComplete={isRegister ? 'new-password' : 'current-password'}
              className="input-field"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={submitting}
            />
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button type="submit" className="btn-primary w-full py-3" disabled={submitting}>
            {submitting ? 'Подождите…' : title}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-zinc-600">
          {isRegister ? (
            <>
              Уже есть аккаунт?{' '}
              <Link className="font-medium text-brand" to="/login">
                Войти
              </Link>
            </>
          ) : (
            <>
              Нет аккаунта?{' '}
              <Link className="font-medium text-brand" to="/login?mode=register">
                Зарегистрироваться
              </Link>
            </>
          )}
        </p>
      </div>
    </div>
  );
}
