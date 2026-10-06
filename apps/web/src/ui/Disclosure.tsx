import { useEffect, useId, useRef, useState } from 'react';
import type { KeyboardEvent, ReactNode } from 'react';

/**
 * Pestañas, acordeón y ventana (F3 del rediseño).
 *
 * Los tres esconden o cambian lo que se ve, así que los tres tienen que decir en voz alta qué está
 * pasando: las pestañas con `aria-selected`, el acordeón con `aria-expanded` y una región que se puede
 * plegar, y la ventana con el `<dialog>` del navegador, que ya trae el foco atrapado y el `Esc`.
 */

export interface TabsProps {
  tabs: readonly { id: string; label: string }[];
  active: string;
  onChange: (id: string) => void;
  children: ReactNode;
}

export function Tabs({ tabs, active, onChange, children }: TabsProps) {
  const base = useId();
  // Con el teclado se cambia de pestaña con las flechas, como en cualquier barra de pestañas.
  const alPulsar = (evento: KeyboardEvent<HTMLDivElement>): void => {
    const indice = tabs.findIndex((tab) => tab.id === active);
    if (evento.key === 'ArrowRight' || evento.key === 'ArrowLeft') {
      evento.preventDefault();
      const paso = evento.key === 'ArrowRight' ? 1 : -1;
      const siguiente = tabs[(indice + paso + tabs.length) % tabs.length];
      if (siguiente !== undefined) {
        onChange(siguiente.id);
      }
    }
  };

  return (
    <div>
      <div className="ui-tabs" role="tablist" tabIndex={-1} onKeyDown={alPulsar}>
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            role="tab"
            id={`${base}-${tab.id}`}
            className="ui-tabs__tab"
            aria-selected={tab.id === active}
            aria-controls={`${base}-${tab.id}-panel`}
            tabIndex={tab.id === active ? 0 : -1}
            onClick={() => onChange(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div role="tabpanel" id={`${base}-${active}-panel`} aria-labelledby={`${base}-${active}`}>
        {children}
      </div>
    </div>
  );
}

export interface AccordionItem {
  id: string;
  title: string;
  children: ReactNode;
}

export interface AccordionProps {
  items: readonly AccordionItem[];
  /** Los que empiezan abiertos. */
  open?: readonly string[];
}

export function Accordion({ items, open = [] }: AccordionProps) {
  const [abiertos, setAbiertos] = useState<readonly string[]>(open);
  const alternar = (id: string): void => {
    setAbiertos((actuales) =>
      actuales.includes(id) ? actuales.filter((otro) => otro !== id) : [...actuales, id],
    );
  };
  return (
    <div>
      {items.map((item) => {
        const abierto = abiertos.includes(item.id);
        return (
          <div key={item.id} className="ui-accordion__item">
            <h3 style={{ margin: 0 }}>
              <button
                type="button"
                className="ui-accordion__trigger"
                aria-expanded={abierto}
                aria-controls={`acordeon-${item.id}`}
                onClick={() => alternar(item.id)}
              >
                {item.title}
                <span aria-hidden="true">{abierto ? '−' : '+'}</span>
              </button>
            </h3>
            <div id={`acordeon-${item.id}`} className="ui-accordion__panel" hidden={!abierto}>
              {item.children}
            </div>
          </div>
        );
      })}
    </div>
  );
}

export interface ModalProps {
  open: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
}

export function Modal({ open, title, onClose, children }: ModalProps) {
  const referencia = useRef<HTMLDialogElement>(null);
  // `showModal` es lo que da el foco atrapado y el `Esc`; abrir el `dialog` a mano no lo hace. Se
  // sincroniza en un efecto y **no** al pintar: tocar el DOM durante el render es lo que prohíbe React.
  useEffect(() => {
    const dialogo = referencia.current;
    if (dialogo === null) {
      return;
    }
    if (open && !dialogo.open) {
      dialogo.showModal();
    }
    if (!open && dialogo.open) {
      dialogo.close();
    }
  }, [open]);

  return (
    <dialog
      ref={referencia}
      className="ui-modal"
      aria-label={title}
      onCancel={(evento) => {
        evento.preventDefault();
        onClose();
      }}
    >
      <h2 className="ui-card__title">{title}</h2>
      {children}
    </dialog>
  );
}
