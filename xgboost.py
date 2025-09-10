import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.preprocessing import MinMaxScaler
from xgboost import XGBRegressor

# Load dataset
df = pd.read_excel("elastic_modulus_dataset.xlsx")

# Separate features and target
X = df.drop(columns=["Elastic modulus"])
y = df["Elastic modulus"].values.reshape(-1, 1)

# Scale output to range [1, 2]
scaler_y = MinMaxScaler(feature_range=(1, 2))
y_scaled = scaler_y.fit_transform(y)

# Train/validation/test split
X_train_val, X_test, y_train_val, y_test = train_test_split(
    X, y_scaled, test_size=0.2, random_state=42
)

# Hyperparameter grid for XGBoost
param_grid = {
    "n_estimators": [100, 200, 400],
    "max_depth": [3, 6, 10],
    "learning_rate": [0.01, 0.1, 0.2],
    "subsample": [0.6, 0.8, 1.0],
    "colsample_bytree": [0.6, 0.8, 1.0],
    "min_child_weight": [1, 3, 5],
}

xgb = XGBRegressor(random_state=42, n_jobs=-1, objective='reg:squarederror')

grid_search = GridSearchCV(
    estimator=xgb,
    param_grid=param_grid,
    cv=5,
    scoring="r2",
    verbose=2,
    n_jobs=-1,
)

grid_search.fit(X_train_val, y_train_val.ravel())

print("Best Hyperparameters:", grid_search.best_params_)
print("Best CV R² Score:", grid_search.best_score_)


best_xgb = grid_search.best_estimator_
test_preds_scaled = best_xgb.predict(X_test)

test_preds = scaler_y.inverse_transform(test_preds_scaled.reshape(-1, 1)).ravel()
y_test_original = scaler_y.inverse_transform(y_test).ravel()

test_r2 = r2_score(y_test_original, test_preds)
test_mse = mean_squared_error(y_test_original, test_preds)

model_accuracy = test_r2 * 100

print("Test R² Score:", test_r2)
print("Test MSE:", test_mse)
print(f"Model Accuracy (0 to 100 scale): {model_accuracy:.2f}")
