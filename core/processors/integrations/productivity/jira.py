from typing import Dict, List, Optional
from datetime import datetime
from jira import JIRA
from clarity.schemas.productivity import (
    JiraIssue,
    JiraWorklog,
    JiraMetrics
)
import structlog

logger = structlog.get_logger()

class JiraProcessor:
    def __init__(self, url: str, token: str):
        self.client = JIRA(url, token_auth=token)

    async def get_user_issues(
        self,
        username: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[JiraIssue]:
        try:
            jql = (
                f'assignee = {username} AND '
                f'updated >= {start_date.strftime("%Y-%m-%d")} AND '
                f'updated <= {end_date.strftime("%Y-%m-%d")}'
            )
            issues = self.client.search_issues(jql)
            
            return [
                JiraIssue(
                    key=issue.key,
                    summary=issue.fields.summary,
                    status=issue.fields.status.name,
                    priority=issue.fields.priority.name,
                    created=issue.fields.created,
                    updated=issue.fields.updated,
                    assignee=issue.fields.assignee.displayName,
                    project=issue.fields.project.key
                )
                for issue in issues
            ]
        except Exception as e:
            logger.error("jira.issue_fetch_failed", error=str(e))
            return []

    async def get_user_worklogs(
        self,
        username: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[JiraWorklog]:
        try:
            worklogs = []
            issues = await self.get_user_issues(username, start_date, end_date)
            
            for issue in issues:
                issue_worklogs = self.client.worklogs(issue.key)
                worklogs.extend([
                    JiraWorklog(
                        id=worklog.id,
                        issue_key=issue.key,
                        author=worklog.author.displayName,
                        time_spent_seconds=worklog.timeSpentSeconds,
                        started=worklog.started,
                        comment=worklog.comment
                    )
                    for worklog in issue_worklogs
                    if start_date <= worklog.started <= end_date
                ])
            
            return worklogs
        except Exception as e:
            logger.error("jira.worklog_fetch_failed", error=str(e))
            return []

    async def get_metrics(
        self,
        username: str,
        start_date: datetime,
        end_date: datetime
    ) -> JiraMetrics:
        try:
            issues = await self.get_user_issues(username, start_date, end_date)
            worklogs = await self.get_user_worklogs(username, start_date, end_date)
            
            return JiraMetrics(
                total_issues=len(issues),
                open_issues=len([i for i in issues if i.status == 'Open']),
                in_progress=len([i for i in issues if i.status == 'In Progress']),
                completed=len([i for i in issues if i.status in ['Done', 'Closed']]),
                total_time_spent=sum(w.time_spent_seconds for w in worklogs),
                average_time_per_issue=(
                    sum(w.time_spent_seconds for w in worklogs) / len(issues)
                    if issues else 0
                )
            )
        except Exception as e:
            logger.error("jira.metrics_calculation_failed", error=str(e))
            return JiraMetrics()
