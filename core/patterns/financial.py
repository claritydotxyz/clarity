from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from clarity.models.transaction import Transaction
from clarity.models.budget import Budget
from clarity.schemas.financial import (
    FinancialPattern,
    SpendingCategory,
    TransactionType,
    BudgetStatus
)
from clarity.core.processors.integrations.financial.plaid import PlaidProcessor
from clarity.utils.monitoring.metrics import financial_analysis_counter
import structlog

logger = structlog.get_logger()

class FinancialAnalyzer:
    """
    Analyzes financial patterns from transaction data and budgets.
    Identifies spending patterns, budget adherence, and financial habits.
    """

    def __init__(self):
        self.plaid_processor = PlaidProcessor()
        
        # Analysis thresholds
        self.spending_variance_threshold = 0.3
        self.budget_variance_threshold = 0.15
        self.pattern_detection_min_transactions = 5
        
        # Category weights for overall financial health
        self.category_weights = {
            SpendingCategory.ESSENTIAL: 0.4,
            SpendingCategory.INVESTMENT: 0.3,
            SpendingCategory.DISCRETIONARY: 0.2,
            SpendingCategory.DEBT: 0.1
        }

    async def get_user_data(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Fetch user's financial data for analysis."""
        try:
            # Fetch transactions and budgets
            transactions = await Transaction.get_user_transactions(
                session, user_id, start_date, end_date
            )
            budgets = await Budget.get_user_budgets(
                session, user_id, start_date, end_date
            )
            
            # Process transactions
            transaction_df = pd.DataFrame([
                {
                    "date": tx.date,
                    "amount": tx.amount,
                    "category": tx.category,
                    "type": tx.transaction_type,
                    "merchant": tx.merchant
                }
                for tx in transactions
            ])
            
            # Process budgets
            budget_data = {
                budget.category: {
                    "limit": budget.amount,
                    "actual": self._calculate_category_spending(
                        transaction_df, budget.category
                    )
                }
                for budget in budgets
            }
            
            return {
                "transactions": transaction_df,
                "budgets": budget_data,
                "metadata": {
                    "total_transactions": len(transactions),
                    "budget_categories": len(budgets),
                    "date_range": (start_date, end_date)
                }
            }
            
        except Exception as e:
            logger.error(
                "financial.data_fetch_failed",
                user_id=user_id,
                error=str(e)
            )
            raise

    async def analyze(self, financial_data: Dict[str, Any]) -> List[FinancialPattern]:
        """Analyze financial data for patterns and insights."""
        patterns = []
        financial_analysis_counter.inc()
        
        try:
            # Analyze spending patterns
            spending_patterns = self._analyze_spending_patterns(
                financial_data["transactions"]
            )
            patterns.extend(spending_patterns)
            
            # Analyze budget adherence
            budget_patterns = self._analyze_budget_patterns(
                financial_data["transactions"],
                financial_data["budgets"]
            )
            patterns.extend(budget_patterns)
            
            # Analyze recurring transactions
            recurring_patterns = self._analyze_recurring_transactions(
                financial_data["transactions"]
            )
            patterns.extend(recurring_patterns)
            
            # Add pattern metadata and confidence scores
            patterns = self._enrich_patterns(patterns)
            
            return patterns
            
        except Exception as e:
            logger.error(
                "financial.analysis_failed",
                error=str(e),
                data_points=len(financial_data.get("transactions", []))
            )
            raise

    def _calculate_category_spending(
        self,
        transactions: pd.DataFrame,
        category: SpendingCategory
    ) -> float:
        """Calculate total spending for a category."""
        category_transactions = transactions[
            (transactions["category"] == category) &
            (transactions["type"] == TransactionType.EXPENSE)
        ]
        return category_transactions["amount"].sum()

    def _analyze_spending_patterns(
        self,
        transactions: pd.DataFrame
    ) -> List[FinancialPattern]:
        """Analyze spending patterns and trends."""
        patterns = []
        
        # Analyze daily spending patterns
        daily_spending = transactions.groupby(
            transactions["date"].dt.date
        )["amount"].sum()
        
        spending_stats = {
            "mean": daily_spending.mean(),
            "std": daily_spending.std(),
            "max": daily_spending.max(),
            "min": daily_spending.min()
        }
        
        # Check for high spending variance
        if spending_stats["std"] / spending_stats["mean"] > self.spending_variance_threshold:
            patterns.append({
                "type": "spending_volatility",
                "name": "high_spending_variance",
                "description": "Daily spending shows high variability",
                "strength": min(1.0, spending_stats["std"] / spending_stats["mean"]),
                "metadata": spending_stats
            })
        
        # Analyze category distribution
        category_spending = transactions.groupby("category")["amount"].sum()
        total_spending = category_spending.sum()
        
        for category, amount in category_spending.items():
            percentage = amount / total_spending
            if percentage > 0.3:  # Significant category threshold
                patterns.append({
                    "type": "category_concentration",
                    "name": f"high_{category.lower()}_spending",
                    "description": f"High concentration of spending in {category}",
                    "strength": percentage,
                    "metadata": {
                        "category": category,
                        "percentage": percentage,
                        "amount": amount
                    }
                })
        
        return patterns

    def _analyze_budget_patterns(
        self,
        transactions: pd.DataFrame,
        budgets: Dict[SpendingCategory, Dict]
    ) -> List[FinancialPattern]:
        """Analyze budget adherence patterns."""
        patterns = []
        
        for category, budget_info in budgets.items():
            limit = budget_info["limit"]
            actual = budget_info["actual"]
            variance = (actual - limit) / limit if limit > 0 else 0
            
            if abs(variance) > self.budget_variance_threshold:
                pattern_type = "over_budget" if variance > 0 else "under_budget"
                patterns.append({
                    "type": pattern_type,
                    "name": f"{category.lower()}_budget_variance",
                    "description": f"{'Exceeded' if variance > 0 else 'Under'} budget in {category}",
                    "strength": abs(variance),
                    "metadata": {
                        "category": category,
                        "variance": variance,
                        "limit": limit,
                        "actual": actual
                    }
                })
        
        return patterns

    def _analyze_recurring_transactions(
        self,
        transactions: pd.DataFrame
    ) -> List[FinancialPattern]:
        """Identify recurring transaction patterns."""
        patterns = []
        
        # Group by merchant
        merchant_transactions = transactions.groupby("merchant")
        
        for merchant, merchant_df in merchant_transactions:
            if len(merchant_df) >= self.pattern_detection_min_transactions:
                # Calculate transaction intervals
                dates = sorted(merchant_df["date"])
                intervals = [(dates[i+1] - dates[i]).days 
                           for i in range(len(dates)-1)]
                
                if intervals:
                    avg_interval = sum(intervals) / len(intervals)
                    interval_std = np.std(intervals)
                    
                    # Check for recurring pattern
                    if interval_std / avg_interval < 0.2:  # Regular interval threshold
                        patterns.append({
                            "type": "recurring_transaction",
                            "name": f"recurring_{merchant.lower()}",
                            "description": f"Recurring transaction pattern for {merchant}",
                            "strength": 1 - (interval_std / avg_interval),
                            "metadata": {
                                "merchant": merchant,
                                "average_interval": avg_interval,
                                "average_amount": merchant_df["amount"].mean(),
                                "transaction_count": len(merchant_df)
                            }
                        })
        
        return patterns

    def _enrich_patterns(
        self,
        patterns: List[FinancialPattern]
    ) -> List[FinancialPattern]:
        """Add metadata and confidence scores to patterns."""
        for pattern in patterns:
            # Calculate confidence based on data points and pattern type
            if pattern["type"] == "recurring_transaction":
                confidence = min(1.0, pattern["metadata"]["transaction_count"] / 10)
            elif pattern["type"] in ["over_budget", "under_budget"]:
                confidence = min(1.0, abs(pattern["metadata"]["variance"]) * 2)
            else:
                confidence = min(1.0, pattern["strength"] * 1.2)
            
            pattern["confidence"] = confidence
            pattern["timestamp"] = datetime.utcnow()
        
        return patterns
