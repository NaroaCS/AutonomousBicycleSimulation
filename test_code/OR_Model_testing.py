# OptimizationModelingTest
# Following: https://medium.com/opex-analytics/optimization-modeling-in-python-pulp-gurobi-and-cplex-83a62129807a

import random
import pulp as plp
import pandas as pd

# Placeholder for the model
opt_model = plp.LpProblem(name="MIP Model")


# Input parameters (This would be given)
n = 10
m = 5
set_I = range(1, n + 1)
set_J = range(1, m + 1)
c = {(i, j): random.normalvariate(0, 1) for i in set_I for j in set_J}
a = {(i, j): random.normalvariate(0, 5) for i in set_I for j in set_J}
l = {(i, j): random.randint(0, 10) for i in set_I for j in set_J}
u = {(i, j): random.randint(10, 20) for i in set_I for j in set_J}
b = {(i, j): random.randint(0, 1) for i in set_I for j in set_J}


# Adding decision variables as dictionaries -> Type(cont,binary, int), lower bound 0 by default, upper bound inf by default

# if x is continous
x_vars = {(i, j): plp.LpVariable(cat=plp.LpContinous, lowBound=l[i, j], upBound=u[i, j], name="x_{0}_{1}".format(i, j),) for i in set_I for j in set_J}

# if x is Binary
x_vars = {(i, j): plp.LpVariable(cat=plp.LpBinary, name="x_{0}_{1}".format(i, j)) for i in set_I for j in set_J}

# if x in Integer
x_vars = {(i, j): plp.LpVariable(cat=plp.LpInteger, lowBound=l[i, j], upBound=u[i, j], name="x_{0}_{1}".format(i, j),) for i in set_I for j in set_J}

# Setting constraints

# <= constraints
constraints = {j: opt_model.addConstraint(plp.LpConstraint(e=m(a[i, j] * x_vars[i, j] for i in set_I), sense=plp.plp.LpConstraintLE, rhs=b[j], name="constrainbt_{0}".format(j),)) for j in set_J}

# >= constraints
constraints = {j: opt_model.addConstraint(plp.LpConstraint(e=plp.lpSum(a[i, j] * x_vars[i, j] for i in set_I), sense=plp.LpConstraintGE, rhs=b[j], name="constraint_{0}".format(j),)) for j in set_J}

# == constraints
constraints = {j: opt_model.addConstraint(plp.Constraint(e=plp.lpSum(a[i, j] * x_vars[i, j] for i in set_I), sense=plp.LpConstraintEQ, rhs=b[j], name="constraint_{0}".format(j),)) for j in set_J}

# Objective function
objective = plp.lpSum(x_vars[i, j] * c[i, j] for i in set_I for j in set_J)

# Objective of the model

# for maximization
opt_model.sense = plp.LpMaximize

# for minimization
# opt_model.sense = plp.LpMinimize

opt_model.setObjective(objective)

# Solve model

# Solving with CBC
opt_model.solve()

# solve with Glpk
opt_model.solve(solver=GLPK_CMD())


# Save the data in a pandas df

opt_df = pd.DataFrame.from_dict(x_vars, orient="index", columns=["variable_object"])

opt_df.index = pd.MultiIndex.from_tuples(opt_df.index, names=["column_i", "column_j"])
opt_df.reset_index(inplace=True)

# SaveData
opt_df["solution_value"] = opt_df["variable_object"].apply(lambda item: item.varValue)

opt_df.drop(columns=["variable_object"], inplace=True)
opt_df.to_csv("./optimization_solution.csv")
