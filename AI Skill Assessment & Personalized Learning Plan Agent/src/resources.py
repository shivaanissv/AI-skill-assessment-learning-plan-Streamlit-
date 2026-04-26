from __future__ import annotations

from typing import Dict, List

from src.models import LearningResource


RESOURCE_DB: Dict[str, List[LearningResource]] = {
    "Python": [
        LearningResource("Python Official Tutorial", "https://docs.python.org/3/tutorial/", "docs"),
        LearningResource("Real Python Learning Paths", "https://realpython.com/learning-paths/", "guided"),
        LearningResource("Exercism Python Track", "https://exercism.org/tracks/python", "practice"),
    ],
    "SQL": [
        LearningResource("Mode SQL Tutorial", "https://mode.com/sql-tutorial/", "tutorial"),
        LearningResource("SQLBolt", "https://sqlbolt.com/", "interactive"),
        LearningResource("LeetCode Database Problems", "https://leetcode.com/problemset/database/", "practice"),
    ],
    "Machine Learning": [
        LearningResource("Google ML Crash Course", "https://developers.google.com/machine-learning/crash-course", "course"),
        LearningResource("scikit-learn User Guide", "https://scikit-learn.org/stable/user_guide.html", "docs"),
        LearningResource("Kaggle Learn", "https://www.kaggle.com/learn", "course"),
    ],
    "System Design": [
        LearningResource("System Design Primer", "https://github.com/donnemartin/system-design-primer", "repo"),
        LearningResource("ByteByteGo Free Articles", "https://blog.bytebytego.com/", "articles"),
        LearningResource("High Scalability", "http://highscalability.com/", "blog"),
    ],
    "Cloud": [
        LearningResource("AWS Skill Builder Free Tier", "https://explore.skillbuilder.aws/learn", "course"),
        LearningResource("Microsoft Learn Azure Paths", "https://learn.microsoft.com/training/azure/", "course"),
        LearningResource("Google Cloud Skills Boost", "https://www.cloudskillsboost.google/", "labs"),
    ],
    "Communication": [
        LearningResource("Pyramid Principle Notes", "https://untools.co/pyramid-principle/", "framework"),
        LearningResource("HBR Communication Guide", "https://hbr.org/topic/subject/communication", "articles"),
        LearningResource("Toastmasters Tips", "https://www.toastmasters.org/resources/public-speaking-tips", "practice"),
    ],
    "Data Analysis": [
        LearningResource("Pandas User Guide", "https://pandas.pydata.org/docs/user_guide/index.html", "docs"),
        LearningResource("Khan Academy Statistics", "https://www.khanacademy.org/math/statistics-probability", "course"),
        LearningResource("DataCamp Free Chapters", "https://www.datacamp.com/", "practice"),
    ],
}


def get_resources_for_skill(skill: str) -> List[LearningResource]:
    if skill in RESOURCE_DB:
        return RESOURCE_DB[skill]
    return [
        LearningResource("Roadmap.sh", "https://roadmap.sh/", "roadmap"),
        LearningResource("freeCodeCamp", "https://www.freecodecamp.org/", "course"),
    ]
