import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import {
  ArrowLeft,
  Copy,
  Check,
  ExternalLink,
  Users,
  MousePointer,
  Smartphone,
  Laptop,
  Globe,
  Share2,
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { api } from "../api";

export default function AnalyticsPage() {
  const { code } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [days, setDays] = useState(30);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    let isMounted = true;
    api.analytics
      .get(code, days)
      .then((res) => {
        if (isMounted) {
          setData(res);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err.message || "Failed to load analytics.");
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [code, days]);

  const copyLink = () => {
    navigator.clipboard.writeText(`http://localhost:8000/${code}`);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-20 text-center">
        <div className="inline-block w-8 h-8 border-3 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin mb-3" />
        <p className="text-sm text-slate-400">Loading link analytics...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="max-w-xl mx-auto px-4 py-20 text-center">
        <div className="p-4 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-2xl text-sm mb-6">
          {error || "Could not load analytics."}
        </div>
        <Link
          to="/dashboard"
          className="inline-flex items-center gap-2 text-sm text-indigo-400 hover:text-indigo-300 font-medium"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Dashboard
        </Link>
      </div>
    );
  }

  const deviceChartData = Object.entries(data.devices || {}).map(([name, count]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    clicks: count,
  }));

  const browserChartData = Object.entries(data.browsers || {}).map(([name, count]) => ({
    name,
    clicks: count,
  }));

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      {/* Back button & Page Header */}
      <div className="mb-6">
        <Link
          to="/dashboard"
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition font-medium mb-4"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to Dashboard
        </Link>

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl sm:text-3xl font-bold text-white font-mono">
                /{data.short_code}
              </h1>
              <button
                onClick={copyLink}
                className="p-1.5 bg-slate-800 hover:bg-slate-700 rounded-lg text-slate-300 transition"
                title="Copy link"
              >
                {copied ? (
                  <Check className="w-4 h-4 text-emerald-400" />
                ) : (
                  <Copy className="w-4 h-4" />
                )}
              </button>
              <a
                href={`http://localhost:8000/${data.short_code}`}
                target="_blank"
                rel="noreferrer"
                className="p-1.5 bg-slate-800 hover:bg-slate-700 rounded-lg text-slate-300 transition"
                title="Test redirect"
              >
                <ExternalLink className="w-4 h-4" />
              </a>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Traffic performance and visitor demographics
            </p>
          </div>

          {/* Time range selector */}
          <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-xl p-1 self-start md:self-auto">
            {[7, 30, 90].map((d) => (
              <button
                key={d}
                onClick={() => setDays(d)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                  days === d
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                Last {d} days
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold uppercase tracking-wider">
            Total Clicks
            <MousePointer className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold text-white mt-2">
            {data.total_clicks.toLocaleString()}
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold uppercase tracking-wider">
            Unique Visitors
            <Users className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold text-white mt-2">
            {data.unique_visitors.toLocaleString()}
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold uppercase tracking-wider">
            Mobile Share
            <Smartphone className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold text-white mt-2">
            {data.total_clicks > 0
              ? `${Math.round(((data.devices.mobile || 0) / data.total_clicks) * 100)}%`
              : "0%"}
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold uppercase tracking-wider">
            Desktop Share
            <Laptop className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold text-white mt-2">
            {data.total_clicks > 0
              ? `${Math.round(((data.devices.desktop || 0) / data.total_clicks) * 100)}%`
              : "0%"}
          </div>
        </div>
      </div>

      {/* Daily Clicks Area Chart */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 mb-8">
        <h3 className="text-base font-bold text-white mb-6">Click Volume Over Time</h3>
        <div className="h-72 w-full">
          {data.daily_clicks && data.daily_clicks.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data.daily_clicks}>
                <defs>
                  <linearGradient id="clickGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="date" stroke="#94a3b8" fontSize={12} />
                <YAxis stroke="#94a3b8" fontSize={12} allowDecimals={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#0f172a",
                    border: "1px solid #1e293b",
                    borderRadius: "0.75rem",
                    color: "#fff",
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="clicks"
                  stroke="#6366f1"
                  strokeWidth={2.5}
                  fillOpacity={1}
                  fill="url(#clickGradient)"
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex items-center justify-center text-xs text-slate-500">
              No click volume recorded yet for this time window.
            </div>
          )}
        </div>
      </div>

      {/* Breakdowns Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Devices Breakdown */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <Smartphone className="w-4 h-4 text-indigo-400" />
            <h3 className="text-sm font-bold text-white">Device Breakdown</h3>
          </div>
          {deviceChartData.length > 0 ? (
            <div className="space-y-3">
              {deviceChartData.map((d) => {
                const pct = data.total_clicks > 0 ? Math.round((d.clicks / data.total_clicks) * 100) : 0;
                return (
                  <div key={d.name}>
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="text-slate-300 font-medium">{d.name}</span>
                      <span className="text-slate-500 font-mono">
                        {d.clicks} clicks ({pct}%)
                      </span>
                    </div>
                    <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden">
                      <div
                        className="bg-indigo-500 h-2 rounded-full"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-xs text-slate-500">No device data available.</p>
          )}
        </div>

        {/* Top Referrers */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <Share2 className="w-4 h-4 text-purple-400" />
            <h3 className="text-sm font-bold text-white">Top Referrers</h3>
          </div>
          {Object.keys(data.referrers || {}).length > 0 ? (
            <div className="space-y-2.5">
              {Object.entries(data.referrers).map(([ref, count]) => (
                <div
                  key={ref}
                  className="flex items-center justify-between p-2.5 bg-slate-950 rounded-xl border border-slate-800/80 text-xs"
                >
                  <span className="text-slate-300 font-medium truncate max-w-xs">{ref}</span>
                  <span className="text-slate-400 font-mono font-bold">{count} clicks</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-500">No referrer data available.</p>
          )}
        </div>

        {/* Top Browsers */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <Globe className="w-4 h-4 text-emerald-400" />
            <h3 className="text-sm font-bold text-white">Browser Usage</h3>
          </div>
          {browserChartData.length > 0 ? (
            <div className="space-y-2.5">
              {browserChartData.map((b) => (
                <div
                  key={b.name}
                  className="flex items-center justify-between p-2.5 bg-slate-950 rounded-xl border border-slate-800/80 text-xs"
                >
                  <span className="text-slate-300 font-medium">{b.name}</span>
                  <span className="text-slate-400 font-mono font-bold">{b.clicks} clicks</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-500">No browser data recorded.</p>
          )}
        </div>

        {/* Geographic Countries */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <Globe className="w-4 h-4 text-amber-400" />
            <h3 className="text-sm font-bold text-white">Geographic Distribution</h3>
          </div>
          {Object.keys(data.countries || {}).length > 0 ? (
            <div className="space-y-2.5">
              {Object.entries(data.countries).map(([country, count]) => (
                <div
                  key={country}
                  className="flex items-center justify-between p-2.5 bg-slate-950 rounded-xl border border-slate-800/80 text-xs"
                >
                  <span className="text-slate-300 font-medium">{country}</span>
                  <span className="text-slate-400 font-mono font-bold">{count} clicks</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-500">No country data recorded.</p>
          )}
        </div>
      </div>
    </div>
  );
}
