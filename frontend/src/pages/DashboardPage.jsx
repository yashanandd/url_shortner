import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Plus,
  Copy,
  Check,
  ExternalLink,
  BarChart2,
  Trash2,
  Calendar,
  Search,
  Link2,
  X,
} from "lucide-react";
import { api, getCurrentUser } from "../api";

export default function DashboardPage() {
  const navigate = useNavigate();
  // Stable reference — getCurrentUser() parses JSON each call so must NOT go
  // in a useEffect dep array (new object every render → infinite loop).
  const [user] = useState(() => getCurrentUser());

  const [urls, setUrls] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [copiedId, setCopiedId] = useState(null);

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [originalUrl, setOriginalUrl] = useState("");
  const [customAlias, setCustomAlias] = useState("");
  const [expiresAt, setExpiresAt] = useState("");
  const [modalLoading, setModalLoading] = useState(false);
  const [modalError, setModalError] = useState("");

  const refreshUrls = async () => {
    try {
      const data = await api.urls.list(0, 100);
      setUrls(data);
    } catch (err) {
      console.error("Failed to refresh URLs:", err);
    }
  };

  useEffect(() => {
    if (!user) {
      navigate("/login");
      return;
    }
    let isMounted = true;
    api.urls
      .list(0, 100)
      .then((data) => {
        if (isMounted) {
          setUrls(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          console.error("Failed to load URLs:", err);
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [user, navigate]);

  const handleCreate = async (e) => {
    e.preventDefault();
    setModalError("");
    setModalLoading(true);

    try {
      const isoExpiry = expiresAt ? new Date(expiresAt).toISOString() : null;
      await api.urls.create(originalUrl.trim(), customAlias.trim() || null, isoExpiry);
      setIsModalOpen(false);
      setOriginalUrl("");
      setCustomAlias("");
      setExpiresAt("");
      await refreshUrls();
    } catch (err) {
      setModalError(err.message || "Failed to create short URL.");
    } finally {
      setModalLoading(false);
    }
  };

  const handleDelete = async (urlId) => {
    if (!window.confirm("Are you sure you want to delete this shortened link?")) return;
    try {
      await api.urls.delete(urlId);
      setUrls((prev) => prev.filter((u) => u.id !== urlId));
    } catch (err) {
      alert(err.message || "Could not delete link.");
    }
  };

  const handleCopy = (shortUrl, id) => {
    navigator.clipboard.writeText(shortUrl);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2500);
  };

  const filteredUrls = urls.filter((u) => {
    const q = searchQuery.toLowerCase();
    return (
      u.short_code.toLowerCase().includes(q) ||
      u.original_url.toLowerCase().includes(q) ||
      (u.custom_alias && u.custom_alias.toLowerCase().includes(q))
    );
  });

  const totalClicks = urls.reduce((acc, curr) => acc + (curr.total_clicks || 0), 0);
  const activeCount = urls.filter((u) => u.status === "ACTIVE").length;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      {/* Header and Action */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            Links Dashboard
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Manage your shortened URLs, monitor clicks, and analyze traffic.
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm transition shadow-md shadow-indigo-600/30"
        >
          <Plus className="w-4 h-4" />
          Create Link
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
          <div className="text-xs uppercase font-semibold text-slate-500 tracking-wider">
            Total Shortened Links
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold text-white mt-2">
            {urls.length}
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
          <div className="text-xs uppercase font-semibold text-slate-500 tracking-wider">
            Total Recorded Clicks
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold text-indigo-400 mt-2">
            {totalClicks.toLocaleString()}
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
          <div className="text-xs uppercase font-semibold text-slate-500 tracking-wider">
            Active Links
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold text-emerald-400 mt-2">
            {activeCount}
          </div>
        </div>
      </div>

      {/* Search Bar */}
      <div className="flex items-center gap-3 mb-6 bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5">
        <Search className="w-4 h-4 text-slate-500" />
        <input
          type="text"
          placeholder="Search by code, alias, or destination URL..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full bg-transparent text-sm text-white placeholder-slate-500 focus:outline-none"
        />
      </div>

      {/* URLs Table / Cards */}
      {loading ? (
        <div className="text-center py-20">
          <div className="inline-block w-8 h-8 border-3 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin mb-3" />
          <p className="text-sm text-slate-400">Loading your shortened links...</p>
        </div>
      ) : filteredUrls.length === 0 ? (
        <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-12 text-center">
          <div className="p-3 bg-indigo-500/10 w-fit rounded-xl mx-auto mb-3 text-indigo-400">
            <Link2 className="w-6 h-6" />
          </div>
          <h3 className="text-base font-semibold text-white">No links found</h3>
          <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
            {searchQuery
              ? "No links matched your search query."
              : "You haven't created any shortened links yet. Click 'Create Link' to get started."}
          </p>
        </div>
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
          <div className="divide-y divide-slate-800">
            {filteredUrls.map((u) => (
              <div
                key={u.id}
                className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-slate-800/40 transition"
              >
                <div className="space-y-1.5 min-w-0 flex-1">
                  <div className="flex items-center gap-3 flex-wrap">
                    <a
                      href={u.short_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-base font-bold text-indigo-400 hover:underline inline-flex items-center gap-1.5 font-mono"
                    >
                      {u.short_url}
                      <ExternalLink className="w-3.5 h-3.5" />
                    </a>

                    <button
                      onClick={() => handleCopy(u.short_url, u.id)}
                      className="p-1 rounded text-slate-400 hover:text-white transition"
                      title="Copy short link"
                    >
                      {copiedId === u.id ? (
                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                      ) : (
                        <Copy className="w-3.5 h-3.5" />
                      )}
                    </button>

                    <span
                      className={`text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full ${
                        u.status === "ACTIVE"
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                      }`}
                    >
                      {u.status}
                    </span>
                  </div>

                  <div className="text-xs text-slate-400 truncate max-w-xl">
                    <span className="text-slate-500 font-medium mr-1.5">Destination:</span>
                    {u.original_url}
                  </div>

                  <div className="flex items-center gap-4 text-[11px] text-slate-500">
                    <span className="inline-flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      {new Date(u.created_at).toLocaleDateString()}
                    </span>
                    {u.expires_at && (
                      <span className="text-amber-400">
                        Expires: {new Date(u.expires_at).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-3 shrink-0">
                  <div className="text-right mr-2">
                    <div className="text-base font-bold text-white">
                      {(u.total_clicks || 0).toLocaleString()}
                    </div>
                    <div className="text-[10px] text-slate-500 uppercase tracking-wider">
                      Clicks
                    </div>
                  </div>

                  <Link
                    to={`/analytics/${u.short_code}`}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 transition"
                  >
                    <BarChart2 className="w-3.5 h-3.5 text-indigo-400" />
                    Analytics
                  </Link>

                  <button
                    onClick={() => handleDelete(u.id)}
                    className="p-1.5 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-slate-800 transition"
                    title="Delete link"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Create Link Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800 mb-5">
              <h3 className="text-lg font-bold text-white">Create New Short Link</h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {modalError && (
              <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs rounded-xl">
                {modalError}
              </div>
            )}

            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                  Destination URL *
                </label>
                <input
                  type="url"
                  required
                  placeholder="https://example.com/very/long/destination"
                  value={originalUrl}
                  onChange={(e) => setOriginalUrl(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                  Custom Alias (Optional)
                </label>
                <div className="flex items-center">
                  <span className="px-3 py-2.5 bg-slate-950 border border-r-0 border-slate-700 rounded-l-xl text-xs text-slate-500 font-mono">
                    /
                  </span>
                  <input
                    type="text"
                    placeholder="custom-alias"
                    value={customAlias}
                    onChange={(e) => setCustomAlias(e.target.value)}
                    className="flex-1 bg-slate-950 border border-slate-700 rounded-r-xl px-3 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                  Expiration Date (Optional)
                </label>
                <input
                  type="datetime-local"
                  value={expiresAt}
                  onChange={(e) => setExpiresAt(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-sm font-medium text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={modalLoading}
                  className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium px-5 py-2 rounded-xl text-sm shadow-md transition"
                >
                  {modalLoading ? "Creating..." : "Create Link"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
