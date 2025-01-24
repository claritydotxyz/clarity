import pytest
import torch
import numpy as np
from clarity.ml.models.attention import MultiHeadAttention
from clarity.ml.models.clustering import BehaviorClusterer
from clarity.ml.models.sequence import BehaviorSequenceModel

def test_attention_model():
    model = MultiHeadAttention(d_model=64, num_heads=4)
    x = torch.randn(2, 10, 64)
    
    output = model(x, x, x)
    
    assert output.output.shape == x.shape
    assert output.attention_weights.shape[1] == 4

def test_clustering():
    clusterer = BehaviorClusterer(n_clusters=3)
    data = np.random.rand(100, 5)
    timestamps = np.arange(100)
    
    result = clusterer.fit_predict(data, timestamps)
    
    assert len(result.labels) == len(data)
    assert len(result.cluster_stats) == 3
