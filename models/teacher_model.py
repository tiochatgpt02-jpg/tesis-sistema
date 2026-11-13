from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional


@dataclass
class TopicGeneration:
    title: str
    description: str
    grade: int
    explanation: str
    examples: List[str]
    activities: List[Dict[str, Any]]
    evaluation_questions: List[Dict[str, Any]]
    game: Dict[str, Any]
    feedback: str
    status: str = 'En proceso'

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DashboardMetric:
    total_students: int
    students_by_grade: Dict[str, int]
    average_progress: int
    activities_count: int
    evaluations_count: int
    available_topics: int
    low_performance_students: List[str]
    performance_by_grade: Dict[str, int]
    alerts: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
