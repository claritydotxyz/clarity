import pytest
from datetime import datetime
from clarity.core.engine.analyzer import InsightAnalyzer
from clarity.core.engine.processor import DataProcessor

async def test_insight_generation():
    analyzer = InsightAnalyzer()
    test_data = {
        "user_id": 1,
        "start_date": datetime.now() - timedelta(days=7),
        "end_date": datetime.now()
    }
    
    result = await analyzer.analyze_user_data(**test_data)
    
    assert "insights" in result
    assert "recommendations" in result
    assert len(result["insights"]) > 0

def test_data_processing():
    processor = DataProcessor()
    test_data = {
        "metrics": [1, 2, 3],
        "categories": ["A", "B", "C"]
    }
    
    processed = processor.process_data(test_data)
    
    assert "metrics" in processed
    assert "processed_at" in processed
    assert len(processed["metrics"]) == len(test_data["metrics"])
