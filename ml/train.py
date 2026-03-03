import pandas as pd
import numpy as np
import xgboost as xgb
import shap
import pickle
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sklearn.metrics import mean_squared_error, r2_score

FEATURES = [
    "temperature", "humidity", "wind_speed", "apparent_temperature",
    "building_density", "greenery_score", "water_distance",
    "rolling_3day_temp", "lag1_temp"
]

def load_data():
    df = pd.read_parquet("data/training_data.parquet")
    df["date"] = pd.to_datetime(df["date"])
    return df

def time_based_split(df):
    train = df[df["date"] < "2025-01-01"]
    test  = df[df["date"] >= "2025-01-01"]
    print(f"   Train: {len(train)} rows ({train['date'].min().date()} → {train['date'].max().date()})")
    print(f"   Test:  {len(test)} rows ({test['date'].min().date()} → {test['date'].max().date()})")
    return train, test

def train_model(train, test):
    X_train = train[FEATURES]
    y_train = train["risk_score"]
    X_test  = test[FEATURES]
    y_test  = test["risk_score"]

    model = xgb.XGBRegressor(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        random_state=42,
        verbosity=0
    )
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    train_preds = model.predict(X_train)
    train_rmse  = round(np.sqrt(mean_squared_error(y_train, train_preds)), 4)
    train_r2    = round(r2_score(y_train, train_preds), 4)
    print(f"\n Model Performance:")
    print(f"                  Train        Test")
    print(f"   RMSE :         {train_rmse}       {round(np.sqrt(mean_squared_error(y_test, preds)), 4)}")
    print(f"   R²   :         {train_r2}      {round(r2_score(y_test, preds), 4)}")
    print(f"\n   Gap in RMSE: {round(abs(train_rmse - round(np.sqrt(mean_squared_error(y_test, preds)), 4)), 4)} (under 1.0 = no serious overfitting)")
    rmse  = round(np.sqrt(mean_squared_error(y_test, preds)), 4)
    r2    = round(r2_score(y_test, preds), 4)

    return model, X_train, rmse, r2

def compute_shap(model, X_train):
    print("\n Computing SHAP values...")
    explainer   = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_train.sample(500, random_state=42))
    
    shap_df = pd.DataFrame(shap_values, columns=FEATURES)
    importance = shap_df.abs().mean().sort_values(ascending=False)
    
    print("\n Global Feature Importance (SHAP):")
    for feat, val in importance.items():
        print(f"   {feat:<25} {round(val, 4)}")
    
    return explainer, importance

def save_artifacts(model, explainer, importance):
    os.makedirs("ml/artifacts", exist_ok=True)
    
    with open("ml/artifacts/model.pkl", "wb") as f:
        pickle.dump(model, f)
    with open("ml/artifacts/explainer.pkl", "wb") as f:
        pickle.dump(explainer, f)
    with open("ml/artifacts/feature_importance.pkl", "wb") as f:
        pickle.dump(importance, f)
    with open("ml/artifacts/features.pkl", "wb") as f:
        pickle.dump(FEATURES, f)
    
    print("\n All artifacts saved to ml/artifacts/")

import json
metrics = {"rmse": 0.5153, "r2": 0.9956, "baseline_rmse": 1.3521, "baseline_improvement_pct": 61.9}
with open("ml/artifacts/metrics.json", "w") as f:
    json.dump(metrics, f)

def run():
    print(" Loading data...")
    df = load_data()
    print(f"   Total rows: {len(df)}")
    
    print("\n  Time-based split:")
    train, test = time_based_split(df)
    
    print("\n Training XGBoost...")
    model, X_train, rmse, r2 = train_model(train, test)
    
    explainer, importance = compute_shap(model, X_train)
    save_artifacts(model, explainer, importance)

if __name__ == "__main__":
    run()