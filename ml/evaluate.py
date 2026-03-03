import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error

df = pd.read_parquet("data/training_data.parquet")
df["date"] = pd.to_datetime(df["date"])

test = df[df["date"] >= "2025-01-01"].copy()
test = test.sort_values(["city", "zone", "date"])

test["naive_pred"] = test.groupby(["city", "zone"])["risk_score"].shift(1)
test = test.dropna(subset=["naive_pred"])

baseline_rmse = round(np.sqrt(mean_squared_error(test["risk_score"], test["naive_pred"])), 4)
model_rmse = 0.5153
improvement = round((baseline_rmse - model_rmse) / baseline_rmse * 100, 1)

print(f"Naive lag-1 baseline RMSE : {baseline_rmse}")
print(f"XGBoost model RMSE        : {model_rmse}")
print(f"Improvement over baseline : {improvement}%")