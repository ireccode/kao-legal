"use client";

import { useEffect, useState } from "react";
import { getCreditBalance } from "@/lib/api";

export default function CreditsPage() {
  const [balance, setBalance] = useState<number | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getCreditBalance()
      .then((data) => setBalance(data.credits))
      .catch((err: unknown) =>
        setError(err instanceof Error ? err.message : "Failed to load balance")
      );
  }, []);

  return (
    <div className="max-w-2xl space-y-6">
      <h1 className="text-2xl font-bold">Credits</h1>

      {error && (
        <div className="p-3 bg-red-50 text-red-700 rounded">{error}</div>
      )}

      <div className="p-6 border rounded-xl">
        <p className="text-gray-600 mb-1">Current balance</p>
        <p className="text-4xl font-bold">
          {balance === null ? "..." : balance}
        </p>
        <p className="text-sm text-gray-500 mt-1">credits</p>
      </div>

      <div className="p-6 border rounded-xl space-y-4">
        <h2 className="font-semibold">Purchase Credits</h2>

        <div className="grid grid-cols-3 gap-4">
          {[
            { label: "Starter", dollars: 10, credits: 1000 },
            { label: "Professional", dollars: 25, credits: 2500 },
            { label: "Team", dollars: 50, credits: 5000 },
          ].map((pkg) => (
            <div key={pkg.label} className="p-4 border rounded-lg text-center">
              <p className="font-medium">{pkg.label}</p>
              <p className="text-2xl font-bold mt-1">${pkg.dollars}</p>
              <p className="text-sm text-gray-500">{pkg.credits} credits</p>
              <a
                href={`${process.env.NEXT_PUBLIC_STRIPE_PAYMENT_LINK}?amount=${pkg.dollars}`}
                className="mt-3 block px-3 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700"
              >
                Buy
              </a>
            </div>
          ))}
        </div>

        <div className="text-sm text-gray-500">
          <p>Credit costs: Meeting Summary = 10 credits, Document = 5 credits each</p>
        </div>
      </div>
    </div>
  );
}
