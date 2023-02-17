import argparse
import csv
import json
import random
import string

import dill
import numpy as np
import pandas as pd
from desdeo_problem.problem import _ScalarObjective
from desdeo_problem.problem import DiscreteDataProblem
from desdeo_problem.surrogatemodels.lipschitzian import LipschitzianRegressor
from desdeo_problem.problem import Variable

from app import db
from models.problem_models import Problem as ProblemModel
from models.user_models import UserModel
from models.questionnaire_models import Question, Questionnaire

parser = argparse.ArgumentParser(
    description="Add N new user to the database with a pre-defined problem. and a given username prefix."
)
parser.add_argument("--N", type=int, help="The number of usernames to be added.", required=True)

dill.settings["recurse"] = True

db.drop_all()
db.create_all()

args = vars(parser.parse_args())

def create_questionnaire(id: int, type:str, group:int):
    return {"id": id, "type": type, "group": group}

def create_question(question_id:int, questionnaire_id: int, question_txt: str, question_type: str, show_solution:int):
    return {"id": question_id, "questionnaire_id": questionnaire_id, "question_txt": question_txt, "question_type": question_type, "show_solution": show_solution}

def main():
    letters = string.ascii_lowercase
    args = vars(parser.parse_args())
    methods = ["nimbus", "nautilus_nimbus"]
    usernames = [[f"{method}_{n}" for n in range(1, args["N"]+1)] for method in methods]
    usernames = sum(usernames, [])
    passwords = [("".join(random.choice(letters) for i in range(6))) for j in range(len(usernames))]

    try:
        for (username, password) in zip(usernames, passwords):
            add_user(username, password)
            add_sus_problem(username)
    except Exception as e:
        print("something went wrong...")
        print(e)
        exit()

    with open("users_and_pass.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile, delimiter=" ", quotechar="|", quoting=csv.QUOTE_MINIMAL)
        list(map(lambda x: writer.writerow(x), zip(usernames, passwords)))

    print(f"Added users {usernames} to the database succesfully.")
    questionnaires = []
    questionnaires.append(create_questionnaire(1, "Demographic",0)) #0 = both groups 1= one method 2= switch method
    questionnaires.append(create_questionnaire(2, "Init",0)) 
    questionnaires.append(create_questionnaire(3, "End",0))
    questionnaires.append(create_questionnaire(4, "End",2))

    questions = []

    #Questions for demographic survey
    questions.append(create_question(1, 1, "Age", "age", 0))
    questions.append(create_question(2, 1, "Gender", "gender", 0))
    questions.append(create_question(3, 1, "Nationality", "open", 0))
    questions.append(create_question(4, 1, "Background", "open", 0))
    questions.append(create_question(5, 1, "Did you have any prior knowledge about these methods other than what you have learnt in this course?", "bool", 0))

    #Questions initial survey
    questions.append(create_question(6, 2, "I am now feeling tired.", "likert", 0))
    questions.append(create_question(7, 2, "What objective function values do you think you can achieve as your final solution?", "open", 0))

    #Questions final survey (both groups)
    questions.append(create_question(8, 3, "I am now feeling tired.","likert",0))
    questions.append(create_question(9, 3, "I am satisfied with my final solution. ","likert",1))
    questions.append(create_question(10, 3, "Please describe why.","open",0))
    questions.append(create_question(11, 3, "I think that the solution I found is the best one.","likert",0))
    questions.append(create_question(12, 3, "Interacting with this decision support tool helped me to understand more about the tradeoffs in this problem.","likert",0))
    questions.append(create_question(13, 3, "What did you find new or unexpected compared to what you knew or expected before starting the solution process? Please specify. ","open",0))
    questions.append(create_question(14, 3, "A lot of mental activity (e.g., thinking, deciding, and remembering) was required to find my final solution.","likert",0))
    questions.append(create_question(15, 3, "The process of finding the final solution was difficult.","likert",0))
    questions.append(create_question(16, 3, "It was easy to learn to use this decision support tool.","likert",0))
    questions.append(create_question(17, 3, "I felt I was in control during the solution process.","likert",0))
    questions.append(create_question(18, 3, "I felt comfortable using this decision support tool.  ","likert",0))
    questions.append(create_question(19, 3, "I felt frustrated in the solution process (e.g., insecure, discouraged, irritated, stressed).","likert",0))
    questions.append(create_question(20, 3, "Please, explain why or why not. ","open",0))
    questions.append(create_question(21, 3, "Overall, I am satisfied with the ease of completing this task.","likert",0))
    questions.append(create_question(22, 3, "Overall, I am satisfied with the amount of time it took to complete this task.","likert",0))

    #Questions final survey (second group)
    questions.append(create_question(23, 4, "Phase 1 enabled exploring solutions with different conflicting values of the objective functions.", "likert", 0))
    questions.append(create_question(24, 4, "Phase 1 enabled me to learn about the conflict degrees among the objectives.", "likert", 0))
    questions.append(create_question(25, 4, "Phase 1 enabled me to direct the search toward  a set of interesting solutions.", "likert", 0))
    questions.append(create_question(26, 4, "Phase 1 played an important role in fine-tuning the final solution.", "likert", 0))
    questions.append(create_question(27, 4, "Phase 1 increased my confidence in the final solution.", "likert", 0))
    questions.append(create_question(28, 4, "Do you have other comments about Phase 1? If so, please specify.", "open", 0))
    questions.append(create_question(29, 4, "Phase 2 enabled exploring solutions with different conflicting values of the objective functions. ", "likert", 0))
    questions.append(create_question(30, 4, "Phase 2 enabled me to learn about the conflict degrees among the objectives.", "likert", 0))
    questions.append(create_question(31, 4, "Phase 2 enabled me to direct the search toward  a set of interesting solutions.", "likert", 0))
    questions.append(create_question(32, 4, "Phase 2 played an important role in fine-tuning the final solution.", "likert", 0))
    questions.append(create_question(33, 4, "Phase 2 increased my confidence in the final solution.", "likert", 0))
    questions.append(create_question(34, 4, "Do you have other comments about Phase 2? If so, please specify.", "open", 0))
    questions.append(create_question(35, 4, "Using the two phases supported me in finding the final solution.", "likert", 0))
    questions.append(create_question(36, 4, "The types of preference information required in the  two phases were different. Switching between these types of preference information was easy.", "likert", 0))
    questions.append(create_question(37, 4, "I feel that the final solution is better than the one obtained at the end of Phase 1.", "likert", 0))
    questions.append(create_question(38, 4, "I feel that Phase 1 made it easier to find a good solution at the end of the solution process.", "likert", 0))

    try:
        for questionnaire in questionnaires:
            add_questionaire(id=questionnaire["id"], type=questionnaire["type"], group=questionnaire["group"])
        for question in questions:
            add_question(id=question["id"], questionnaire_id=question["questionnaire_id"], question_txt=question["question_txt"], question_type=question["question_type"], show_solution=question["show_solution"])

    except Exception as e:
        print("something went wrong...")
        print(e)
        exit()

    print(f"Added questions to the database succesfully.")


def add_user(username, password):
    db.session.add(UserModel(username=username, password=UserModel.generate_hash(password)))
    db.session.commit()


def add_sus_problem(username):
    user_query = UserModel.query.filter_by(username=username).first()
    if user_query is None:
        print(f"USername {username} not found")
        return
    else:
        id = user_query.id

    file_name = "./tests/data/sustainability_spanish.csv"

    data = pd.read_csv(file_name)
    # minus because all are to be maximized
    data[["social", "economic", "environmental"]] = -data[["social", "economic", "environmental"]]

    var_names = [f"x{i}" for i in range(1, 12)]

    ideal = data[["social", "economic", "environmental"]].min().values
    nadir = data[["social", "economic", "environmental"]].max().values

    # define the sus problem
    var_names = [f"x{i}" for i in range(1, 12)]
    obj_names = ["social", "economic", "environmental"]

    problem = DiscreteDataProblem(data, var_names, obj_names, ideal, nadir)

    db.session.add(
        ProblemModel(
            name="Spanish sustainability problem",
            problem_type="Discrete",
            problem_pickle=problem,
            user_id=id,
            minimize=json.dumps([-1, -1, -1]),
        )
    )
    db.session.commit()
    print(f"Sustainability problem added for user '{username}'")

def add_question(id, questionnaire_id, question_txt, question_type, show_solution):
    db.session.add(Question(id=id, questionnaire_id=questionnaire_id, question_txt=question_txt, question_type=question_type, show_solution=show_solution))
    db.session.commit()

def add_questionaire(id, type, group):
    db.session.add(Questionnaire(id=id, type=type, group=group))
    db.session.commit()

if __name__ == "__main__":
    main()
