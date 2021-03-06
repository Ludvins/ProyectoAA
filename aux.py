#!/usr/bin/env python3


#######################################################
##################### IMPORTS #########################
#######################################################

import math
import threading
import time

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams

from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline
from sklearn.feature_selection import VarianceThreshold
from sklearn.manifold import TSNE

from sklearn.linear_model import (
    LassoCV,
    LogisticRegression,
    SGDClassifier,
    RidgeClassifier,
    Perceptron,
    SGDRegressor,
    LinearRegression,
    Ridge,
    Lasso,
)
from sklearn.ensemble import (
    RandomForestClassifier,
    RandomForestRegressor,
    ExtraTreesRegressor,
    ExtraTreesClassifier,
)

from sklearn.metrics import mean_squared_error

from itertools import product

import pandas as pd

from sklearn.metrics import (
    confusion_matrix,
    r2_score,
    mean_squared_error,
    mean_absolute_error,
    accuracy_score,
    plot_roc_curve,
    make_scorer,
)
from sklearn.model_selection import (
    train_test_split,
    StratifiedKFold,
    KFold,
    GridSearchCV,
    cross_val_score,
    learning_curve,
)

from sklearn.datasets import make_classification

from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, classification_report, matthews_corrcoef
from sklearn import preprocessing
from sklearn.utils import resample
from imblearn.ensemble import BalancedBaggingClassifier, BalancedRandomForestClassifier
from imblearn.metrics import geometric_mean_score as gms
from sklearn.neural_network import MLPClassifier

pd.options.display.max_columns = 100

#######################################################
#################### FUNCIONES ########################
#######################################################


def show_confusion_matrix(y_real, y_pred, n):
    """Muestra matriz de confusión."""
    mat = confusion_matrix(y_real, y_pred)
    mat = 100 * mat.astype("float64") / mat.sum(axis=1)[:, np.newaxis]
    fig, ax = plt.subplots()
    ax.matshow(mat, cmap="Purples")
    ax.set(
        title="Matriz de confusión", xlabel="Etiqueta real", ylabel="Etiqueta predicha",
    )
    ax.set_xticklabels(np.arange(n + 1))
    ax.set_yticklabels(np.arange(n + 1))

    for i in range(n):
        for j in range(n):
            ax.text(
                j,
                i,
                "{:.0f}%".format(mat[i, j]),
                ha="center",
                va="center",
                color="black" if mat[i, j] < 50 else "white",
            )

    plt.show()


def show_preprocess_correlation_matrix(data, prep_data, title=None):
    """Muestra matriz de correlación para datos antes y después del preprocesado."""
    print("Matriz de correlación pre y post procesado (dígitos)")

    fig, axs = plt.subplots(1, 2, figsize=[12.0, 5.8])

    corr_matrix = np.abs(np.corrcoef(data.T))
    im = axs[0].matshow(corr_matrix, cmap="cividis")
    axs[0].title.set_text("Sin preprocesado")

    corr_matrix_post = np.abs(np.corrcoef(prep_data.T))
    axs[1].matshow(corr_matrix_post, cmap="cividis")
    axs[1].title.set_text("Con preprocesado")

    if title is not None:
        fig.suptitle(title)
    fig.colorbar(im, ax=axs.ravel().tolist(), shrink=0.6)
    plt.show()


def plot_learning_curve(
    estimator,
    title,
    X,
    y,
    scoring,
    ylim=None,
    cv=None,
    n_jobs=1,
    train_sizes=np.linspace(0.1, 1.0, 5),
):
    """
    Generate a simple plot of the test and traning learning curve.

    Parameters
    ----------
    estimator : object type that implements the "fit" and "predict" methods
        An object of that type which is cloned for each validation.

    title : string
        Title for the chart.

    X : array-like, shape (n_samples, n_features)
        Training vector, where n_samples is the number of samples and
        n_features is the number of features.

    y : array-like, shape (n_samples) or (n_samples, n_features), optional
        Target relative to X for classification or regression;
        None for unsupervised learning.

    ylim : tuple, shape (ymin, ymax), optional
        Defines minimum and maximum yvalues plotted.

    cv : integer, cross-validation generator, optional
        If an integer is passed, it is the number of folds (defaults to 3).
        Specific cross-validation objects can be passed, see
        sklearn.cross_validation module for the list of possible objects

    n_jobs : integer, optional
        Number of jobs to run in parallel (default 1).
    """
    plt.figure()
    plt.title(title)
    if ylim is not None:
        plt.ylim(*ylim)
    plt.xlabel("Training examples")
    plt.ylabel("Score")
    train_sizes, train_scores, test_scores = learning_curve(
        estimator, X, y, scoring=scoring, cv=cv, n_jobs=n_jobs, train_sizes=train_sizes
    )
    train_scores_mean = np.mean(train_scores, axis=1)
    train_scores_std = np.std(train_scores, axis=1)
    test_scores_mean = np.mean(test_scores, axis=1)
    test_scores_std = np.std(test_scores, axis=1)
    plt.grid()

    plt.fill_between(
        train_sizes,
        train_scores_mean - train_scores_std,
        train_scores_mean + train_scores_std,
        alpha=0.1,
        color="r",
    )
    plt.fill_between(
        train_sizes,
        test_scores_mean - test_scores_std,
        test_scores_mean + test_scores_std,
        alpha=0.1,
        color="g",
    )
    plt.plot(train_sizes, train_scores_mean, "o-", color="r", label="Training score")
    plt.plot(
        train_sizes, test_scores_mean, "o-", color="g", label="Cross-validation score"
    )

    plt.legend(loc="best")
    return plt


def kfold_models(models, X, y, seed, scorer, stratified=True, verbose=True):
    """
    Realiza validación cruzada con el método K-fold a todos los modelos
    en "models" y devuelve el mejor de ellos.
    Argumentos:
    - models: Vector de modelos de la forma ("nombre", modelo).
    - X: Vector de datos sobre el que hacer K-fold
    - y: Vector de etiquetas.
    - seed: semilla a utilizar.
    - scorer: Funcion de score a utilizar
    - stratified: Indica si el K-fold utilizado debe mantener la proporcion de clases.
    - verbose: Indica si debe imprimir mensajes por pantalla.
    """

    # Inicializa el mejor valor.
    best_score = -1

    # Imprime modelos considerados
    if verbose:
        print("Los modelos que se van a considerar son: ")
        for (name, _) in models:
            print("\t", name)
        print("\n")

    # Crea objeto K-fold
    if stratified:
        kfold = StratifiedKFold(random_state=seed, shuffle=True)
    else:
        kfold = KFold(random_state=seed, shuffle=True)

    for (name, model) in models:

        if verbose:
            print("--> {} <--".format(name))

        # Calcula la media de los valores obtenidos en la validación cruzada.
        score = np.mean(
            cross_val_score(model, X, y, scoring=scorer, cv=kfold, n_jobs=-1)
        )

        # Almacena el mejor resultado
        if best_score < score:
            best_score = score
            best_model = model

        # Mostramos los resultados
        if verbose:
            print("Score en K-fold: {:.3f}".format(score))
            print("\n")

    if verbose:
        print("\nMejor modelo: ", end="")
        print(best_model)
    return best_model
