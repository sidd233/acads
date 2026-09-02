import numpy as np
import pandas as pd

RANDOM_STATE = 42
TEST_SIZE = 0.2


def train_test_split(X, y, test_size=0.2, random_state=42):
    n_samples = X.shape[0]
    rng = np.random.RandomState(random_state)
    shuffled_idx = rng.permutation(n_samples)

    n_test = int(np.round(n_samples * test_size))
    test_idx = shuffled_idx[:n_test]
    train_idx = shuffled_idx[n_test:]

    return X[train_idx], X[test_idx], y[train_idx], y[test_idx]


class StandardScaler:
    """Z-score standardization: (x - mean) / std, fit on training data only."""

    def fit(self, X):
        self.mean_ = X.mean(axis=0)
        self.std_ = X.std(axis=0, ddof=0)
        return self

    def transform(self, X):
        return (X - self.mean_) / self.std_

    def fit_transform(self, X):
        return self.fit(X).transform(X)


def load_and_split(csv_path="auto_mpg.csv"):
    """Load the raw CSV, split into train/test, and impute missing horsepower
    using the training-set mean. Returns raw (unscaled) arrays."""
    df = pd.read_csv(csv_path)

    X = df[["vehicle_weight", "horsepower"]].to_numpy(dtype=float)
    y = df["miles_per_gallon"].to_numpy(dtype=float)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )

    hp_train_mean = np.nanmean(X_train[:, 1])
    X_train[np.isnan(X_train[:, 1]), 1] = hp_train_mean
    X_test[np.isnan(X_test[:, 1]), 1] = hp_train_mean

    return X_train, X_test, y_train, y_test, df


def prepare_data(csv_path="auto_mpg.csv"):
    """Load, split, impute and standardize the data. No printing / side effects.

    Returns X_train_std, X_test_std, y_train_std, y_test_std, x_scaler, y_scaler.
    """
    X_train, X_test, y_train, y_test, _ = load_and_split(csv_path)

    x_scaler = StandardScaler().fit(X_train)
    y_scaler = StandardScaler().fit(y_train.reshape(-1, 1))

    X_train_std = x_scaler.transform(X_train)
    X_test_std = x_scaler.transform(X_test)
    y_train_std = y_scaler.transform(y_train.reshape(-1, 1)).ravel()
    y_test_std = y_scaler.transform(y_test.reshape(-1, 1)).ravel()

    return X_train_std, X_test_std, y_train_std, y_test_std, x_scaler, y_scaler


def main():
    X_train, X_test, y_train, y_test, df = load_and_split()

    print("=" * 60)
    print("Raw dataset")
    print("=" * 60)
    print(f"Total samples        : {len(df)}")
    print(f"Missing horsepower   : {df['horsepower'].isna().sum()}")

    hp_train_mean = X_train[:, 1].mean()
    print(f"\nTraining-set horsepower mean used for imputation: {hp_train_mean:.4f}")

    x_scaler = StandardScaler().fit(X_train)
    y_scaler = StandardScaler().fit(y_train.reshape(-1, 1))

    X_train_std = x_scaler.transform(X_train)
    X_test_std = x_scaler.transform(X_test)
    y_train_std = y_scaler.transform(y_train.reshape(-1, 1)).ravel()
    y_test_std = y_scaler.transform(y_test.reshape(-1, 1)).ravel()

    print("\n" + "=" * 60)
    print("Final dataset sizes")
    print("=" * 60)
    print(f"Training samples : {X_train.shape[0]}  ({X_train.shape[0] / len(df):.1%})")
    print(f"Testing samples  : {X_test.shape[0]}  ({X_test.shape[0] / len(df):.1%})")

    print("\n" + "=" * 60)
    print("Descriptive statistics: raw training set (after imputation, before scaling)")
    print("=" * 60)
    train_raw_df = pd.DataFrame(
        {"vehicle_weight": X_train[:, 0], "horsepower": X_train[:, 1], "mpg": y_train}
    )
    print(train_raw_df.describe())

    print("\n" + "=" * 60)
    print("Descriptive statistics: raw test set (after imputation, before scaling)")
    print("=" * 60)
    test_raw_df = pd.DataFrame(
        {"vehicle_weight": X_test[:, 0], "horsepower": X_test[:, 1], "mpg": y_test}
    )
    print(test_raw_df.describe())

    print("\n" + "=" * 60)
    print("Standardization parameters (fit on training data only)")
    print("=" * 60)
    print(f"vehicle_weight mean, std : {x_scaler.mean_[0]:.4f}, {x_scaler.std_[0]:.4f}")
    print(f"horsepower     mean, std : {x_scaler.mean_[1]:.4f}, {x_scaler.std_[1]:.4f}")
    print(f"mpg            mean, std : {y_scaler.mean_[0]:.4f}, {y_scaler.std_[0]:.4f}")

    print("\n" + "=" * 60)
    print("Descriptive statistics: standardized training set")
    print("=" * 60)
    train_std_df = pd.DataFrame(
        {"vehicle_weight": X_train_std[:, 0], "horsepower": X_train_std[:, 1], "mpg": y_train_std}
    )
    print(train_std_df.describe())

    print("\n" + "=" * 60)
    print("Descriptive statistics: standardized test set")
    print("=" * 60)
    test_std_df = pd.DataFrame(
        {"vehicle_weight": X_test_std[:, 0], "horsepower": X_test_std[:, 1], "mpg": y_test_std}
    )
    print(test_std_df.describe())

    return X_train_std, X_test_std, y_train_std, y_test_std, x_scaler, y_scaler


if __name__ == "__main__":
    main()
