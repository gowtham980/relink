"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";

const links = [
  { href: "/home", label: "Home" },
  { href: "/check-in", label: "Check-in" },
  { href: "/plans", label: "Plans" },
  { href: "/urge", label: "Urge SOS" },
  { href: "/coach", label: "Coach" },
  { href: "/slip", label: "Slip" },
  { href: "/insights", label: "Insights" },
  { href: "/ethics", label: "Ethics" },
  { href: "/settings", label: "Settings" },
];

export function Shell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const hideNav = path === "/" || path === "/onboarding";

  return (
    <div className="mx-auto flex min-h-screen max-w-5xl flex-col px-4 pb-16 pt-4 sm:px-6">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded focus:bg-white focus:px-3 focus:py-2"
      >
        Skip to content
      </a>
      <header className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <Link href={hideNav ? "/" : "/home"} className="group flex items-center gap-2">
          <span
            className="flex h-9 w-9 items-center justify-center rounded-xl bg-pine text-sm font-bold text-white"
            aria-hidden
          >
            R
          </span>
          <div>
            <p className="font-display text-lg font-semibold leading-none text-ink">Relink</p>
            <p className="text-xs text-dusk">Pause · Plan · Practice</p>
          </div>
        </Link>
        <p className="max-w-xs text-right text-xs text-dusk" role="note">
          Wellness tool — not medical care.{" "}
          <Link href="/ethics" className="underline">
            Crisis help
          </Link>
        </p>
      </header>

      {!hideNav && (
        <nav aria-label="Primary" className="mb-6 overflow-x-auto">
          <ul className="flex min-w-max gap-1 rounded-2xl bg-white/70 p-1 shadow-sm ring-1 ring-black/5">
            {links.map((l) => {
              const active = path === l.href;
              return (
                <li key={l.href}>
                  <Link
                    href={l.href}
                    className={clsx(
                      "block rounded-xl px-3 py-2 text-sm font-medium transition",
                      active ? "bg-pine text-white" : "text-dusk hover:bg-black/5"
                    )}
                    aria-current={active ? "page" : undefined}
                  >
                    {l.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
      )}

      <main id="main" className="flex-1">
        {children}
      </main>
    </div>
  );
}
