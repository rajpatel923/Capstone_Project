import type { DocSection, DocBlock } from "@/lib/docs/content"

function Block({ block }: { block: DocBlock }) {
  switch (block.type) {
    case "paragraph":
      return (
        <p className="text-sm text-muted-foreground leading-relaxed">
          {block.text}
        </p>
      )

    case "heading":
      return (
        <h3 className="text-sm font-semibold text-foreground mt-6 mb-2">
          {block.text}
        </h3>
      )

    case "list":
      return (
        <ul className="space-y-1.5 ml-1">
          {block.items.map((item, i) => (
            <li key={i} className="flex gap-2 text-sm text-muted-foreground">
              <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-zinc-400" />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      )

    case "steps":
      return (
        <ol className="space-y-2 ml-1">
          {block.items.map((item, i) => (
            <li key={i} className="flex gap-3 text-sm text-muted-foreground">
              <span className="flex size-5 shrink-0 items-center justify-center rounded-full bg-zinc-100 text-xs font-semibold text-zinc-600 mt-0.5">
                {i + 1}
              </span>
              <span className="pt-0.5">{item}</span>
            </li>
          ))}
        </ol>
      )

    case "code":
      return (
        <div className="rounded-lg overflow-hidden border border-zinc-200">
          {block.label && (
            <div className="bg-zinc-100 border-b border-zinc-200 px-4 py-1.5">
              <span className="text-xs font-medium text-zinc-500">{block.label}</span>
            </div>
          )}
          <pre className="bg-zinc-950 px-4 py-3 overflow-x-auto">
            <code className="font-mono text-xs leading-relaxed text-zinc-200">
              {block.lines.join("\n")}
            </code>
          </pre>
        </div>
      )

    case "callout": {
      const styles = {
        info: "border-blue-200 bg-blue-50 text-blue-800",
        warning: "border-amber-200 bg-amber-50 text-amber-800",
        tip: "border-green-200 bg-green-50 text-green-800",
      }
      const labels = { info: "Note", warning: "Important", tip: "Tip" }
      return (
        <div className={`rounded-lg border-l-4 px-4 py-3 text-sm ${styles[block.variant]}`}>
          <span className="font-semibold">{labels[block.variant]}: </span>
          {block.text}
        </div>
      )
    }

    case "table":
      return (
        <div className="overflow-x-auto rounded-lg border border-zinc-200">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-zinc-200 bg-zinc-50">
                {block.headers.map((h, i) => (
                  <th
                    key={i}
                    className="px-4 py-2.5 text-left text-xs font-semibold text-zinc-600 uppercase tracking-wider"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100 bg-white">
              {block.rows.map((row, i) => (
                <tr key={i}>
                  {row.map((cell, j) => (
                    <td
                      key={j}
                      className={`px-4 py-3 text-sm ${j === 0 ? "font-mono text-xs font-medium text-zinc-800" : "text-muted-foreground"}`}
                    >
                      {cell}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )

    default:
      return null
  }
}

type Props = {
  section: DocSection
}

export function DocSectionView({ section }: Props) {
  return (
    <section id={section.id} className="scroll-mt-6">
      <div className="mb-6 border-b border-zinc-200 pb-4">
        <h2 className="text-lg font-semibold text-foreground">{section.title}</h2>
        <p className="mt-0.5 text-sm text-muted-foreground">{section.description}</p>
      </div>
      <div className="space-y-4">
        {section.blocks.map((block, i) => (
          <Block key={i} block={block} />
        ))}
      </div>
    </section>
  )
}
