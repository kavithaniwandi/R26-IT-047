const PriorityFeedPlaceholder = () => {
  return (
    <div className="rounded-3xl border border-dashed border-amber-300 bg-[#D69E2E]/10 p-8 shadow-sm">
      <div className="mx-auto flex max-w-2xl flex-col items-center text-center">
        <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-white text-amber-600 shadow-sm">
          <span className="text-2xl">⚑</span>
        </div>
        <h3 className="text-xl font-semibold text-slate-900">Trending Requests</h3>
        <p className="mt-3 text-sm leading-6 text-slate-600">
          Priority Feed — implemented by team member. Plug in &lt;PriorityFeed /&gt; component here.
        </p>
      </div>
    </div>
  );
};

export default PriorityFeedPlaceholder;