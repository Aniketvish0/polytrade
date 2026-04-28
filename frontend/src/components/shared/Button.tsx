import React from 'react';

type ButtonVariant = 'primary' | 'danger' | 'ghost' | 'success';
type ButtonSize = 'sm' | 'md';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  children: React.ReactNode;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    'bg-accent text-white hover:bg-blue-600 active:bg-blue-700 border border-accent',
  danger:
    'bg-denied/10 text-denied hover:bg-denied/20 active:bg-denied/30 border border-denied/30',
  ghost:
    'bg-transparent text-secondary hover:text-primary hover:bg-white/5 border border-transparent',
  success:
    'bg-approved/10 text-approved hover:bg-approved/20 active:bg-approved/30 border border-approved/30',
};

const sizeStyles: Record<ButtonSize, string> = {
  sm: 'px-2 py-0.5 text-xs',
  md: 'px-3 py-1 text-sm',
};

export function Button({
  variant = 'ghost',
  size = 'sm',
  children,
  className = '',
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      className={`
        inline-flex items-center justify-center font-medium
        transition-colors duration-100
        disabled:opacity-40 disabled:cursor-not-allowed
        ${variantStyles[variant]}
        ${sizeStyles[size]}
        ${className}
      `}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
}
