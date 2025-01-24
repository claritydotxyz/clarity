from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from clarity.models.activity import UserActivity
from clarity.schemas.temporal import TemporalPattern, TimeBlock, DaySegment, WeekSegment
from clarity.utils.helpers.dates import get_week_segment, get_day_segment
import structlog

logger = structlog.get_logger()


class TemporalAnalyzer:
    """
    Analyzes temporal patterns in user activity.
    Identifies timing patterns, routines, and scheduling habits.
    """

    def __init__(self):
        # Configuration
        self.min_pattern_occurrences = 3
        self.routine_consistency_threshold = 0.6
        self.time_block_duration = 30  # minutes

        # Time segment definitions
        self.day_segments = {
            DaySegment.EARLY_MORNING: (5, 8),
            DaySegment.MORNING: (8, 12),
            DaySegment.AFTERNOON: (12, 17),
            DaySegment.EVENING: (17, 21),
            DaySegment.NIGHT: (21, 5),
        }

        # Weight factors for pattern scoring
        self.pattern_weights = {"consistency": 0.4, "duration": 0.3, "frequency": 0.3}

    async def get_user_data(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
        session: AsyncSession,
    ) -> Dict[str, Any]:
        """Fetch temporal activity data for analysis."""
        try:
            # Get user activities
            activities = await UserActivity.get_user_activities(
                session, user_id, start_date, end_date
            )

            # Convert to DataFrame
            activity_df = pd.DataFrame(
                [
                    {
                        "timestamp": activity.timestamp,
                        "duration": activity.duration,
                        "activity_type": activity.activity_type,
                        "day_of_week": activity.timestamp.weekday(),
                        "hour": activity.timestamp.hour,
                        "day_segment": get_day_segment(activity.timestamp.hour),
                    }
                    for activity in activities
                ]
            )

            # Calculate time blocks
            time_blocks = self._calculate_time_blocks(activity_df)

            return {
                "activities": activity_df,
                "time_blocks": time_blocks,
                "metadata": {
                    "total_activities": len(activities),
                    "date_range": (start_date, end_date),
                    "active_days": len(activity_df["timestamp"].dt.date.unique()),
                },
            }

        except Exception as e:
            logger.error("temporal.data_fetch_failed", user_id=user_id, error=str(e))
            raise

    async def analyze(self, temporal_data: Dict[str, Any]) -> List[TemporalPattern]:
        """Analyze temporal data for patterns and routines."""
        patterns = []

        try:
            # Analyze daily patterns
            daily_patterns = self._analyze_daily_patterns(temporal_data["activities"])
            patterns.extend(daily_patterns)

            # Analyze weekly patterns
            weekly_patterns = self._analyze_weekly_patterns(temporal_data["activities"])
            patterns.extend(weekly_patterns)

            # Analyze time block patterns
            block_patterns = self._analyze_time_blocks(temporal_data["time_blocks"])
            patterns.extend(block_patterns)

            # Calculate pattern scores and metadata
            patterns = self._calculate_pattern_scores(patterns)

            return patterns

        except Exception as e:
            logger.error(
                "temporal.analysis_failed",
                error=str(e),
                data_points=len(temporal_data.get("activities", [])),
            )
            raise

    def _calculate_time_blocks(self, activities: pd.DataFrame) -> List[TimeBlock]:
        """Calculate consolidated time blocks from activities."""
        time_blocks = []
        current_block = None

        # Sort activities by timestamp
        sorted_activities = activities.sort_values("timestamp")

        for _, activity in sorted_activities.iterrows():
            if current_block is None:
                current_block = {
                    "start_time": activity["timestamp"],
                    "end_time": activity["timestamp"]
                    + timedelta(minutes=activity["duration"]),
                    "activities": [activity],
                }
            else:
                # Check if activity belongs to current block
                time_gap = (
                    activity["timestamp"] - current_block["end_time"]
                ).total_seconds() / 60

                if time_gap <= self.time_block_duration:
                    current_block["end_time"] = activity["timestamp"] + timedelta(
                        minutes=activity["duration"]
                    )
                    current_block["activities"].append(activity)
                else:
                    # Create time block and start new one
                    time_blocks.append(
                        TimeBlock(
                            start_time=current_block["start_time"],
                            end_time=current_block["end_time"],
                            duration=(
                                current_block["end_time"] - current_block["start_time"]
                            ).total_seconds()
                            / 60,
                            activity_count=len(current_block["activities"]),
                        )
                    )
                    current_block = {
                        "start_time": activity["timestamp"],
                        "end_time": activity["timestamp"]
                        + timedelta(minutes=activity["duration"]),
                        "activities": [activity],
                    }

        # Handle last block
        if current_block:
            time_blocks.append(
                TimeBlock(
                    start_time=current_block["start_time"],
                    end_time=current_block["end_time"],
                    duration=(
                        current_block["end_time"] - current_block["start_time"]
                    ).total_seconds()
                    / 60,
                    activity_count=len(current_block["activities"]),
                )
            )

        return time_blocks

    def _analyze_daily_patterns(
        self, activities: pd.DataFrame
    ) -> List[TemporalPattern]:
        """Analyze patterns within daily activity."""
        patterns = []

        # Analyze activity by day segment
        segment_activity = activities.groupby("day_segment")["duration"].sum()
        total_duration = segment_activity.sum()

        for segment, duration in segment_activity.items():
            percentage = duration / total_duration
            if percentage > 0.25:  # Significant segment threshold
                patterns.append(
                    {
                        "type": "daily_segment",
                        "name": f"high_{segment.lower()}_activity",
                        "description": f"High activity concentration in {segment}",
                        "strength": percentage,
                        "metadata": {
                            "segment": segment,
                            "percentage": percentage,
                            "duration": duration,
                        },
                    }
                )

        # Analyze hourly patterns
        hourly_activity = activities.groupby("hour")["duration"].sum()
        peak_hours = hourly_activity[
            hourly_activity > hourly_activity.mean() + hourly_activity.std()
        ]

        if not peak_hours.empty:
            patterns.append(
                {
                    "type": "peak_hours",
                    "name": "daily_peak_activity",
                    "description": f"Peak activity hours: {', '.join(f'{h:02d}:00' for h in peak_hours.index)}",
                    "strength": len(peak_hours) / 24,
                    "metadata": {
                        "peak_hours": peak_hours.index.tolist(),
                        "average_duration": hourly_activity.mean(),
                        "peak_duration": peak_hours.mean(),
                    },
                }
            )

        return patterns

    def _analyze_weekly_patterns(
        self, activities: pd.DataFrame
    ) -> List[TemporalPattern]:
        """Analyze patterns across different days of the week."""
        patterns = []

        # Analyze activity by day of week
        daily_activity = activities.groupby("day_of_week")["duration"].agg(
            ["sum", "count", "mean"]
        )

        # Find high activity days
        high_activity_days = daily_activity[
            daily_activity["sum"] > daily_activity["sum"].mean()
        ]

        if not high_activity_days.empty:
            patterns.append(
                {
                    "type": "weekly_pattern",
                    "name": "high_activity_days",
                    "description": "Identified high activity days",
                    "strength": len(high_activity_days) / 7,
                    "metadata": {
                        "days": high_activity_days.index.tolist(),
                        "average_duration": daily_activity["mean"].mean(),
                        "activity_counts": daily_activity["count"].to_dict(),
                    },
                }
            )

        # Analyze weekend vs weekday patterns
        weekday_mask = activities["day_of_week"].isin([0, 1, 2, 3, 4])
        weekday_duration = activities[weekday_mask]["duration"].sum() / 5
        weekend_duration = activities[~weekday_mask]["duration"].sum() / 2

        if abs(weekend_duration - weekday_duration) > weekday_duration * 0.2:
            patterns.append(
                {
                    "type": "weekend_pattern",
                    "name": "weekend_variation",
                    "description": f"{'Higher' if weekend_duration > weekday_duration else 'Lower'} weekend activity",
                    "strength": abs(weekend_duration - weekday_duration)
                    / weekday_duration,
                    "metadata": {
                        "weekday_average": weekday_duration,
                        "weekend_average": weekend_duration,
                        "difference_percentage": (weekend_duration - weekday_duration)
                        / weekday_duration,
                    },
                }
            )

        return patterns

    def _analyze_time_blocks(
        self, time_blocks: List[TimeBlock]
    ) -> List[TemporalPattern]:
        """Analyze patterns in time block distribution."""
        patterns = []

        # Convert time blocks to DataFrame
        block_df = pd.DataFrame(
            [
                {
                    "start_hour": block.start_time.hour,
                    "duration": block.duration,
                    "activity_count": block.activity_count,
                }
                for block in time_blocks
            ]
        )

        # Analyze block duration patterns
        avg_duration = block_df["duration"].mean()
        duration_std = block_df["duration"].std()

        if duration_std / avg_duration < self.routine_consistency_threshold:
            patterns.append(
                {
                    "type": "time_block",
                    "name": "consistent_duration",
                    "description": f"Consistent time block duration around {avg_duration:.0f} minutes",
                    "strength": 1 - (duration_std / avg_duration),
                    "metadata": {
                        "average_duration": avg_duration,
                        "consistency": 1 - (duration_std / avg_duration),
                        "block_count": len(time_blocks),
                    },
                }
            )

        # Analyze block start time patterns
        start_time_counts = block_df["start_hour"].value_counts()
        common_starts = start_time_counts[
            start_time_counts >= self.min_pattern_occurrences
        ]

        if not common_starts.empty:
            patterns.append(
                {
                    "type": "time_block",
                    "name": "common_start_times",
                    "description": "Regular block start times detected",
                    "strength": len(common_starts) / 24,
                    "metadata": {
                        "common_hours": common_starts.index.tolist(),
                        "frequencies": common_starts.to_dict(),
                    },
                }
            )

        return patterns

    def _calculate_pattern_scores(
        self, patterns: List[TemporalPattern]
    ) -> List[TemporalPattern]:
        """Calculate final scores for temporal patterns."""
        for pattern in patterns:
            # Calculate base score from pattern strength
            base_score = pattern["strength"]

            # Apply weight factors based on pattern type
            if "consistency" in pattern["metadata"]:
                score = (
                    base_score * self.pattern_weights["consistency"]
                    + pattern["metadata"]["consistency"]
                    * self.pattern_weights["duration"]
                )
            elif "frequency" in pattern["metadata"]:
                score = (
                    base_score * self.pattern_weights["frequency"]
                    + min(1.0, pattern["metadata"]["frequency"] / 10)
                    * self.pattern_weights["frequency"]
                )
            else:
                score = base_score

            pattern["score"] = min(1.0, score)
            pattern["confidence"] = min(1.0, pattern["strength"] * 1.2)
            pattern["timestamp"] = datetime.utcnow()

        return patterns
