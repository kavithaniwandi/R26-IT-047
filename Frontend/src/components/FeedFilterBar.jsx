const categories = ['All', 'Chronic Illness', 'Emergency', 'Pediatric', 'Cancer', 'General OTC'];

const FeedFilterBar = ({ sortBy, onSortChange, activeCategory, onCategoryChange, visibleCount }) => {
  return (
    <div className="rounded-3xl border border-white/70 bg-white p-4 shadow-sm">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-3">
          <label className="text-sm font-medium text-slate-700" htmlFor="feed-sort">
            Sort by
          </label>
          <select
            id="feed-sort"
            value={sortBy}
            onChange={(event) => onSortChange(event.target.value)}
            className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm text-slate-700 outline-none transition focus:border-[#2D9E6B] focus:ring-2 focus:ring-[#2D9E6B]/15"
          >
            <option value="best-match">Best Match</option>
            <option value="urgency">Urgency</option>
            <option value="nearest-location">Nearest Location</option>
          </select>
        </div>

        <div className="flex flex-wrap gap-2">
          {categories.map((category) => {
            const isActive = activeCategory === category;
            return (
              <button
                key={category}
                type="button"
                onClick={() => onCategoryChange(category)}
                className={`rounded-full px-4 py-2 text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-[#2D9E6B] text-white shadow-sm'
                    : 'bg-[#F0FFF4] text-slate-700 hover:bg-[#E6FAEE]'
                }`}
              >
                {category}
              </button>
            );
          })}
        </div>
      </div>

      <p className="mt-4 text-sm text-slate-600">Showing {visibleCount} requests matched to your profile</p>
    </div>
  );
};

export default FeedFilterBar;