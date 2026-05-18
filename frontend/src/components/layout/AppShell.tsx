import type { ReactNode } from "react";
import Image from "next/image";
import { Database } from "lucide-react";

/**
 * Props for the {@link AppShell} component.
 * children: The content to be rendered inside the shell.
 */
type AppShellProps = {
    children: ReactNode;
};

/**
 * Provides the fixed-height workspace shell used by the whole app.
 *
 * The children area intentionally owns its own scrolling so the chat and video
 * panes can keep independent scroll positions inside a stable viewport.
 */
export function AppShell({ children }: AppShellProps) {
    return (
        <main className="flex h-screen flex-col overflow-hidden bg-[#f6f8fb]">
            <header className="shrink-0 border-b border-slate-200 bg-white/95">
                <div className="mx-auto flex h-14 max-w-400 items-center justify-between px-4 sm:px-5 lg:px-6">
                    <div className="flex min-w-0 items-center gap-3">
                        <Image
                            src="/app-icon.svg"
                            alt=""
                            width={32}
                            height={32}
                            className="h-8 w-8 shrink-0 rounded-lg"
                        />

                        <div className="min-w-0">
                            <h1 className="truncate text-sm font-semibold text-slate-950 sm:text-base">
                                Video RAG Workspace
                            </h1>
                            <p className="truncate text-xs text-slate-500">
                                Social video analysis
                            </p>
                        </div>
                    </div>

                    <div className="hidden items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-xs font-medium text-slate-600 sm:flex">
                        <span className="h-2 w-2 rounded-full bg-emerald-500" />
                        <Database size={14} />
                        Chroma index
                    </div>
                </div>
            </header>

            <div className="mx-auto min-h-0 w-full max-w-[1600px] flex-1 overflow-hidden px-4 py-4 sm:px-5 lg:px-6">
                {children}
            </div>
        </main>
    );
}
