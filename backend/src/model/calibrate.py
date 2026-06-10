from sklearn.calibration import CalibratedClassifierCV

def fit_calibration(estimator, X, y, cv=5, method="sigmoid"):
    """
    Applies Platt scaling calibration to the model using CalibratedClassifierCV.
    """
    print(f"Applying Platt scaling calibration ({method}, cv={cv})...")
    calibrated_clf = CalibratedClassifierCV(estimator=estimator, method=method, cv=cv)
    calibrated_clf.fit(X, y)
    return calibrated_clf
