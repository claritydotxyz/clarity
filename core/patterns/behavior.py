from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
import numpy as np
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from clarity.models.activity import UserActivity
from clarity.models.application import ApplicationUsage
from clarity.schemas.behavior import (
    BehaviorPattern,
    ProductivityMetrics,
    FocusSession,
    ApplicationCategory,
)
from clarity.utils.monitoring.metrics import (
    behavior_analysis_duration,
    behavior_patterns_detected,
    focus_sessions_tracked,
)
from clarity.core.processors.apps.browser import BrowserDataProcessor
from clarity.core.processors.apps.ide import IDEDataProcessor
from clarity.core.processors.apps.messaging import MessagingDataProcessor
import structlog

logger = structlog.get_logger()


class BehaviorAnalyzer:
    """
    Analyzes user behavior patterns from application usage and activity data.
    Identifies productivity patterns, focus sessions, and work habits.
    """

    def __init__(self):
        self.browser_processor = BrowserDataProcessor()
        self.ide_processor = IDEDataProcessor()
        self.messaging_processor = MessagingDataProcessor()

        # Configuration
        self.focus_session_threshold = 25  # minutes
        self.productivity_thresholds = {
            ApplicationCategory.DEVELOPMENT: 0.9,
            ApplicationCategory.COMMUNICATION: 0.6,
            ApplicationCategory.BROWSING: 0.4,
            ApplicationCategory.SOCIAL_MEDIA: 0.2,
            ApplicationCategory.ENTERTAINMENT: 0.1,
        }

        # Productivity impact weights
        self.impact_weights = {
            "focus_duration": 0.3,
            "context_switches": 0.2,
            "app_category": 0.3,
            "time_of_day": 0.2,
        }

    async def get_user_data(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
        session: AsyncSession,
    ) -> Dict[str, Any]:
        """
        Retrieve user behavior data for analysis.

        Args:
            user_id: User identifier
            start_date: Analysis period start
            end_date: Analysis period end
            session: Database session

        Returns:
            Dictionary containing behavior data
        """
        try:
            # Fetch data concurrently
            activity_data, app_usage = await asyncio.gather(
                self._fetch_activity_data(user_id, start_date, end_date, session),
                self._fetch_application_usage(user_id, start_date, end_date, session),
            )

            # Process application usage by category
            categorized_usage = self._categorize_application_usage(app_usage)

            # Identify focus sessions
            focus_sessions = self._identify_focus_sessions(activity_data)

            # Calculate productivity metrics
            productivity_metrics = self._calculate_productivity_metrics(
                activity_data, categorized_usage, focus_sessions
            )

            return {
                "activity_data": activity_data,
                "application_usage": categorized_usage,
                "focus_sessions": focus_sessions,
                "productivity_metrics": productivity_metrics,
                "metadata": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "total_active_time": sum(activity_data["duration"]),
                    "total_focus_time": sum(
                        session.duration for session in focus_sessions
                    ),
                },
            }

        except Exception as e:
            logger.error(
                "behavior.data_fetch_failed",
                user_id=user_id,
                error=str(e),
                start_date=start_date,
                end_date=end_date,
            )
            raise

    async def analyze(self, behavior_data: Dict[str, Any]) -> List[BehaviorPattern]:
        """
        Analyze behavior data to identify patterns and trends.

        Args:
            behavior_data: Dictionary containing behavior metrics and activity data

        Returns:
            List of identified behavior patterns
        """
        analysis_start = datetime.utcnow()
        patterns = []

        try:
            # Analyze focus patterns
            focus_patterns = self._analyze_focus_patterns(
                behavior_data["focus_sessions"], behavior_data["activity_data"]
            )
            patterns.extend(focus_patterns)

            # Analyze productivity patterns
            productivity_patterns = self._analyze_productivity_patterns(
                behavior_data["productivity_metrics"],
                behavior_data["application_usage"],
            )
            patterns.extend(productivity_patterns)

            # Analyze work habits
            habit_patterns = self._analyze_work_habits(
                behavior_data["activity_data"], behavior_data["application_usage"]
            )
            patterns.extend(habit_patterns)

            # Calculate pattern strengths and confidence
            patterns = self._calculate_pattern_metrics(patterns)

            # Update monitoring metrics
            analysis_duration = (datetime.utcnow() - analysis_start).total_seconds()
            behavior_analysis_duration.observe(analysis_duration)
            behavior_patterns_detected.inc(len(patterns))

            return patterns

        except Exception as e:
            logger.error(
                "behavior.analysis_failed",
                error=str(e),
                data_points=len(behavior_data.get("activity_data", [])),
            )
            raise

    async def _fetch_activity_data(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
        session: AsyncSession,
    ) -> pd.DataFrame:
        """Fetch and process user activity data."""
        activities = await UserActivity.get_user_activities(
            session, user_id, start_date, end_date
        )

        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(
            [
                {
                    "timestamp": activity.timestamp,
                    "activity_type": activity.activity_type,
                    "duration": activity.duration,
                    "metadata": activity.metadata,
                }
                for activity in activities
            ]
        )

        return df

    async def _fetch_application_usage(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
        session: AsyncSession,
    ) -> pd.DataFrame:
        """Fetch and process application usage data."""
        app_usage = await ApplicationUsage.get_user_app_usage(
            session, user_id, start_date, end_date
        )

        df = pd.DataFrame(
            [
                {
                    "timestamp": usage.timestamp,
                    "application": usage.application_name,
                    "duration": usage.duration,
                    "category": usage.category,
                    "is_active": usage.is_active,
                }
                for usage in app_usage
            ]
        )

        return df

    def _categorize_application_usage(
        self, app_usage: pd.DataFrame
    ) -> Dict[ApplicationCategory, pd.DataFrame]:
        """Categorize application usage by type."""
        categorized = {}

        for category in ApplicationCategory:
            category_usage = app_usage[app_usage["category"] == category]
            if not category_usage.empty:
                categorized[category] = category_usage

        return categorized

    def _identify_focus_sessions(
        self, activity_data: pd.DataFrame
    ) -> List[FocusSession]:
        """Identify continuous focus sessions from activity data."""
        focus_sessions = []
        current_session = None

        # Sort activities by timestamp
        sorted_activities = activity_data.sort_values("timestamp")

        for _, activity in sorted_activities.iterrows():
            if current_session is None:
                current_session = {
                    "start_time": activity["timestamp"],
                    "duration": activity["duration"],
                    "activities": [activity],
                }
            else:
                # Check if activity is part of current session
                time_gap = (
                    activity["timestamp"]
                    - current_session["activities"][-1]["timestamp"]
                ).total_seconds() / 60

                if time_gap <= 5:  # 5-minute gap threshold
                    current_session["duration"] += activity["duration"]
                    current_session["activities"].append(activity)
                else:
                    # End current session if it meets minimum duration
                    if current_session["duration"] >= self.focus_session_threshold:
                        focus_sessions.append(
                            FocusSession(
                                start_time=current_session["start_time"],
                                duration=current_session["duration"],
                                activity_count=len(current_session["activities"]),
                            )
                        )
                    # Start new session
                    current_session = {
                        "start_time": activity["timestamp"],
                        "duration": activity["duration"],
                        "activities": [activity],
                    }

        # Handle last session
        if (
            current_session
            and current_session["duration"] >= self.focus_session_threshold
        ):
            focus_sessions.append(
                FocusSession(
                    start_time=current_session["start_time"],
                    duration=current_session["duration"],
                    activity_count=len(current_session["activities"]),
                )
            )

        focus_sessions_tracked.inc(len(focus_sessions))
        return focus_sessions

    def _calculate_productivity_metrics(
        self,
        activity_data: pd.DataFrame,
        categorized_usage: Dict[ApplicationCategory, pd.DataFrame],
        focus_sessions: List[FocusSession],
    ) -> ProductivityMetrics:
        """Calculate comprehensive productivity metrics."""
        total_time = activity_data["duration"].sum()

        # Calculate time spent in each category
        category_times = {
            category: usage["duration"].sum()
            for category, usage in categorized_usage.items()
        }

        # Calculate productivity score
        productivity_score = (
            sum(
                category_times.get(cat, 0) * self.productivity_thresholds.get(cat, 0)
                for cat in ApplicationCategory
            )
            / total_time
            if total_time > 0
            else 0
        )

        # Calculate focus metrics
        total_focus_time = sum(session.duration for session in focus_sessions)
        avg_session_duration = (
            total_focus_time / len(focus_sessions) if focus_sessions else 0
        )

        # Calculate context switching metric
        context_switches = self._calculate_context_switches(activity_data)

        return ProductivityMetrics(
            productivity_score=productivity_score,
            focus_time_percentage=total_focus_time / total_time
            if total_time > 0
            else 0,
            average_focus_duration=avg_session_duration,
            context_switches_per_hour=context_switches,
            category_breakdown=category_times,
        )

    def _calculate_context_switches(self, activity_data: pd.DataFrame) -> float:
        """Calculate context switches per hour from activity data."""
        # Group activities by hour
        activity_data["hour"] = activity_data["timestamp"].dt.hour
        hourly_switches = activity_data.groupby("hour")["activity_type"].nunique()

        return hourly_switches.mean()

    def _analyze_focus_patterns(
        self, focus_sessions: List[FocusSession], activity_data: pd.DataFrame
    ) -> List[BehaviorPattern]:
        """Analyze focus session patterns."""
        patterns = []

        if not focus_sessions:
            return patterns

        # Analyze focus session distribution
        session_df = pd.DataFrame(
            [
                {
                    "start_hour": session.start_time.hour,
                    "duration": session.duration,
                    "activity_count": session.activity_count,
                }
                for session in focus_sessions
            ]
        )

        # Find peak focus hours
        hourly_focus = session_df.groupby("start_hour")["duration"].sum()
        peak_hour = hourly_focus.idxmax()
        peak_duration = hourly_focus.max()

        patterns.append(
            BehaviorPattern(
                type="focus_time",
                name="peak_focus_hours",
                description=f"Peak focus hours occur at {peak_hour:02d}:00",
                strength=peak_duration / hourly_focus.mean(),
                metadata={
                    "peak_hour": peak_hour,
                    "peak_duration": peak_duration,
                    "session_count": len(focus_sessions),
                },
            )
        )

        return patterns

    def _analyze_productivity_patterns(
        self,
        productivity_metrics: ProductivityMetrics,
        categorized_usage: Dict[ApplicationCategory, pd.DataFrame],
    ) -> List[BehaviorPattern]:
        """Analyze productivity patterns."""
        patterns = []

        # Analyze category usage patterns
        for category, usage_df in categorized_usage.items():
            if not usage_df.empty:
                avg_duration = usage_df["duration"].mean()
                usage_frequency = len(usage_df) / len(
                    usage_df["timestamp"].dt.date.unique()
                )

                if usage_frequency > 5:  # Significant usage pattern threshold
                    patterns.append(
                        BehaviorPattern(
                            type="application_usage",
                            name=f"{category.lower()}_usage",
                            description=f"High {category} application usage frequency",
                            strength=usage_frequency / 10,  # Normalize to 0-1
                            metadata={
                                "category": category,
                                "frequency": usage_frequency,
                                "avg_duration": avg_duration,
                            },
                        )
                    )

        return patterns

    def _analyze_work_habits(
        self,
        activity_data: pd.DataFrame,
        categorized_usage: Dict[ApplicationCategory, pd.DataFrame],
    ) -> List[BehaviorPattern]:
        """Analyze work habits and routines."""
        patterns = []

        # Analyze daily routines
        activity_data["hour"] = activity_data["timestamp"].dt.hour
        hourly_activity = activity_data.groupby("hour")["duration"].sum()

        # Find consistent active hours
        active_hours = hourly_activity[hourly_activity > hourly_activity.mean()]
        if not active_hours.empty:
            patterns.append(
                BehaviorPattern(
                    type="work_routine",
                    name="active_hours",
                    description=f"Core active hours between {active_hours.index.min():02d}:00-{active_hours.index.max():02d}:00",
                    strength=len(active_hours) / 24,
                    metadata={
                        "start_hour": active_hours.index.min(),
                        "end_hour": active_hours.index.max(),
                        "peak_hour": hourly_activity.idxmax(),
                    },
                )
            )

        return patterns

    def _calculate_pattern_metrics(
        self, patterns: List[BehaviorPattern]
    ) -> List[BehaviorPattern]:
        """Calculate strength and confidence metrics for patterns."""
        for pattern in patterns:
            # Normalize pattern strength
            pattern.strength = min(1.0, pattern.strength)

            # Calculate confidence based on data points and pattern strength
            if "session_count" in pattern.metadata:
                confidence_factor = min(1.0, pattern.metadata["session_count"] / 20)
            elif "frequency" in pattern.metadata:
                confidence_factor = min(1.0, pattern.metadata["frequency"] / 10)
            else:
                confidence_factor = 0.7  # Default confidence

            pattern.confidence = confidence_factor * pattern.strength
            # Calculate support (percentage of time pattern is active)
            if "duration" in pattern.metadata:
                pattern.support = pattern.metadata["duration"] / (
                    24 * 60
                )  # minutes in day
            elif "frequency" in pattern.metadata:
                pattern.support = pattern.metadata["frequency"] / 24  # hourly frequency
            else:
                pattern.support = 0.5  # Default support

        return patterns

    def _analyze_multitasking_patterns(
        self,
        activity_data: pd.DataFrame,
        app_usage: Dict[ApplicationCategory, pd.DataFrame],
    ) -> List[BehaviorPattern]:
        """Analyze patterns of concurrent application usage and task switching."""
        patterns = []

        # Create timeline of application switches
        timeline = pd.concat(
            [df.assign(category=cat) for cat, df in app_usage.items()]
        ).sort_values("timestamp")

        # Calculate overlapping application usage
        timeline["end_time"] = timeline["timestamp"] + pd.Timedelta(
            minutes=timeline["duration"]
        )

        overlaps = []
        for i in range(len(timeline) - 1):
            current = timeline.iloc[i]
            next_app = timeline.iloc[i + 1]

            if current["end_time"] > next_app["timestamp"]:
                overlaps.append(
                    {
                        "timestamp": next_app["timestamp"],
                        "categories": [current["category"], next_app["category"]],
                        "duration": (
                            current["end_time"] - next_app["timestamp"]
                        ).total_seconds()
                        / 60,
                    }
                )

        if overlaps:
            overlap_df = pd.DataFrame(overlaps)
            frequent_combinations = (
                overlap_df.groupby("categories")["duration"]
                .agg(["count", "sum", "mean"])
                .sort_values("count", ascending=False)
            )

            for combo, stats in frequent_combinations.iterrows():
                if stats["count"] >= 5:  # Minimum occurrences threshold
                    patterns.append(
                        BehaviorPattern(
                            type="multitasking",
                            name="concurrent_apps",
                            description=f"Frequent concurrent usage of {combo[0]} and {combo[1]}",
                            strength=min(1.0, stats["count"] / 20),
                            metadata={
                                "categories": combo,
                                "occurrence_count": stats["count"],
                                "average_duration": stats["mean"],
                                "total_duration": stats["sum"],
                            },
                        )
                    )

        return patterns

    def _analyze_break_patterns(
        self, activity_data: pd.DataFrame, focus_sessions: List[FocusSession]
    ) -> List[BehaviorPattern]:
        """Analyze patterns in break timing and duration between focus sessions."""
        patterns = []

        if len(focus_sessions) < 2:
            return patterns

        # Calculate break durations between sessions
        break_durations = []
        for i in range(len(focus_sessions) - 1):
            current_session = focus_sessions[i]
            next_session = focus_sessions[i + 1]

            break_start = current_session.start_time + timedelta(
                minutes=current_session.duration
            )
            break_duration = (
                next_session.start_time - break_start
            ).total_seconds() / 60

            if break_duration > 0:
                break_durations.append(
                    {
                        "start_time": break_start,
                        "duration": break_duration,
                        "prev_session_duration": current_session.duration,
                    }
                )

        if break_durations:
            break_df = pd.DataFrame(break_durations)

            # Analyze break duration patterns
            avg_break = break_df["duration"].mean()
            break_consistency = 1 - (
                break_df["duration"].std() / avg_break if avg_break > 0 else 0
            )

            patterns.append(
                BehaviorPattern(
                    type="break_pattern",
                    name="break_duration",
                    description=f"Average break duration of {avg_break:.1f} minutes",
                    strength=break_consistency,
                    metadata={
                        "average_duration": avg_break,
                        "break_count": len(break_durations),
                        "consistency": break_consistency,
                    },
                )
            )

            # Analyze break timing relative to focus duration
            correlation = break_df["duration"].corr(break_df["prev_session_duration"])
            if abs(correlation) > 0.3:
                patterns.append(
                    BehaviorPattern(
                        type="break_pattern",
                        name="break_correlation",
                        description="Break duration correlates with previous focus duration",
                        strength=abs(correlation),
                        metadata={
                            "correlation": correlation,
                            "sample_size": len(break_durations),
                        },
                    )
                )

        return patterns

    def _analyze_distraction_patterns(
        self,
        activity_data: pd.DataFrame,
        app_usage: Dict[ApplicationCategory, pd.DataFrame],
    ) -> List[BehaviorPattern]:
        """Analyze patterns in distraction and interruption timing."""
        patterns = []

        # Identify potential distractions
        distraction_categories = [
            ApplicationCategory.SOCIAL_MEDIA,
            ApplicationCategory.ENTERTAINMENT,
        ]

        distractions = pd.concat(
            [app_usage[cat] for cat in distraction_categories if cat in app_usage]
        )

        if not distractions.empty:
            # Analyze distraction frequency by hour
            distractions["hour"] = distractions["timestamp"].dt.hour
            hourly_distractions = distractions.groupby("hour").size()

            # Find peak distraction hours
            peak_hours = hourly_distractions[
                hourly_distractions
                > hourly_distractions.mean() + hourly_distractions.std()
            ]

            if not peak_hours.empty:
                patterns.append(
                    BehaviorPattern(
                        type="distraction",
                        name="peak_distraction_hours",
                        description=f"Peak distraction hours: {', '.join(f'{h:02d}:00' for h in peak_hours.index)}",
                        strength=len(peak_hours) / 24,
                        metadata={
                            "peak_hours": peak_hours.index.tolist(),
                            "average_distractions": hourly_distractions.mean(),
                            "total_distractions": len(distractions),
                        },
                    )
                )

            # Analyze distraction duration
            avg_duration = distractions["duration"].mean()
            duration_variance = distractions["duration"].std() / avg_duration

            patterns.append(
                BehaviorPattern(
                    type="distraction",
                    name="distraction_duration",
                    description=f"Average distraction duration: {avg_duration:.1f} minutes",
                    strength=1 - min(1.0, duration_variance),
                    metadata={
                        "average_duration": avg_duration,
                        "duration_consistency": 1 - duration_variance,
                        "sample_size": len(distractions),
                    },
                )
            )

        return patterns

    def _analyze_productivity_impact(
        self,
        activity_data: pd.DataFrame,
        productivity_metrics: ProductivityMetrics,
        focus_sessions: List[FocusSession],
    ) -> Dict[str, float]:
        """Analyze factors impacting productivity."""
        impacts = {}

        # Analyze focus duration impact
        avg_focus = productivity_metrics.average_focus_duration
        optimal_focus = 50  # minutes
        focus_impact = min(1.0, avg_focus / optimal_focus)
        impacts["focus_duration"] = focus_impact * self.impact_weights["focus_duration"]

        # Analyze context switching impact
        optimal_switches = 10  # per hour
        switch_ratio = min(
            1.0, optimal_switches / productivity_metrics.context_switches_per_hour
        )
        impacts["context_switches"] = (
            switch_ratio * self.impact_weights["context_switches"]
        )

        # Analyze application category impact
        category_impact = sum(
            self.productivity_thresholds.get(cat, 0)
            * (duration / sum(productivity_metrics.category_breakdown.values()))
            for cat, duration in productivity_metrics.category_breakdown.items()
        )
        impacts["app_category"] = category_impact * self.impact_weights["app_category"]

        # Analyze time of day impact
        activity_data["hour"] = activity_data["timestamp"].dt.hour
        hourly_productivity = activity_data.groupby("hour")["duration"].sum()
        peak_hours_ratio = (
            len(hourly_productivity[hourly_productivity > hourly_productivity.mean()])
            / 24
        )
        impacts["time_of_day"] = peak_hours_ratio * self.impact_weights["time_of_day"]

        return impacts
