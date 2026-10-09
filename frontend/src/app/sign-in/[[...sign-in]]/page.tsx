import { SignIn } from "@clerk/nextjs"

export default function SignInPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50">
      <div className="space-y-4">
        <div className="text-center">
          <p className="font-mono text-xs tracking-widest text-zinc-400">FRZR BURN</p>
          <h1 className="mt-1 text-lg font-semibold">Admin Dashboard</h1>
        </div>
        <SignIn />
      </div>
    </div>
  )
}
