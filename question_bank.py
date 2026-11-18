import random

QUESTION_BANK = {
    "Python": [
        {
            "difficulty": "Easy",
            "question": "Which keyword is used to define a function in Python?",
            "options": ["func", "def", "function", "define"],
            "answer": "B",
            "explanation": "Python uses the def keyword to define a function."
        },
        {
            "difficulty": "Easy",
            "question": "Which data type stores True or False?",
            "options": ["String", "Integer", "Boolean", "List"],
            "answer": "C",
            "explanation": "Boolean stores True or False values."
        },
        {
            "difficulty": "Medium",
            "question": "What is the output of len([10, 20, 30])?",
            "options": ["2", "3", "4", "30"],
            "answer": "B",
            "explanation": "The list contains three elements."
        },
        {
            "difficulty": "Medium",
            "question": "Which data structure stores key-value pairs?",
            "options": ["Tuple", "Set", "Dictionary", "String"],
            "answer": "C",
            "explanation": "A dictionary stores information as key-value pairs."
        },
        {
            "difficulty": "Hard",
            "question": "What does a Python lambda expression create?",
            "options": ["A loop", "An anonymous function", "A class", "A module"],
            "answer": "B",
            "explanation": "Lambda creates a small anonymous function."
        }
    ],

    "Data Analysis": [
        {
            "difficulty": "Easy",
            "question": "Which library is commonly used for tabular data analysis in Python?",
            "options": ["Pandas", "Flask", "Django", "Turtle"],
            "answer": "A",
            "explanation": "Pandas provides DataFrames for tabular data analysis."
        },
        {
            "difficulty": "Easy",
            "question": "What does CSV stand for?",
            "options": [
                "Computer System Value",
                "Comma Separated Values",
                "Common Source Variable",
                "Column System View"
            ],
            "answer": "B",
            "explanation": "CSV means Comma Separated Values."
        },
        {
            "difficulty": "Medium",
            "question": "Which measure represents the middle value of sorted data?",
            "options": ["Mean", "Mode", "Median", "Range"],
            "answer": "C",
            "explanation": "Median is the middle value after sorting."
        },
        {
            "difficulty": "Medium",
            "question": "Which Pandas method displays the first rows of a DataFrame?",
            "options": ["tail()", "head()", "show()", "first()"],
            "answer": "B",
            "explanation": "head() displays the first rows."
        },
        {
            "difficulty": "Hard",
            "question": "What is the main purpose of data cleaning?",
            "options": [
                "Increase file size",
                "Remove errors and inconsistencies",
                "Create random data",
                "Delete all columns"
            ],
            "answer": "B",
            "explanation": "Data cleaning improves data quality."
        }
    ],

    "Machine Learning": [
        {
            "difficulty": "Easy",
            "question": "Which type of learning uses labelled training data?",
            "options": [
                "Supervised learning",
                "Unsupervised learning",
                "Reinforcement learning",
                "Random learning"
            ],
            "answer": "A",
            "explanation": "Supervised learning trains using labelled examples."
        },
        {
            "difficulty": "Easy",
            "question": "Which task predicts a continuous numerical value?",
            "options": ["Classification", "Regression", "Clustering", "Sorting"],
            "answer": "B",
            "explanation": "Regression predicts continuous numerical values."
        },
        {
            "difficulty": "Medium",
            "question": "What is overfitting?",
            "options": [
                "Model performs poorly on training data",
                "Model memorizes training data and generalizes poorly",
                "Model has no input data",
                "Model always predicts the mean"
            ],
            "answer": "B",
            "explanation": "Overfitting occurs when a model learns training-specific patterns."
        },
        {
            "difficulty": "Medium",
            "question": "Which algorithm is commonly used for classification?",
            "options": [
                "Linear Regression",
                "K-Nearest Neighbors",
                "PCA only",
                "Mean calculation"
            ],
            "answer": "B",
            "explanation": "K-Nearest Neighbors can classify samples using nearby examples."
        },
        {
            "difficulty": "Hard",
            "question": "What is the purpose of a test dataset?",
            "options": [
                "Train the model repeatedly",
                "Evaluate performance on unseen data",
                "Remove features",
                "Replace the training dataset"
            ],
            "answer": "B",
            "explanation": "The test dataset evaluates performance on unseen data."
        }
    ],

    "Statistics": [
        {
            "difficulty": "Easy",
            "question": "What is the mean of 2, 4, and 6?",
            "options": ["2", "3", "4", "6"],
            "answer": "C",
            "explanation": "(2 + 4 + 6) / 3 = 4."
        },
        {
            "difficulty": "Easy",
            "question": "Which measure identifies the most frequent value?",
            "options": ["Mean", "Median", "Mode", "Variance"],
            "answer": "C",
            "explanation": "Mode is the value that occurs most frequently."
        },
        {
            "difficulty": "Medium",
            "question": "What does standard deviation measure?",
            "options": [
                "Data spread around the mean",
                "Number of rows",
                "Maximum value only",
                "Data type"
            ],
            "answer": "A",
            "explanation": "Standard deviation measures data spread."
        },
        {
            "difficulty": "Medium",
            "question": "What is the probability of getting heads in a fair coin toss?",
            "options": ["0", "0.25", "0.5", "1"],
            "answer": "C",
            "explanation": "Heads probability is 1/2 or 0.5."
        },
        {
            "difficulty": "Hard",
            "question": "What does correlation measure?",
            "options": [
                "Causal relationship in every case",
                "Association between variables",
                "The number of observations",
                "The median of variables"
            ],
            "answer": "B",
            "explanation": "Correlation measures association, not necessarily causation."
        }
    ]
}


def get_questions(topic, difficulty=None, count=5):
    questions = QUESTION_BANK.get(topic, [])

    if difficulty:
        questions = [
            q for q in questions
            if q["difficulty"].lower() == difficulty.lower()
        ]

    if not questions:
        return []

    return random.sample(questions, min(count, len(questions)))