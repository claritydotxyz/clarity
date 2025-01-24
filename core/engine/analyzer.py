from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import asyncio
import numpy as np
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from clarity.core.patterns.behavior import BehaviorAnalyzer
from clarity.core.patterns.financial import FinancialAnalyzer
from clarity.core.patterns.temporal import TemporalAnalyzer
from clarity.core.engine.processor import DataProcessor
from clarity.models.insight import Insight
from clarity.models.analysis import Analysis
from clarity.schemas.analysis import (
    AnalysisResult,
    InsightType,
    PatternScore,
    RecommendationType,
)
from clarity.utils.monitoring.metrics import (
    analysis_duration_histogram,
    insights_generated_counter,
    analysis_error_counter,
)
import structlog

logger = structlog.get_logger()


class InsightAnalyzer:
    """
    Core analyzer engine that processes collected data and generates insights.
    Combines behavioral, financial, and temporal patterns to create comprehensive insights.
    """

    def __init__(self):
        self.behavior_analyzer = BehaviorAnalyzer()
        self.financial_analyzer = FinancialAnalyzer()
        self.temporal_analyzer = TemporalAnalyzer()
        self.data_processor = DataProcessor()

        # Configure analysis thresholds
        self.correlation_threshold = 0.7
        self.pattern_significance_threshold = 0.6
        self.min_data_points = 10

        # Pattern weights for scoring
        self.pattern_weights = {
            "productivity": 0.35,
            "financial": 0.35,
            "temporal": 0.30,
        }

    async def analyze_user_data(
        self,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        session: AsyncSession = None,
        include_raw_data: bool = False,
    ) -> AnalysisResult:
        """
        Analyze user data across all dimensions to generate insights.

        Args:
            user_id: ID of the user to analyze
            start_date: Start date for analysis window
            end_date: End date for analysis window
            session: Database session
            include_raw_data: Whether to include raw data in result

        Returns:
            AnalysisResult containing all insights and recommendations

        Raises:
            ValueError: If date range is invalid
            AnalysisError: If analysis fails
        """
        analysis_start_time = datetime.utcnow()

        try:
            # Validate and set date range
            end_date = end_date or datetime.utcnow()
            start_date = start_date or (end_date - timedelta(days=30))

            if start_date >= end_date:
                raise ValueError("Start date must be before end date")

            # Collect data from all analyzers concurrently
            data_tasks = [
                self.behavior_analyzer.get_user_data(
                    user_id, start_date, end_date, session
                ),
                self.financial_analyzer.get_user_data(
                    user_id, start_date, end_date, session
                ),
                self.temporal_analyzer.get_user_data(
                    user_id, start_date, end_date, session
                ),
            ]

            behavior_data, financial_data, temporal_data = await asyncio.gather(
                *data_tasks
            )

            # Validate data sufficiency
            if not self._check_data_sufficiency(
                behavior_data, financial_data, temporal_data
            ):
                logger.warning(
                    "analyzer.insufficient_data",
                    user_id=user_id,
                    start_date=start_date,
                    end_date=end_date,
                )

            # Process and analyze patterns concurrently
            analysis_tasks = [
                self.behavior_analyzer.analyze(behavior_data),
                self.financial_analyzer.analyze(financial_data),
                self.temporal_analyzer.analyze(temporal_data),
            ]

            (
                behavior_patterns,
                financial_patterns,
                temporal_patterns,
            ) = await asyncio.gather(*analysis_tasks)

            # Combine patterns and generate insights
            combined_patterns = self._combine_patterns(
                behavior_patterns, financial_patterns, temporal_patterns
            )

            insights = self._generate_insights(combined_patterns)
            recommendations = self._generate_recommendations(insights)

            # Calculate pattern scores
            pattern_scores = self._calculate_pattern_scores(combined_patterns)

            # Store analysis results
            analysis = Analysis(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                insights=insights,
                recommendations=recommendations,
                pattern_scores=pattern_scores,
            )
            session.add(analysis)
            await session.commit()

            # Update metrics
            analysis_duration = (
                datetime.utcnow() - analysis_start_time
            ).total_seconds()
            analysis_duration_histogram.observe(analysis_duration)
            insights_generated_counter.inc(len(insights))

            return AnalysisResult(
                insights=insights,
                recommendations=recommendations,
                pattern_scores=pattern_scores,
                metadata={
                    "analysis_id": analysis.id,
                    "analysis_duration": analysis_duration,
                    "data_start_date": start_date,
                    "data_end_date": end_date,
                    "total_patterns_analyzed": len(combined_patterns),
                    "total_insights_generated": len(insights),
                },
                raw_data=self._prepare_raw_data(
                    behavior_data, financial_data, temporal_data
                )
                if include_raw_data
                else None,
            )

        except Exception as e:
            analysis_error_counter.inc()
            logger.error(
                "analyzer.analysis_failed",
                user_id=user_id,
                error=str(e),
                start_date=start_date,
                end_date=end_date,
            )
            raise

    def _check_data_sufficiency(self, *data_sets: Tuple[Any]) -> bool:
        """Check if there is sufficient data for meaningful analysis."""
        return all(
            len(data) >= self.min_data_points for data in data_sets if data is not None
        )

    def _combine_patterns(
        self, behavior_patterns: Dict, financial_patterns: Dict, temporal_patterns: Dict
    ) -> List[Dict]:
        """
        Combine and correlate patterns from different analyzers.
        Implements advanced pattern correlation using statistical methods.
        """
        combined_patterns = []

        # Convert patterns to dataframes for analysis
        pattern_dfs = {
            "behavior": pd.DataFrame(behavior_patterns),
            "financial": pd.DataFrame(financial_patterns),
            "temporal": pd.DataFrame(temporal_patterns),
        }

        # Calculate correlation matrix
        correlation_matrix = pd.concat(pattern_dfs.values(), axis=1).corr()

        # Find significant correlations
        significant_correlations = self._find_significant_correlations(
            correlation_matrix
        )

        # Generate combined patterns
        for pattern_type, correlations in significant_correlations.items():
            for correlated_type, correlation_strength in correlations.items():
                combined_patterns.append(
                    {
                        "type": f"{pattern_type}_{correlated_type}",
                        "strength": correlation_strength,
                        "patterns": {
                            pattern_type: pattern_dfs[pattern_type],
                            correlated_type: pattern_dfs[correlated_type],
                        },
                        "metadata": {
                            "correlation_coefficient": correlation_strength,
                            "sample_size": len(pattern_dfs[pattern_type]),
                            "timestamp": datetime.utcnow(),
                        },
                    }
                )

        # Add individual strong patterns
        for pattern_type, df in pattern_dfs.items():
            strong_patterns = self._find_strong_patterns(df)
            for pattern in strong_patterns:
                combined_patterns.append(
                    {
                        "type": pattern_type,
                        "strength": pattern["strength"],
                        "pattern": pattern["data"],
                        "metadata": {
                            "confidence": pattern["confidence"],
                            "support": pattern["support"],
                            "timestamp": datetime.utcnow(),
                        },
                    }
                )

        return combined_patterns

    def _find_significant_correlations(
        self, correlation_matrix: pd.DataFrame
    ) -> Dict[str, Dict[str, float]]:
        """Find statistically significant correlations between patterns."""
        significant_correlations = {}

        for col in correlation_matrix.columns:
            correlations = {}
            for idx in correlation_matrix.index:
                if col != idx:
                    corr_value = abs(correlation_matrix.loc[idx, col])
                    if corr_value >= self.correlation_threshold:
                        correlations[idx] = corr_value

            if correlations:
                significant_correlations[col] = correlations

        return significant_correlations

    def _find_strong_patterns(self, pattern_df: pd.DataFrame) -> List[Dict]:
        """Identify strong individual patterns in the data."""
        strong_patterns = []

        # Calculate pattern strength using statistical methods
        for column in pattern_df.columns:
            data = pattern_df[column].dropna()
            if len(data) >= self.min_data_points:
                # Calculate basic statistics
                mean = data.mean()
                std = data.std()

                # Calculate pattern strength metrics
                strength = abs(mean) / (std if std > 0 else 1)

                if strength >= self.pattern_significance_threshold:
                    # Calculate confidence and support
                    confidence = min(1.0, strength / 2)
                    support = len(data) / len(pattern_df)

                    strong_patterns.append(
                        {
                            "name": column,
                            "strength": float(strength),
                            "data": data.to_dict(),
                            "confidence": float(confidence),
                            "support": float(support),
                        }
                    )

        return strong_patterns

    def _generate_insights(self, combined_patterns: List[Dict]) -> List[Dict]:
        """Generate actionable insights from combined patterns."""
        insights = []

        for pattern in combined_patterns:
            try:
                # Generate insight based on pattern type
                if pattern["type"].startswith("behavior_financial"):
                    insights.extend(self._generate_behavior_financial_insights(pattern))
                elif pattern["type"].startswith("temporal_financial"):
                    insights.extend(self._generate_temporal_financial_insights(pattern))
                elif pattern["type"].startswith("behavior_temporal"):
                    insights.extend(self._generate_behavior_temporal_insights(pattern))
                else:
                    # Generate single-dimension insights
                    insights.extend(self._generate_single_dimension_insights(pattern))

            except Exception as e:
                logger.error(
                    "analyzer.insight_generation_failed",
                    pattern_type=pattern["type"],
                    error=str(e),
                )

        # Deduplicate and rank insights
        return self._rank_and_deduplicate_insights(insights)

    def _generate_recommendations(self, insights: List[Dict]) -> List[Dict]:
        """Generate personalized recommendations based on insights."""
        recommendations = []

        # Group insights by category
        categorized_insights = self._categorize_insights(insights)

        for category, category_insights in categorized_insights.items():
            try:
                if category == "productivity":
                    recommendations.extend(
                        self._generate_productivity_recommendations(category_insights)
                    )
                elif category == "financial":
                    recommendations.extend(
                        self._generate_financial_recommendations(category_insights)
                    )
                elif category == "time_management":
                    recommendations.extend(
                        self._generate_time_recommendations(category_insights)
                    )

                # Add recommendation metadata
                for rec in recommendations:
                    rec.update(
                        {
                            "timestamp": datetime.utcnow(),
                            "source_insights": [i["id"] for i in category_insights],
                            "confidence_score": self._calculate_recommendation_confidence(
                                rec
                            ),
                        }
                    )

            except Exception as e:
                logger.error(
                    "analyzer.recommendation_generation_failed",
                    category=category,
                    error=str(e),
                )

        # Prioritize and deduplicate recommendations
        return self._prioritize_recommendations(recommendations)

    def _calculate_pattern_scores(self, patterns: List[Dict]) -> Dict[str, float]:
        """Calculate normalized scores for different pattern types."""
        scores = {"productivity": 0.0, "financial": 0.0, "temporal": 0.0}

        for pattern in patterns:
            pattern_type = pattern["type"].split("_")[0]
            if pattern_type in scores:
                scores[pattern_type] += (
                    pattern["strength"] * self.pattern_weights[pattern_type]
                )

        # Normalize scores to 0-1 range
        max_score = max(scores.values()) if scores.values() else 1
        return {k: v / max_score if max_score > 0 else 0 for k, v in scores.items()}

    def _prepare_raw_data(
        self, behavior_data: Dict, financial_data: Dict, temporal_data: Dict
    ) -> Dict:
        """Prepare raw data for response if requested."""
        return {
            "behavior": self.data_processor.anonymize_data(behavior_data),
            "financial": self.data_processor.anonymize_data(financial_data),
            "temporal": self.data_processor.anonymize_data(temporal_data),
        }
