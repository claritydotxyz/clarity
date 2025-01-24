"""
State management for the UI using Zustand store.
"""
from .store import useStore
from .actions import {
    fetchInsights,
    updateSettings,
    generateReport,
    fetchUserData
}

__all__ = [
    'useStore',
    'fetchInsights',
    'updateSettings',
    'generateReport',
    'fetchUserData'
]
