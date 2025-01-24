from typing import Dict, List, Optional
from datetime import datetime
import stripe
from clarity.schemas.financial import StripeTransaction, Customer
import structlog

logger = structlog.get_logger()

class StripeProcessor:
    def __init__(self, api_key: str):
        stripe.api_key = api_key

    async def get_transactions(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[StripeTransaction]:
        try:
            charges = stripe.Charge.list(
                created={
                    'gte': int(start_date.timestamp()),
                    'lte': int(end_date.timestamp())
                }
            )
            
            return [
                StripeTransaction(
                    id=charge.id,
                    amount=charge.amount / 100.0,
                    currency=charge.currency,
                    status=charge.status,
                    customer_id=charge.customer,
                    created_at=datetime.fromtimestamp(charge.created)
                )
                for charge in charges.auto_paging_iter()
            ]
        except Exception as e:
           logger.error("stripe.transaction_fetch_failed", error=str(e))
            return []

    async def get_customers(self) -> List[Customer]:
        try:
            customers = stripe.Customer.list()
            return [
                Customer(
                    id=customer.id,
                    email=customer.email,
                    name=customer.name,
                    created_at=datetime.fromtimestamp(customer.created),
                    metadata=customer.metadata
                )
                for customer in customers.auto_paging_iter()
            ]
        except Exception as e:
            logger.error("stripe.customer_fetch_failed", error=str(e))
            return []

    async def get_customer_transactions(
        self,
        customer_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[StripeTransaction]:
        try:
            charges = stripe.Charge.list(
                customer=customer_id,
                created={
                    'gte': int(start_date.timestamp()),
                    'lte': int(end_date.timestamp())
                }
            )
            
            return [
                StripeTransaction(
                    id=charge.id,
                    amount=charge.amount / 100.0,
                    currency=charge.currency,
                    status=charge.status,
                    customer_id=charge.customer,
                    created_at=datetime.fromtimestamp(charge.created),
                    metadata=charge.metadata
                )
                for charge in charges.auto_paging_iter()
            ]
        except Exception as e:
            logger.error(
                "stripe.customer_transaction_fetch_failed",
                customer_id=customer_id,
                error=str(e)
            )
            return []

    async def get_transaction_stats(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        try:
            transactions = await self.get_transactions(start_date, end_date)
            
            return {
                'total_amount': sum(tx.amount for tx in transactions),
                'transaction_count': len(transactions),
                'successful_count': len([tx for tx in transactions if tx.status == 'succeeded']),
                'currency_breakdown': self._group_by_currency(transactions),
                'daily_volumes': self._calculate_daily_volumes(transactions)
            }
        except Exception as e:
            logger.error("stripe.stats_calculation_failed", error=str(e))
            return {}

    def _group_by_currency(self, transactions: List[StripeTransaction]) -> Dict:
        currency_totals = {}
        for tx in transactions:
            if tx.currency not in currency_totals:
                currency_totals[tx.currency] = 0
            currency_totals[tx.currency] += tx.amount
        return currency_totals

    def _calculate_daily_volumes(self, transactions: List[StripeTransaction]) -> Dict:
        daily_volumes = {}
        for tx in transactions:
            date_key = tx.created_at.date().isoformat()
            if date_key not in daily_volumes:
                daily_volumes[date_key] = 0
            daily_volumes[date_key] += tx.amount
        return daily_volumes
