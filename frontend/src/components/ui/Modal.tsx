import { type ReactNode, useEffect, useId, useRef } from "react";

type ModalProps = {
  title: string;
  open: boolean;
  onClose: () => void;
  children: ReactNode;
  wide?: boolean;
};

export function Modal({ title, open, onClose, children, wide = false }: ModalProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const titleId = useId();

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) {
      return;
    }
    if (open && !dialog.open) {
      dialog.showModal();
    }
    if (!open && dialog.open) {
      dialog.close();
    }
  }, [open]);

  return (
    <dialog
      ref={dialogRef}
      className={wide ? "dialog dialog-wide" : "dialog"}
      aria-labelledby={titleId}
      onClose={onClose}
    >
      {open && (
        <div className="dialog-inner">
          <div className="dialog-head">
            <h2 id={titleId} className="dialog-title">
              {title}
            </h2>
            <button type="button" className="btn btn-ghost btn-sm" onClick={onClose}>
              Close
            </button>
          </div>
          {children}
        </div>
      )}
    </dialog>
  );
}
