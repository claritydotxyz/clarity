from typing import Dict, List, Optional
from datetime import datetime
from github import Github
from clarity.schemas.productivity import (
    Commit,
    PullRequest,
    Repository,
    ContributionStats
)
import structlog

logger = structlog.get_logger()

class GithubProcessor:
    def __init__(self, token: str):
        self.client = Github(token)
        
    async def get_user_activity(
        self,
        username: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        try:
            user = self.client.get_user(username)
            repos = user.get_repos()
            
            commits = await self._get_user_commits(repos, start_date, end_date)
            prs = await self._get_user_prs(repos, start_date, end_date)
            stats = await self._calculate_stats(commits, prs)
            
            return {
                'commits': commits,
                'pull_requests': prs,
                'stats': stats
            }
        except Exception as e:
            logger.error("github.activity_fetch_failed", error=str(e))
            return {}

    async def _get_user_commits(
        self,
        repos: List[Repository],
        start_date: datetime,
        end_date: datetime
    ) -> List[Commit]:
        commits = []
        for repo in repos:
            try:
                repo_commits = repo.get_commits(
                    author=repo.owner.login,
                    since=start_date,
                    until=end_date
                )
                commits.extend([
                    Commit(
                        id=commit.sha,
                        message=commit.commit.message,
                        author=commit.author.login if commit.author else None,
                        timestamp=commit.commit.author.date,
                        repository=repo.name,
                        additions=commit.stats.additions,
                        deletions=commit.stats.deletions
                    )
                    for commit in repo_commits
                ])
            except Exception as e:
                logger.error(
                    "github.commit_fetch_failed",
                    repo=repo.name,
                    error=str(e)
                )
        return commits

    async def _get_user_prs(
        self,
        repos: List[Repository],
        start_date: datetime,
        end_date: datetime
    ) -> List[PullRequest]:
        prs = []
        for repo in repos:
            try:
                repo_prs = repo.get_pulls(
                    state='all',
                    sort='created',
                    direction='desc'
                )
                prs.extend([
                    PullRequest(
                        id=pr.number,
                        title=pr.title,
                        state=pr.state,
                        created_at=pr.created_at,
                        merged_at=pr.merged_at,
                        repository=repo.name,
                        additions=pr.additions,
                        deletions=pr.deletions
                    )
                    for pr in repo_prs
                    if start_date <= pr.created_at <= end_date
                ])
            except Exception as e:
                logger.error(
                    "github.pr_fetch_failed",
                    repo=repo.name,
                    error=str(e)
                )
        return prs

    async def _calculate_stats(
        self,
        commits: List[Commit],
        prs: List[PullRequest]
    ) -> ContributionStats:
        return ContributionStats(
            total_commits=len(commits),
            total_prs=len(prs),
            total_additions=sum(c.additions for c in commits),
            total_deletions=sum(c.deletions for c in commits),
            merged_prs=len([pr for pr in prs if pr.merged_at]),
            avg_pr_size=sum(pr.additions + pr.deletions for pr in prs) / len(prs) if prs else 0
        )
