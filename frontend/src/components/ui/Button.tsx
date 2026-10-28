import type { ButtonHTMLAttributes } from "react";
import { Corners } from "./Corners";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost";
  size?: "md" | "sm";
};

export function buttonClass(variant: ButtonProps["variant"], size: ButtonProps["size"] = "md") {
  return [
    "btn",
    `btn-${variant}`,
    size === "sm" ? "btn-sm" : "",
    variant === "primary" ? "blueprint" : "",
  ]
    .filter(Boolean)
    .join(" ");
}

export function Button({
  variant = "secondary",
  size = "md",
  className,
  children,
  type = "button",
  ...props
}: ButtonProps) {
  const classes = [buttonClass(variant, size), className].filter(Boolean).join(" ");
  return (
    <button type={type === "submit" ? "submit" : "button"} className={classes} {...props}>
      {children}
      {variant === "primary" && <Corners />}
    </button>
  );
}
