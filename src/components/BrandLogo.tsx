type BrandLogoProps = {
  size?: 'sm' | 'md' | 'lg';
  showShadow?: boolean;
};

const sizes = {
  sm: 'h-9 w-9',
  md: 'h-10 w-10',
  lg: 'h-12 w-12',
};

export function BrandLogo({ size = 'md', showShadow = true }: BrandLogoProps) {
  return (
    <span
      className={`relative inline-flex shrink-0 items-center justify-center overflow-hidden rounded-xl bg-gradient-to-br from-brand to-brand-dark ${sizes[size]} ${showShadow ? 'shadow-md shadow-brand/30' : ''}`}
    >
      <img
        src="/assets/logo.png"
        alt=""
        className="h-full w-full object-cover"
        onError={(e) => {
          const img = e.currentTarget;
          img.style.display = 'none';
          const fallback = img.nextElementSibling;
          if (fallback instanceof HTMLElement) fallback.style.display = 'flex';
        }}
      />
      <span className="hidden h-full w-full items-center justify-center text-white" aria-hidden>
        <svg className="h-[55%] w-[55%]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
          <path d="M8 4h8l4 4v12a1 1 0 01-1 1H8a1 1 0 01-1-1V5a1 1 0 011-1z" />
          <path d="M16 4v4h4M9 13l2 2 4-4" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </span>
    </span>
  );
}
