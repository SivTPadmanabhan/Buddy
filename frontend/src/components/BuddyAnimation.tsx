/* ============================================================
 * EXPERIMENTAL: Animated Jack Russell Terrier line art
 *
 * This entire component is experimental. If the animation
 * doesn't look right, this file can be deleted and the
 * <BuddyAnimation /> usage in App.tsx removed with no
 * other changes needed.
 * ============================================================ */

export default function BuddyAnimation() {
  return (
    <div className="flex flex-col items-center gap-4 select-none">
      <svg
        viewBox="0 0 200 180"
        width="160"
        height="144"
        className="buddy-jrt"
        aria-label="Buddy the Jack Russell Terrier"
      >
        {/* Neck */}
        <path
          d="M80 170 Q85 130 90 110 Q95 95 105 90 Q115 95 110 110 Q115 130 120 170"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          className="jrt-neck"
        />

        {/* Head outline */}
        <ellipse
          cx="100" cy="72" rx="38" ry="32"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          className="jrt-head"
        />

        {/* Left ear (floppy) */}
        <path
          d="M68 58 Q55 35 50 50 Q48 62 64 68"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          className="jrt-ear-left"
        />

        {/* Right ear (floppy) */}
        <path
          d="M132 58 Q145 35 150 50 Q152 62 136 68"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          className="jrt-ear-right"
        />

        {/* Left eye */}
        <circle cx="86" cy="68" r="4" fill="currentColor" className="jrt-eye" />

        {/* Right eye */}
        <circle cx="114" cy="68" r="4" fill="currentColor" className="jrt-eye" />

        {/* Eye shine */}
        <circle cx="87.5" cy="66.5" r="1.5" fill="white" />
        <circle cx="115.5" cy="66.5" r="1.5" fill="white" />

        {/* Nose */}
        <ellipse cx="100" cy="82" rx="5" ry="3.5" fill="currentColor" className="jrt-nose" />

        {/* Mouth / smile — animated between closed and open (bark) */}
        <path
          d="M92 88 Q96 93 100 88 Q104 93 108 88"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          className="jrt-mouth"
        />

        {/* Tongue (visible during bark) */}
        <path
          d="M98 89 Q100 98 102 89"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          className="jrt-tongue"
        />

        {/* Spot marking on face */}
        <path
          d="M82 55 Q90 48 100 52 Q95 60 85 58"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.2"
          strokeLinecap="round"
          opacity="0.3"
        />
      </svg>

      <style>{`
        .buddy-jrt {
          color: var(--color-emerald-dark, #059669);
          filter: drop-shadow(0 2px 8px rgba(52, 211, 153, 0.2));
        }

        .dark .buddy-jrt {
          color: var(--color-emerald-primary, #34D399);
          filter: drop-shadow(0 2px 12px rgba(52, 211, 153, 0.3));
        }

        /* Head bob */
        .jrt-head, .jrt-ear-left, .jrt-ear-right,
        .jrt-eye, .jrt-nose, .jrt-mouth, .jrt-tongue {
          animation: headBob 3s ease-in-out infinite;
        }

        @keyframes headBob {
          0%, 100% { transform: translateY(0px); }
          15% { transform: translateY(-3px); }
          30% { transform: translateY(0px); }
          50% { transform: translateY(-2px); }
          65% { transform: translateY(0px); }
        }

        /* Ear wiggle */
        .jrt-ear-left {
          transform-origin: 64px 68px;
          animation: earWiggleL 3s ease-in-out infinite;
        }

        .jrt-ear-right {
          transform-origin: 136px 68px;
          animation: earWiggleR 3s ease-in-out infinite;
        }

        @keyframes earWiggleL {
          0%, 100% { transform: rotate(0deg) translateY(0); }
          15% { transform: rotate(-8deg) translateY(-3px); }
          30% { transform: rotate(0deg) translateY(0); }
          50% { transform: rotate(-5deg) translateY(-2px); }
          65% { transform: rotate(0deg) translateY(0); }
        }

        @keyframes earWiggleR {
          0%, 100% { transform: rotate(0deg) translateY(0); }
          15% { transform: rotate(8deg) translateY(-3px); }
          30% { transform: rotate(0deg) translateY(0); }
          50% { transform: rotate(5deg) translateY(-2px); }
          65% { transform: rotate(0deg) translateY(0); }
        }

        /* Mouth bark */
        .jrt-mouth {
          animation: bark 3s ease-in-out infinite;
        }

        @keyframes bark {
          0%, 30%, 65%, 100% {
            d: path("M92 88 Q96 93 100 88 Q104 93 108 88");
          }
          15%, 50% {
            d: path("M92 88 Q96 97 100 92 Q104 97 108 88");
          }
        }

        /* Tongue visibility synced with bark */
        .jrt-tongue {
          opacity: 0;
          animation: tongueShow 3s ease-in-out infinite;
        }

        @keyframes tongueShow {
          0%, 30%, 65%, 100% { opacity: 0; }
          15%, 50% { opacity: 1; }
        }

        /* Eye blink */
        .jrt-eye {
          animation: blink 4s ease-in-out infinite;
        }

        @keyframes blink {
          0%, 95%, 100% { transform: scaleY(1) translateY(0); }
          97% { transform: scaleY(0.1) translateY(0); }
        }

        /* Entrance */
        .buddy-jrt {
          animation: fadeInUp 0.8s ease-out both;
        }

        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
  );
}

/* ============================================================
 * END EXPERIMENTAL: Animated Jack Russell Terrier
 * ============================================================ */
