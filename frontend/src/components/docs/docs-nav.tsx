"use client"

import { cn } from "cn"
import type { DocSection } from "@/lib/docs/content"

type Props = {
  sections: DocSection[]
  activeId: string
}

export function DocsNav({ sections, activeId }: Props) {
  const handleClick = (e: React.MouseEvent<HTMLAnchorElement>, id: string) => {
    e.preventDefault()
    const el = document.getElementById(id)
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "start" })
    }
  }

  return (
    <nav>
      <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-zinc-400">
        On this page
      </p>
      <ul className="space-y-0.5">
        {sections.map((section) => {
          const active = activeId === section.id
          return (
            <li key={section.id}>
              <a
                href={`#${section.id}`}
                onClick={(e) => handleClick(e, section.id)}
                className={cn(
                  "block rounded-md px-3 py-2 text-sm transition-colors",
                  active
                    ? "bg-zinc-100 font-medium text-foreground"
                    : "text-muted-foreground hover:bg-zinc-50 hover:text-foreground",
                )}
              >
                {section.title}
              </a>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}
