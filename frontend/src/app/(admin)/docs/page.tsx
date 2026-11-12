"use client"

import { useEffect, useRef, useState } from "react"
import { docSections } from "@/lib/docs/content"
import { DocSectionView } from "@/components/docs/doc-section"
import { DocsNav } from "@/components/docs/docs-nav"

export default function DocsPage() {
  const [activeId, setActiveId] = useState(docSections[0]?.id ?? "")
  const observerRef = useRef<IntersectionObserver | null>(null)

  useEffect(() => {
    observerRef.current?.disconnect()

    observerRef.current = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setActiveId(entry.target.id)
            break
          }
        }
      },
      { rootMargin: "-20% 0px -70% 0px", threshold: 0 },
    )

    docSections.forEach((section) => {
      const el = document.getElementById(section.id)
      if (el) observerRef.current?.observe(el)
    })

    return () => observerRef.current?.disconnect()
  }, [])

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-xl font-semibold">Documentation</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          System guide for FRZR BURN admins
        </p>
      </div>

      {/* Two-column layout */}
      <div className="flex gap-8 items-start">
        {/* Sticky TOC */}
        <div className="w-52 shrink-0 sticky top-0">
          <DocsNav sections={docSections} activeId={activeId} />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0 rounded-lg border bg-white px-8 py-6">
          <div className="space-y-14">
            {docSections.map((section) => (
              <DocSectionView key={section.id} section={section} />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
