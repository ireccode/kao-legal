import { redirect } from "next/navigation";
import { cookies } from "next/headers";
import { runWithAmplifyServerContext } from "@aws-amplify/adapter-nextjs";
import { fetchAuthSession } from "aws-amplify/auth/server";

async function isAuthenticated(): Promise<boolean> {
  try {
    const authenticated = await runWithAmplifyServerContext({
      nextServerContext: { cookies },
      operation: async (contextSpec) => {
        const session = await fetchAuthSession(contextSpec);
        return !!session.tokens;
      },
    });
    return authenticated;
  } catch {
    return false;
  }
}

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const authenticated = await isAuthenticated();

  if (!authenticated) {
    redirect("/sign-in");
  }

  return (
    <div className="min-h-screen flex flex-col">
      <nav className="border-b px-6 py-3 flex gap-6">
        <a href="/meeting" className="text-blue-600 hover:underline">
          Meeting Summary
        </a>
        <a href="/documents" className="text-blue-600 hover:underline">
          Documents
        </a>
        <a href="/credits" className="text-blue-600 hover:underline">
          Credits
        </a>
      </nav>
      <main className="flex-1 p-8">{children}</main>
    </div>
  );
}
