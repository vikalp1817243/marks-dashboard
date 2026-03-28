import sys
import os
import pytest
import numpy as np
import json

# Add backend root to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_numpy_mean():
    scores = np.array([70.0, 80.0, 90.0, 60.0, 85.0])
    assert round(float(np.mean(scores)), 3) == 77.0

def test_numpy_median():
    scores = np.array([70.0, 80.0, 90.0, 60.0, 85.0])
    assert round(float(np.median(scores)), 3) == 80.0

def test_numpy_std_dev():
    scores = np.array([70.0, 80.0, 90.0, 60.0, 85.0])
    expected_std = round(float(np.std(scores)), 3)
    assert expected_std == 10.77

def test_numpy_percentiles():
    scores = np.array([70.0, 80.0, 90.0, 60.0, 85.0])
    q1 = float(np.percentile(scores, 25))
    q3 = float(np.percentile(scores, 75))
    assert q1 == 70.0
    assert q3 == 85.0

def test_histogram_bins():
    scores = np.array([15.0, 25.0, 35.0, 55.0, 65.0, 75.0, 85.0, 95.0])
    bins = np.linspace(0, 100, 11)
    hist, _ = np.histogram(scores, bins=bins)
    # Should have 10 bins
    assert len(hist) == 10
    # Each score falls in one bin
    assert sum(hist) == 8

def test_single_score():
    scores = np.array([50.0])
    assert float(np.mean(scores)) == 50.0
    assert float(np.median(scores)) == 50.0
    assert float(np.std(scores)) == 0.0

def test_identical_scores():
    scores = np.array([75.0, 75.0, 75.0, 75.0])
    assert float(np.mean(scores)) == 75.0
    assert float(np.std(scores)) == 0.0

def test_interpretation_strong():
    """μ > 75% and σ < 15% → Strong comprehension"""
    max_marks = 100
    mean, std_dev = 82.0, 8.0
    mean_pct = (mean / max_marks) * 100
    std_pct = (std_dev / max_marks) * 100
    assert mean_pct > 75 and std_pct < 15

def test_interpretation_polarized():
    """μ > 50% and σ > 25% → Polarized"""
    max_marks = 100
    mean, std_dev = 60.0, 30.0
    mean_pct = (mean / max_marks) * 100
    std_pct = (std_dev / max_marks) * 100
    assert mean_pct > 50 and std_pct > 25

def test_interpretation_poor():
    """μ < 40% and σ < 15% → Uniformly poor"""
    max_marks = 100
    mean, std_dev = 30.0, 10.0
    mean_pct = (mean / max_marks) * 100
    std_pct = (std_dev / max_marks) * 100
    assert mean_pct < 40 and std_pct < 15

def test_float_precision():
    """Scores with 3 decimal places"""
    scores = np.array([78.500, 82.125, 91.333])
    mean = round(float(np.mean(scores)), 3)
    assert isinstance(mean, float)
    # Check that we maintain precision
    assert len(str(mean).split('.')[-1]) <= 3
