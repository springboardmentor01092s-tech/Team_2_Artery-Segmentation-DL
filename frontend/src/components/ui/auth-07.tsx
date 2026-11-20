import type { ReactNode } from "react";

type Auth7Props = {
  title: string;
  description: string;
  social?: ReactNode;
  children: ReactNode;
  footer: ReactNode;
};

/** Adapted from Watermelon UI auth-07 for CoroVision AI. */
export default function Auth7({ title, description, social, children, footer }: Auth7Props) {
  return (
    <main className="wm-auth flex min-h-screen w-full bg-white font-sans text-neutral-950 antialiased">
      <section className="relative flex min-h-screen w-full flex-col lg:w-1/2" aria-labelledby="auth-title">
        <div className="wm-auth-brand">
          <img src="/corovision-heart-mark.png" alt="" />
          <span>CoroVision AI</span>
        </div>

        <div className="flex flex-1 items-center justify-center px-6 pb-12 pt-28 md:px-10 lg:pt-24">
          <div className="w-full max-w-[420px]">
            <div className="mb-7 text-center">
              <h1 id="auth-title" className="mb-2 text-3xl font-semibold tracking-tight text-neutral-900 md:text-4xl">{title}</h1>
              <p className="text-sm leading-6 text-neutral-500">{description}</p>
            </div>

            {social && <div>{social}</div>}
            {social && (
              <div className="relative my-6 flex items-center" aria-hidden="true">
                <div className="grow border-t border-neutral-200" />
                <span className="px-4 text-sm text-neutral-400">or</span>
                <div className="grow border-t border-neutral-200" />
              </div>
            )}

            <div>{children}</div>
            <div className="mt-6 text-center text-sm text-neutral-500">{footer}</div>
          </div>
        </div>

        <p className="wm-auth-disclaimer">CoroVision AI research prototype · Use de-identified images only.</p>
      </section>

      <aside className="relative hidden min-h-screen p-4 lg:block lg:w-1/2" aria-label="CoroVision AI visual">
        <div className="wm-auth-image-panel">
          <img src="/auth-7.avif" alt="" fetchPriority="high" className="absolute inset-0 h-full w-full object-cover" />
          <div className="wm-auth-image-overlay" />
          <div className="wm-auth-image-copy">
            <span>ADVANCED CORONARY IMAGING</span>
            <h2>See the vessels.<br />Detect the narrowing.<br />Understand the results.</h2>
          </div>
        </div>
      </aside>
    </main>
  );
}
