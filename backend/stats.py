import numpy as np
import statistics
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models import ExamScore, CachedStats, ExamSession

async def recalculate_stats(session_id: str, db: AsyncSession):
    # Fetch all scores for the session
    result = await db.execute(select(ExamScore.score_value).where(ExamScore.session_id == session_id))
    scores = result.scalars().all()
    
    if not scores:
        return None
        
    scores_array = np.array([float(s) for s in scores])
    
    # Calculate basic stats
    count = len(scores_array)
    mean = float(np.mean(scores_array))
    median = float(np.median(scores_array))
    std_dev = float(np.std(scores_array))
    minimum = float(np.min(scores_array))
    maximum = float(np.max(scores_array))
    q1 = float(np.percentile(scores_array, 25))
    q3 = float(np.percentile(scores_array, 75))
    
    # Mode
    try:
        modes = statistics.multimode([float(s) for s in scores_array])
        mode = float(modes[0]) # pick the first one if multiple
    except statistics.StatisticsError:
        mode = None

    # Histogram data
    session_res = await db.execute(select(ExamSession.max_marks).where(ExamSession.id == session_id))
    max_marks = session_res.scalar() or 100
    
    # 10 bins
    bins = np.linspace(0, max_marks, 11)
    hist, bin_edges = np.histogram(scores_array, bins=bins)
    
    histogram_data = {
        "labels": [f"{int(bin_edges[i])}-{int(bin_edges[i+1])}" for i in range(len(hist))],
        "data": hist.tolist()
    }
    
    # Interpretation Logic
    mean_pct = (mean / max_marks) * 100
    std_pct = (std_dev / max_marks) * 100
    
    if count < 3:
        interpretation = "📊 Waiting for more submissions to generate an accurate interpretation."
    elif mean_pct > 75 and std_pct < 15:
        interpretation = "✅ Strong comprehension. Most students scored near the top."
    elif mean_pct > 50 and std_pct > 25:
        interpretation = "⚠️ Polarized. Class divided between high and low performers."
    elif mean_pct < 40 and std_pct < 15:
        interpretation = "❌ Uniformly poor. Assessment may have been too difficult."
    elif mean_pct < 40 and std_pct > 25:
        interpretation = "🔶 Mixed low performance with high variance."
    elif 40 <= mean_pct <= 75 and std_pct < 15:
        interpretation = "📊 Consistent average performance with tight clustering."
    else:
        interpretation = "📈 Moderate performance with normal spread."

    # Upsert to DB
    stats_res = await db.execute(select(CachedStats).where(CachedStats.session_id == session_id))
    stats_obj = stats_res.scalar_one_or_none()
    
    if not stats_obj:
        stats_obj = CachedStats(session_id=session_id)
        db.add(stats_obj)
        
    stats_obj.mean = round(mean, 3)
    stats_obj.median = round(median, 3)
    stats_obj.mode = round(mode, 3) if mode is not None else None
    stats_obj.std_dev = round(std_dev, 3)
    stats_obj.min = round(minimum, 3)
    stats_obj.max = round(maximum, 3)
    stats_obj.q1 = round(q1, 3)
    stats_obj.q3 = round(q3, 3)
    stats_obj.count = count
    stats_obj.interpretation = interpretation
    stats_obj.histogram_json = json.dumps(histogram_data)
    stats_obj.raw_scores_json = json.dumps([float(s) for s in scores_array])

    await db.commit()
    await db.refresh(stats_obj)
    
    return {
        "session_id": stats_obj.session_id,
        "mean": stats_obj.mean,
        "median": stats_obj.median,
        "mode": stats_obj.mode,
        "std_dev": stats_obj.std_dev,
        "min": stats_obj.min,
        "max": stats_obj.max,
        "q1": stats_obj.q1,
        "q3": stats_obj.q3,
        "count": stats_obj.count,
        "interpretation": stats_obj.interpretation,
        "histogram_json": stats_obj.histogram_json,
        "raw_scores_json": stats_obj.raw_scores_json
    }
