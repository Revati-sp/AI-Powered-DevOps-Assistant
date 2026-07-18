import Link from "next/link";

import { APP_NAME } from "@/lib/constants/app";

function InfrastructureVisual() {
  return (
    <div className="relative hidden h-full w-full overflow-hidden lg:block" aria-hidden>
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_20%_20%,#0f766e_0%,transparent_50%),radial-gradient(ellipse_at_80%_70%,#0891b2_0%,transparent_45%),linear-gradient(160deg,#0f172a_0%,#042f2e_45%,#0b252a_100%)]" />
      <div className="absolute inset-0 [background-image:linear-gradient(rgba(45,212,191,0.08)_1px,transparent_1px),linear-gradient(90deg,rgba(45,212,191,0.08)_1px,transparent_1px)] [background-size:48px_48px] opacity-40" />

      <svg
        className="absolute inset-0 h-full w-full"
        viewBox="0 0 640 800"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        <path
          d="M120 180 C220 160, 280 240, 360 220 C440 200, 480 280, 540 260"
          stroke="#2dd4bf"
          strokeWidth="1.5"
          strokeOpacity="0.55"
          className="animate-pulse"
        />
        <path
          d="M80 420 C180 380, 240 480, 340 450 C440 420, 500 520, 580 490"
          stroke="#22d3ee"
          strokeWidth="1.25"
          strokeOpacity="0.4"
        />
        <path
          d="M140 620 C240 580, 300 680, 420 640 C500 610, 540 700, 600 670"
          stroke="#5eead4"
          strokeWidth="1.25"
          strokeOpacity="0.35"
        />

        {[
          [160, 190],
          [360, 220],
          [520, 255],
          [120, 430],
          [340, 450],
          [560, 495],
          [220, 600],
          [420, 640],
        ].map(([cx, cy], index) => (
          <g key={`${cx}-${cy}`} filter="url(#glow)">
            <circle cx={cx} cy={cy} r={index % 2 === 0 ? 7 : 5} fill="#2dd4bf" fillOpacity="0.85">
              <animate
                attributeName="r"
                values={index % 2 === 0 ? "7;10;7" : "5;8;5"}
                dur={`${2.4 + (index % 3) * 0.4}s`}
                repeatCount="indefinite"
              />
              <animate
                attributeName="opacity"
                values="0.55;1;0.55"
                dur={`${2.4 + (index % 3) * 0.4}s`}
                repeatCount="indefinite"
              />
            </circle>
            <rect
              x={cx - 18}
              y={cy - 18}
              width="36"
              height="36"
              rx="6"
              stroke="#99f6e4"
              strokeOpacity="0.25"
              strokeWidth="1"
            />
          </g>
        ))}

        <text
          x="64"
          y="720"
          fill="#99f6e4"
          fillOpacity="0.55"
          fontSize="12"
          fontFamily="ui-monospace, SFMono-Regular, Menlo, monospace"
        >
          pipelines · infra · reviews · chat
        </text>
      </svg>

      <div className="absolute inset-x-0 bottom-0 p-10">
        <p className="max-w-sm text-lg font-medium text-teal-50/95">
          Ship safer infrastructure with an AI teammate that understands your stack.
        </p>
      </div>
    </div>
  );
}

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="bg-background flex min-h-svh">
      <div className="relative hidden w-[48%] lg:block">
        <InfrastructureVisual />
      </div>

      <div className="flex w-full flex-col lg:w-[52%]">
        <header className="border-border/60 from-primary/15 via-background to-background border-b bg-gradient-to-b px-6 py-5 lg:border-none lg:bg-none lg:px-10 lg:pt-10">
          <Link
            href="/"
            className="text-foreground inline-flex items-center gap-2 text-sm font-semibold tracking-tight"
          >
            <span className="bg-primary/15 text-primary inline-flex h-8 w-8 items-center justify-center rounded-md text-xs font-bold">
              ADA
            </span>
            <span className="max-w-[16rem] truncate sm:max-w-none">{APP_NAME}</span>
          </Link>
        </header>

        <main
          id="main-content"
          tabIndex={-1}
          className="flex flex-1 items-center justify-center px-6 py-10 outline-none lg:px-16"
        >
          <div className="w-full max-w-md">{children}</div>
        </main>
      </div>
    </div>
  );
}
