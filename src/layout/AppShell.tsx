import { useState } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { BrandLogo } from '@/components/BrandLogo';
import { useAuth } from '@/context/AuthContext';

const navCls = ({ isActive }: { isActive: boolean }) =>
  `flex h-11 w-11 items-center justify-center rounded-xl transition-all ${
    isActive
      ? 'bg-brand text-white shadow-md shadow-brand/30'
      : 'text-zinc-500 hover:bg-white/80 hover:text-brand-dark'
  }`;

function IconHome() {
  return (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
      <path d="M4 10.5L12 4l8 6.5V20a1 1 0 01-1 1h-5v-6H10v6H5a1 1 0 01-1-1v-9.5z" />
    </svg>
  );
}

function IconPlus() {
  return (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
      <path d="M12 5v14M5 12h14" />
    </svg>
  );
}

export function AppShell() {
  const { user, logout } = useAuth();
  const loc = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <div className="flex min-h-screen flex-col md:flex-row">
      <aside className="glass-bar flex flex-row items-center gap-1 border-b px-3 py-2 md:w-[72px] md:flex-col md:border-b-0 md:border-r md:py-6">
        <div className="mb-0 flex flex-1 gap-1 md:mb-8 md:flex-none md:flex-col md:gap-2">
          <NavLink to="/" className={navCls} title="Главная">
            <IconHome />
          </NavLink>
          <NavLink to="/project/new" className={navCls} title="Создать новый проект">
            <IconPlus />
          </NavLink>
        </div>
      </aside>

      <div className="flex min-h-0 flex-1 flex-col">
        <header className="glass-bar flex items-center justify-between border-b px-4 py-3 md:px-8">
          <NavLink to="/" className="flex items-center gap-3">
            <BrandLogo />
            <span className="text-lg font-semibold tracking-tight text-zinc-900">Оформлятор</span>
          </NavLink>

          <div className="flex items-center gap-3">
            {!user && (
              <>
                <NavLink to="/login" className="text-sm font-medium text-brand hover:text-brand-dark">
                  Войти
                </NavLink>
                <NavLink to="/login?mode=register" className="btn-primary px-4 py-2 text-sm">
                  Регистрация
                </NavLink>
              </>
            )}
            {user && (
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setMenuOpen((v) => !v)}
                  className="flex items-center gap-2 rounded-full py-1 pl-1 pr-3 transition hover:bg-white/60"
                >
                  <span className="flex h-9 w-9 items-center justify-center rounded-full bg-brand text-sm font-semibold text-white shadow-sm">
                    {user.email.slice(0, 1).toUpperCase()}
                  </span>
                  <span className="hidden max-w-[180px] truncate text-sm font-medium sm:inline">{user.email}</span>
                  <svg className="h-4 w-4 text-zinc-400" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M7 10l5 5 5-5H7z" />
                  </svg>
                </button>
                {menuOpen && (
                  <>
                    <button
                      type="button"
                      className="fixed inset-0 z-10 cursor-default bg-transparent"
                      aria-label="Закрыть меню"
                      onClick={() => setMenuOpen(false)}
                    />
                    <div className="card-panel absolute right-0 z-20 mt-2 w-56 py-2">
                      <div className="border-b border-violet-100 px-4 pb-2">
                        <p className="truncate text-sm font-medium">{user.email}</p>
                      </div>
                      <button
                        type="button"
                        className="mt-1 w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50"
                        onClick={() => {
                          setMenuOpen(false);
                          logout();
                        }}
                      >
                        Выйти
                      </button>
                    </div>
                  </>
                )}
              </div>
            )}
          </div>
        </header>

        <main className="flex-1 overflow-auto p-4 md:p-8">
          <Outlet />
        </main>

        {!user && !loc.pathname.startsWith('/login') && (
          <footer className="glass-bar border-t px-4 py-3 text-center text-xs text-zinc-500 md:px-8">
            <NavLink className="font-medium text-brand" to="/login">
              Войти в аккаунт
            </NavLink>
          </footer>
        )}
      </div>
    </div>
  );
}
