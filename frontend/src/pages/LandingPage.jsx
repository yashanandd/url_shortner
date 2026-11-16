import { useState } from "react";
import {
  Copy,
  Check,
  ExternalLink,
  Zap,
  ShieldCheck,
  BarChart3,
  ArrowRight,
} from "lucide-react";
import { api } from "../api";

export default function LandingPage() {
  const [longUrl, setLongUrl] = useState("");
  const [customAlias, setCustomAlias] = useState("");
  const [showAlias, setShowAlias] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [createdUrl, setCreatedUrl] = useState(null);
  const [copied, setCopied] = useState(false);

  const handleShorten = async (e) => {
    e.preventDefault();
    setError("");
    setCreatedUrl(null);
    setCopied(false);

    if (!longUrl.trim()) {
      setError("Please enter a destination URL.");
      return;
    }

    setLoading(true);
    try {
      const res = await api.urls.create(longUrl.trim(), customAlias.trim() || null);
      setCreatedUrl(res);
      setLongUrl("");
      setCustomAlias("");
    } catch (err) {
      setError(err.message || "Failed to shorten URL.");
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = () => {
    if (!createdUrl) return;
    navigator.clipboard.writeText(createdUrl.short_url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] flex flex-col justify-between">
      {/* Hero Section */}
      <div className="max-w-5xl mx-auto px-4 pt-16 pb-12 sm:pt-24 text-center">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-semibold mb-6">
          <Zap className="w-3.5 h-3.5 text-indigo-400" />
          Production-Scale URL Engine & Analytics
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-white mb-6">
          Transform long URLs into <br className="hidden sm:inline" />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-purple-300 to-indigo-200">
            high-speed, trackable links.
          </span>
        </h1>

        <p className="max-w-2xl mx-auto text-base sm:text-lg text-slate-400 mb-10">
          LinkFlow delivers sub-millisecond redirection backed by Redis caching,
          real-time click analytics via Redis Streams, and enterprise-grade SSRF defense.
        </p>

        {/* Shortener Box */}
        <div className="max-w-2xl mx-auto bg-slate-900 border border-slate-800 rounded-2xl p-4 sm:p-6 shadow-2xl shadow-indigo-950/20 text-left">
          <form onSubmit={handleShorten} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                Enter Destination URL
              </label>
              <div className="flex flex-col sm:flex-row gap-2">
                <input
                  type="url"
                  placeholder="https://example.com/very/long/campaign-url"
                  value={longUrl}
                  onChange={(e) => setLongUrl(e.target.value)}
                  required
                  className="flex-1 bg-slate-950 border border-slate-700 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
                />
                <button
                  type="submit"
                  disabled={loading}
                  className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium px-6 py-3 rounded-xl text-sm transition flex items-center justify-center gap-2 whitespace-nowrap shadow-md shadow-indigo-600/30"
                >
                  {loading ? (
                    <span className="inline-block w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                  ) : (
                    <>
                      Shorten URL
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Custom Alias Toggle */}
            <div className="pt-1">
              <button
                type="button"
                onClick={() => setShowAlias(!showAlias)}
                className="text-xs text-indigo-400 hover:text-indigo-300 transition font-medium"
              >
                {showAlias ? "− Hide custom alias" : "+ Add custom alias"}
              </button>

              {showAlias && (
                <div className="mt-2 flex items-center gap-2">
                  <span className="text-xs text-slate-500 font-mono">http://localhost:8000/</span>
                  <input
                    type="text"
                    placeholder="my-custom-name"
                    value={customAlias}
                    onChange={(e) => setCustomAlias(e.target.value)}
                    className="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono"
                  />
                </div>
              )}
            </div>

            {error && (
              <div className="p-3 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs rounded-xl">
                {error}
              </div>
            )}
          </form>

          {/* Result Card */}
          {createdUrl && (
            <div className="mt-6 pt-5 border-t border-slate-800">
              <div className="flex items-center justify-between p-3.5 bg-slate-950 rounded-xl border border-indigo-500/30">
                <div className="truncate mr-3">
                  <div className="text-xs text-slate-400 mb-0.5">Shortened link:</div>
                  <a
                    href={createdUrl.short_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-indigo-400 font-mono text-sm font-semibold hover:underline inline-flex items-center gap-1.5"
                  >
                    {createdUrl.short_url}
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={copyToClipboard}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-indigo-600 hover:bg-indigo-500 text-white transition"
                  >
                    {copied ? (
                      <>
                        <Check className="w-3.5 h-3.5 text-emerald-300" />
                        Copied!
                      </>
                    ) : (
                      <>
                        <Copy className="w-3.5 h-3.5" />
                        Copy
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Feature Highlights Grid */}
      <div className="max-w-6xl mx-auto px-4 py-16 sm:py-20 border-t border-slate-800/80">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition">
            <div className="p-3 bg-indigo-500/10 w-fit rounded-xl mb-4 text-indigo-400">
              <Zap className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Sub-Millisecond Redirects</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Cached via Redis with anti-stampede 60s negative caching and 24h active invalidation, guaranteeing lightning-fast p95 latency.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition">
            <div className="p-3 bg-purple-500/10 w-fit rounded-xl mb-4 text-purple-400">
              <BarChart3 className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-white mb-2">Decoupled Analytics</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Clicks are enqueued via Redis Streams (<code className="text-xs text-purple-300">XADD</code>) and batch-ingested into PostgreSQL without delaying visitor redirects.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition">
            <div className="p-3 bg-emerald-500/10 w-fit rounded-xl mb-4 text-emerald-400">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-white mb-2">SSRF & Abuse Shield</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Automatic private/loopback IP network filtering, circular redirect detection, and sliding-window rate limiting.
            </p>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-6 text-center text-xs text-slate-500">
        LinkFlow © 2026 · Production-scale URL Shortening & Analytics Platform
      </footer>
    </div>
  );
}
