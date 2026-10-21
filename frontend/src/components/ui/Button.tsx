import type { ButtonHTMLAttributes } from "react";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "danger";
};

export function Button({ variant = "primary", ...props }: ButtonProps) {
  return (
    <p className="todo">
      TODO: styled button, variant {variant}, forwards native button props and type="button".
    </p>
  );
}
