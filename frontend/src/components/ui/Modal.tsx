'use client';

import * as Dialog from '@radix-ui/react-dialog';
import { X } from 'lucide-react';
import { ReactNode } from 'react';

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  width?: string;
}

export default function Modal({ open, onClose, title, children, width = 'max-w-2xl' }: ModalProps) {
  return (
    <Dialog.Root open={open} onOpenChange={(v) => !v && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[200] animate-in fade-in-0" />
        <Dialog.Content
          className={`fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-[201] w-[95vw] ${width} rounded-xl bg-[#0f1729] border border-[#1e3a5f] shadow-2xl animate-in fade-in-0 zoom-in-95 max-h-[85vh] flex flex-col`}
        >
          <div className="flex items-center justify-between px-5 py-4 border-b border-[#1e3a5f]/60">
            <Dialog.Title className="text-base font-semibold text-white">{title}</Dialog.Title>
            <Dialog.Close asChild>
              <button className="p-1 rounded-md hover:bg-white/10 transition-colors text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </Dialog.Close>
          </div>
          <div className="flex-1 overflow-y-auto p-5">{children}</div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
