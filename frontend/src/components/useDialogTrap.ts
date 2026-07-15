import { useEffect, useRef } from "react";

export default function useDialogTrap(container: React.RefObject<HTMLElement | null>, onClose: () => void) {
  const closeHandler = useRef(onClose);
  closeHandler.current = onClose;
  useEffect(() => {
    const focusable = () => Array.from(container.current?.querySelectorAll<HTMLElement>('button, a[href], input, textarea, select, [tabindex]:not([tabindex="-1"])') || []).filter((item) => !item.hasAttribute("disabled"));
    focusable()[0]?.focus();
    const handler = (event: KeyboardEvent) => {
      if (event.key === "Escape") closeHandler.current();
      if (event.key !== "Tab") return;
      const items = focusable();
      if (!items.length) return;
      const first = items[0], last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [container]);
}
