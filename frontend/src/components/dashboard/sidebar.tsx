"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { UserButton } from "@clerk/nextjs"
import { cn } from "cn"
import {
  LayoutDashboard,
  Users,
  Server,
  Activity,
  Package,
} from "lucide-react"

const NAV_ITEMS = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/students", label: "Students", icon: Users },
  { href: "/devices", label: "Devices", icon: Server },
  { href: "/events", label: "Events", icon: Activity },
  { href: "/items", label: "Items", icon: Package },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="flex h-screen w-60 shrink-0 flex-col border-r border-zinc-800 bg-zinc-950">
      {/* Logo */}
      <div className="flex h-14 items-center border-b border-zinc-800 px-5">
        <span className="font-mono text-sm font-semibold tracking-widest text-zinc-100">
          FRZR BURN
        </span>
        <span className="ml-2 rounded bg-zinc-800 px-1.5 py-0.5 font-mono text-[10px] text-zinc-400">
          ADMIN
        </span>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto px-3 py-4">
        <ul className="space-y-0.5">
          {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
            const active = pathname === href || pathname.startsWith(href + "/")
            return (
              <li key={href}>
                <Link
                  href={href}
                  className={cn(
                    "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                    active
                      ? "bg-zinc-800 text-zinc-100"
                      : "text-zinc-400 hover:bg-zinc-800/60 hover:text-zinc-200",
                  )}
                >
                  <Icon className="size-4 shrink-0" />
                  {label}
                </Link>
              </li>
            )
          })}
        </ul>
      </nav>

      {/* Footer */}
      <div className="flex items-center gap-3 border-t border-zinc-800 px-5 py-4">
        <UserButton
          appearance={{
            elements: { avatarBox: "size-7" },
          }}
        />
        <span className="truncate text-xs text-zinc-500">Admin</span>
      </div>
    </aside>
  )
}
