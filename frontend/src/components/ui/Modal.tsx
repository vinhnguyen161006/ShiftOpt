import type { ReactNode } from "react";

type ModalProps = {
  title: string;
  open: boolean;
  onClose: () => void;
  children: ReactNode;
};

export function Modal({ title, open, onClose, children }: ModalProps) {
  return (
    <p className="todo">
      TODO: dialog "{title}" with close button, Escape to close and focus trap; hidden when not
      open.
    </p>
  );
}
