"""
strategies/ml_predictor.py
Predictor de ML con XGBoost.
Features: indicadores técnicos + retornos históricos + volatilidad.
Target: sube >2% en los próximos 5 días → clase 1 (BUY), baja >2% → clase -1 (SELL), resto → 0 (HOLD).
"""
import os
import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score, classification_report
from xgboost import XGBClassifier

from config.settings import settings
from config.logger import logger


@dataclass
class MLPrediction:
    ticker: str
    signal: str              # BUY / SELL / HOLD
    probability: float       # confianza del modelo 0-1
    target_return: float     # retorno esperado (aproximado)
    model_accuracy: float
    features_used: int
    trained_at: Optional[str]

    @property
    def is_actionable(self) -> bool:
        return self.signal != "HOLD" and self.probability >= settings.ml_min_confidence


class MLPredictor:
    """
    Modelo XGBoost por ticker.
    - Se entrena con al menos 100 días de datos
    - Features: 30+ indicadores técnicos y estadísticos
    - Reentrenamiento automático configurable
    - Persistencia en disco (joblib)
    """

    def __init__(self):
        self.models: Dict[str, XGBClassifier] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        self.metadata: Dict[str, Dict] = {}
        self.models_dir = settings.models_dir

    # ── Feature Engineering ────────────────────────────────────

    def build_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Construye el feature set completo a partir de OHLCV."""
        df = df.copy()
        close = df["Close"]
        high  = df["High"]
        low   = df["Low"]
        vol   = df["Volume"]

        # ── Retornos ──────────────────────────────────────────
        for n in [1, 2, 3, 5, 10, 20]:
            df[f"ret_{n}d"] = close.pct_change(n)

        # ── Volatilidad ───────────────────────────────────────
        for n in [5, 10, 20]:
            df[f"vol_{n}d"] = close.pct_change().rolling(n).std()

        # ── RSI ───────────────────────────────────────────────
        delta = close.diff()
        gain  = delta.clip(lower=0).rolling(14).mean()
        loss  = (-delta.clip(upper=0)).rolling(14).mean()
        rs    = gain / loss.replace(0, np.nan)
        df["rsi"] = 100 - 100 / (1 + rs)
        df["rsi_change"] = df["rsi"].diff()

        # ── MACD ──────────────────────────────────────────────
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd  = ema12 - ema26
        sig9  = macd.ewm(span=9, adjust=False).mean()
        df["macd"]      = macd
        df["macd_sig"]  = sig9
        df["macd_hist"] = macd - sig9
        df["macd_hist_change"] = df["macd_hist"].diff()

        # ── Bollinger Bands ───────────────────────────────────
        sma20 = close.rolling(20).mean()
        std20 = close.rolling(20).std()
        bb_up = sma20 + 2 * std20
        bb_lo = sma20 - 2 * std20
        df["bb_pct"]   = (close - bb_lo) / (bb_up - bb_lo).replace(0, np.nan)
        df["bb_width"] = (bb_up - bb_lo) / sma20.replace(0, np.nan)

        # ── EMAs y cruces ─────────────────────────────────────
        for span in [10, 20, 50, 100, 200]:
            df[f"ema{span}"] = close.ewm(span=span, adjust=False).mean()
            df[f"dist_ema{span}"] = (close - df[f"ema{span}"]) / df[f"ema{span}"].replace(0, np.nan)

        df["ema_cross_10_20"] = (df["ema10"] > df["ema20"]).astype(int)
        df["ema_cross_20_50"] = (df["ema20"] > df["ema50"]).astype(int)

        # ── Stochastic ────────────────────────────────────────
        l14 = low.rolling(14).min()
        h14 = high.rolling(14).max()
        df["stoch_k"] = 100 * (close - l14) / (h14 - l14).replace(0, np.nan)
        df["stoch_d"] = df["stoch_k"].rolling(3).mean()

        # ── ATR y ADX ─────────────────────────────────────────
        tr = pd.concat([
            high - low,
            (high - close.shift()).abs(),
            (low  - close.shift()).abs(),
        ], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()
        df["atr_pct"] = atr / close.replace(0, np.nan)

        dip = 100 * (high.diff().clip(lower=0) / atr.replace(0, np.nan)).rolling(14).mean()
        dim = 100 * ((-low.diff()).clip(lower=0) / atr.replace(0, np.nan)).rolling(14).mean()
        dx  = 100 * (dip - dim).abs() / (dip + dim).replace(0, np.nan)
        df["adx"]      = dx.rolling(14).mean()
        df["di_plus"]  = dip
        df["di_minus"] = dim

        # ── Volumen ───────────────────────────────────────────
        avg_vol20 = vol.rolling(20).mean()
        df["vol_ratio"]  = vol / avg_vol20.replace(0, np.nan)
        df["vol_trend"]  = avg_vol20.pct_change(5)

        # ── Momentum ──────────────────────────────────────────
        df["momentum_10"] = close / close.shift(10).replace(0, np.nan) - 1
        df["momentum_20"] = close / close.shift(20).replace(0, np.nan) - 1

        # ── Soporte / Resistencia ─────────────────────────────
        df["high_20d"] = high.rolling(20).max()
        df["low_20d"]  = low.rolling(20).min()
        df["dist_high"] = (close - df["high_20d"]) / df["high_20d"].replace(0, np.nan)
        df["dist_low"]  = (close - df["low_20d"])  / df["low_20d"].replace(0, np.nan)

        # Seleccionar solo features numéricas (excluir OHLCV originales)
        feature_cols = [c for c in df.columns if c not in ["Open","High","Low","Close","Volume","Dividends","Stock Splits"]]
        return df[feature_cols]

    def build_target(self, df: pd.DataFrame, forward_days: int = 5, threshold: float = 0.015) -> pd.Series:
        """
        Target:
         1 → precio sube >threshold en forward_days
        -1 → precio baja >threshold
         0 → neutral
        Umbral reducido a 1.5% para más muestras de BUY/SELL.
        """
        future_ret = df["Close"].shift(-forward_days) / df["Close"] - 1
        target = pd.Series(0, index=df.index, dtype=int)
        target[future_ret >  threshold] =  1
        target[future_ret < -threshold] = -1
        return target

    # ── Entrenamiento ─────────────────────────────────────────

    def train(self, df: pd.DataFrame, ticker: str) -> Dict:
        """Entrena/reentrena el modelo para un ticker."""
        if len(df) < 100:
            logger.warning(f"Datos insuficientes para entrenar {ticker}: {len(df)} filas")
            return {}

        logger.info(f"🤖 Entrenando ML para {ticker} ({len(df)} filas)...")

        features_df = self.build_features(df)
        target      = self.build_target(df)

        # Alinear índices y eliminar NaN
        combined = pd.concat([features_df, target.rename("target")], axis=1).dropna()
        combined = combined[:-5]  # Eliminar últimas filas (target futuro no disponible)

        if len(combined) < 60:
            logger.warning(f"Muy pocos datos limpios para {ticker}: {len(combined)}")
            return {}

        X = combined.drop("target", axis=1)
        y = combined["target"]

        # Si solo hay una clase, intentar con umbral más bajo
        if len(y.unique()) < 2:
            logger.warning(f"Solo una clase en {ticker} — intentando con umbral 0.5%")
            target2 = self.build_target(df, threshold=0.005)
            combined2 = pd.concat([features_df, target2.rename("target")], axis=1).dropna()
            combined2 = combined2[:-5]
            if len(combined2) >= 60 and len(combined2["target"].unique()) >= 2:
                combined = combined2
                X = combined.drop("target", axis=1)
                y = combined["target"]
            else:
                logger.warning(f"No se pudo balancear clases para {ticker}")
                return {}

        # Escalar features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Time-series cross validation - fewer splits for smaller datasets
        n_splits = 2 if len(X) < 150 else 3
        tscv = TimeSeriesSplit(n_splits=n_splits)
        accuracies = []

        model = XGBClassifier(
            n_estimators=80,
            max_depth=3,
            learning_rate=0.08,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_weight=3,
            gamma=0.0,
            reg_alpha=0.05,
            reg_lambda=1.0,
            eval_metric="mlogloss",
            random_state=42,
            n_jobs=1,
            verbosity=0,
        )

        for train_idx, val_idx in tscv.split(X_scaled):
            X_tr, X_val = X_scaled[train_idx], X_scaled[val_idx]
            y_tr, y_val = y.iloc[train_idx], y.iloc[val_idx]
            if len(y_tr.unique()) < 2:
                continue
            try:
                model.fit(X_tr, y_tr)
                preds = model.predict(X_val)
                accuracies.append(accuracy_score(y_val, preds))
            except Exception as e:
                logger.warning(f"Error en fold CV: {e}")
                continue

        # Entrenar modelo final con todos los datos
        try:
            if len(y.unique()) < 2:
                logger.warning(f"Solo una clase en dataset final {ticker}")
                return {}
            if not accuracies:
                accuracies = [0.0]
            model.fit(X_scaled, y)
        except Exception as e:
            logger.warning(f"Error en entrenamiento final {ticker}: {e}")
            return {}

        avg_accuracy = np.mean(accuracies)
        logger.info(f"✅ {ticker} — Accuracy CV: {avg_accuracy:.2%} | Features: {X.shape[1]}")

        # Guardar
        self.models[ticker]   = model
        self.scalers[ticker]  = scaler

        meta = {
            "ticker":       ticker,
            "trained_at":   datetime.now().isoformat(),
            "accuracy":     round(float(avg_accuracy), 4),
            "n_samples":    len(combined),
            "n_features":   X.shape[1],
            "feature_names": list(X.columns),
            "class_distribution": y.value_counts().to_dict(),
        }
        self.metadata[ticker] = meta
        self._save_model(ticker, model, scaler, meta)

        return meta

    # ── Predicción ────────────────────────────────────────────

    def predict(self, df: pd.DataFrame, ticker: str) -> MLPrediction:
        """Genera predicción para el estado actual del mercado."""
        # Cargar modelo si no está en memoria
        if ticker not in self.models:
            loaded = self._load_model(ticker)
            if not loaded:
                # Entrenar on-the-fly
                meta = self.train(df, ticker)
                if not meta:
                    return self._default_prediction(ticker)

        model  = self.models.get(ticker)
        scaler = self.scalers.get(ticker)
        meta   = self.metadata.get(ticker, {})

        if model is None or scaler is None:
            return self._default_prediction(ticker)

        features_df = self.build_features(df)
        last_features = features_df.iloc[[-1]].dropna(axis=1)

        # Asegurar que las columnas coincidan con las del entrenamiento
        trained_features = meta.get("feature_names", [])
        if trained_features:
            # Usar solo las columnas disponibles en ambos
            common_cols = [c for c in trained_features if c in last_features.columns]
            if len(common_cols) < len(trained_features) * 0.8:
                # Muy pocas features en común, reentrenar
                meta = self.train(df, ticker)
                if not meta:
                    return self._default_prediction(ticker)
                model  = self.models[ticker]
                scaler = self.scalers[ticker]
                common_cols = [c for c in meta.get("feature_names", []) if c in last_features.columns]

            last_features = last_features.reindex(columns=trained_features, fill_value=0)

        try:
            X = scaler.transform(last_features.values)
            pred_class  = model.predict(X)[0]
            pred_proba  = model.predict_proba(X)[0]

            # Mapa clase → señal
            classes = model.classes_
            class_map = {-1: "SELL", 0: "HOLD", 1: "BUY"}
            signal = class_map.get(int(pred_class), "HOLD")

            # Confianza: probabilidad de la clase predicha
            prob_idx = list(classes).index(pred_class)
            confidence = float(pred_proba[prob_idx])

            # Retorno esperado aproximado
            target_ret = 0.02 if signal == "BUY" else (-0.02 if signal == "SELL" else 0.0)

            return MLPrediction(
                ticker=ticker,
                signal=signal,
                probability=round(confidence, 4),
                target_return=target_ret,
                model_accuracy=meta.get("accuracy", 0.0),
                features_used=meta.get("n_features", 0),
                trained_at=meta.get("trained_at"),
            )

        except Exception as e:
            logger.error(f"Error predicción ML {ticker}: {e}")
            return self._default_prediction(ticker)

    def _default_prediction(self, ticker: str) -> MLPrediction:
        return MLPrediction(
            ticker=ticker, signal="HOLD", probability=0.0,
            target_return=0.0, model_accuracy=0.0, features_used=0, trained_at=None,
        )

    # ── Persistencia ──────────────────────────────────────────

    def _save_model(self, ticker: str, model, scaler, meta: Dict):
        try:
            safe_name = ticker.replace(".", "_")
            joblib.dump(model,  self.models_dir / f"{safe_name}_model.pkl")
            joblib.dump(scaler, self.models_dir / f"{safe_name}_scaler.pkl")
            with open(self.models_dir / f"{safe_name}_meta.json", "w") as f:
                json.dump(meta, f, indent=2, default=str)
            logger.debug(f"💾 Modelo guardado: {ticker}")
        except Exception as e:
            logger.error(f"Error guardando modelo {ticker}: {e}")

    def _load_model(self, ticker: str) -> bool:
        try:
            safe_name = ticker.replace(".", "_")
            model_path  = self.models_dir / f"{safe_name}_model.pkl"
            scaler_path = self.models_dir / f"{safe_name}_scaler.pkl"
            meta_path   = self.models_dir / f"{safe_name}_meta.json"

            if not model_path.exists():
                return False

            self.models[ticker]  = joblib.load(model_path)
            self.scalers[ticker] = joblib.load(scaler_path)

            if meta_path.exists():
                with open(meta_path) as f:
                    self.metadata[ticker] = json.load(f)

            logger.debug(f"📂 Modelo cargado: {ticker}")
            return True

        except Exception as e:
            logger.warning(f"No se pudo cargar modelo {ticker}: {e}")
            return False

    def needs_retraining(self, ticker: str) -> bool:
        """¿El modelo necesita ser reentrenado?"""
        meta = self.metadata.get(ticker)
        if not meta:
            return True

        trained_at = datetime.fromisoformat(meta["trained_at"])
        hours_since = (datetime.now() - trained_at).total_seconds() / 3600
        return hours_since >= settings.ml_retrain_interval_hours


# Instancia global
ml_predictor = MLPredictor()
