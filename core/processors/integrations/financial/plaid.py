from typing import Dict, List, Optional
from datetime import datetime
import plaid
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.accounts_get_request import AccountsGetRequest
from clarity.schemas.financial import Transaction, Account, PlaidCredentials
import structlog

logger = structlog.get_logger()

class PlaidProcessor:
    def __init__(self, credentials: PlaidCredentials):
        self.client = plaid.Client(
            client_id=credentials.client_id,
            secret=credentials.secret,
            environment=credentials.environment
        )

    async def get_transactions(
        self,
        access_token: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Transaction]:
        try:
            request = TransactionsGetRequest(
                access_token=access_token,
                start_date=start_date.date(),
                end_date=end_date.date()
            )
            response = self.client.transactions_get(request)
            
            return [
                Transaction(
                    id=tx.transaction_id,
                    amount=tx.amount,
                    date=datetime.strptime(tx.date, '%Y-%m-%d'),
                    category=tx.category[0] if tx.category else None,
                    merchant=tx.merchant_name,
                    account_id=tx.account_id
                )
                for tx in response.transactions
            ]
        except Exception as e:
            logger.error("plaid.transaction_fetch_failed", error=str(e))
            return []

    async def get_accounts(self, access_token: str) -> List[Account]:
        try:
            request = AccountsGetRequest(access_token=access_token)
            response = self.client.accounts_get(request)
            
            return [
                Account(
                    id=account.account_id,
                    name=account.name,
                    type=account.type,
                    subtype=account.subtype,
                    balance=account.balances.current
                )
                for account in response.accounts
            ]
        except Exception as e:
            logger.error("plaid.account_fetch_failed", error=str(e))
            return []
