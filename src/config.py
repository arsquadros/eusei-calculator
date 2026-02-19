# core/config.py

METRICS_CONFIG = {
    "hours": {
        "display_name": "Tempo Estimado (Horas)",
        "weight": 0.15,
        "min": 0.0,
        "max": 200.0,
        "type": "number"
    },
    "tech_complexity": {
        "display_name": "Complexidade Técnica",
        "weight": 0.35,
        "min": 1,
        "max": 10,
        "type": "slider"
    },
    "manual_effort": {
        "display_name": "Esforço Manual",
        "weight": 0.15,
        "min": 1,
        "max": 10,
        "type": "slider"
    },
    "uncertainty": {
        "display_name": "Incertezas",
        "weight": 0.35,
        "min": 1,
        "max": 10,
        "type": "slider"
    }
}