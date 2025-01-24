 <main className="container mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold">Insights</h1>
          <div className="flex space-x-4">
            <select className="form-select">
              <option>Last 7 days</option>
              <option>Last 30 days</option>
              <option>Last 3 months</option>
            </select>
            <button className="bg-blue-500 text-white px-4 py-2 rounded">
              Export
            </button>
          </div>
        </div>

        {loading ? (
          <div>Loading insights...</div>
        ) : (
          <InsightList insights={insights} />
        )}
      </main>
    </div>
  );
};

export default InsightsPage;
