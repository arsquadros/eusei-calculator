METRICS_CONFIG = {
    "hours": {
        "display_name": "Tempo Estimado em Horas",
        "weight": 0.15,
        "min": 0.0,
        "max": 200.0,
        "type": "number",
        "description": "Estimativa bruta de tempo focado para conclusão, sem considerar interrupções.",
        "how_to_estimate": "Considere o tempo de desenvolvimento puro (mão na massa). Se passar de 160h, a tarefa deve ser quebrada."
    },
    "tech_complexity": {
        "display_name": "Complexidade Técnica",
        "weight": 0.35,
        "min": 1,
        "max": 10,
        "type": "slider",
        "description": "Dificuldade de implementação técnica.",
        "how_to_estimate": "Avalie o quão difícil é a implementação: uso de novas tecnologias, algoritmos complexos ou refatorações profundas."
    },
    "manual_effort": {
        "display_name": "Esforço Manual",
        "weight": 0.15,
        "min": 1,
        "max": 10,
        "type": "slider",
        "description": "Trabalho braçal ou repetitivo.",
        "how_to_estimate": "Avalie quanto tempo será gasto em setups manuais, preenchimento de planilhas ou testes que não podem ser automatizados."
    },
    "uncertainty": {
        "display_name": "Incertezas",
        "weight": 0.35,
        "min": 1,
        "max": 10,
        "type": "slider",
        "description": "Falta de clareza ou dependências externas.",
        "how_to_estimate": "Quanto maior o risco de bloqueio por outros times ou requisitos vagos, maior deve ser este valor."
    }
}
