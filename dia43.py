"""
DÍA 43: LSTM — Redes Neuronales para Series Temporales
=======================================================
Bootcamp Quant Trading - Irene Tanarro

Modelo: LSTM (Long Short-Term Memory) con PyTorch
Target: ¿Sube AAPL mañana? (1 = sí, 0 = no)
Diferencia: LSTM mira secuencias de 10 días, no días individuales

Requisitos: pip install torch scikit-learn xgboost yfinance pandas numpy
"""

import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
import warnings
warnings.filterwarnings("ignore")

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

torch.manual_seed(42)
np.random.seed(42)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ============================================================
# PARTE 1: DATOS Y FEATURES
# ============================================================

print("=" * 60)
print("  🧠 DÍA 43: LSTM CON PYTORCH")
print("  📊 Predicción de AAPL con secuencias temporales")
print("=" * 60)

print(f"\n   🔧 Usando: {device}")
print("\n📥 Descargando datos...")

ticker = "AAPL"
data = yf.download(ticker, start="2020-01-01", end="2025-12-31", progress=False)

if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.get_level_values(0)

df = data.copy()

# Features (mismo feature engineering que Días 41-42)
df["return_1d"] = df["Close"].pct_change(1)
df["return_5d"] = df["Close"].pct_change(5)
df["return_10d"] = df["Close"].pct_change(10)
df["return_20d"] = df["Close"].pct_change(20)

df["MA5"] = df["Close"].rolling(5).mean()
df["MA10"] = df["Close"].rolling(10).mean()
df["MA20"] = df["Close"].rolling(20).mean()
df["MA50"] = df["Close"].rolling(50).mean()

df["precio_vs_MA5"] = df["Close"] / df["MA5"]
df["precio_vs_MA10"] = df["Close"] / df["MA10"]
df["precio_vs_MA20"] = df["Close"] / df["MA20"]
df["precio_vs_MA50"] = df["Close"] / df["MA50"]

df["volatilidad_5d"] = df["return_1d"].rolling(5).std()
df["volatilidad_10d"] = df["return_1d"].rolling(10).std()
df["volatilidad_20d"] = df["return_1d"].rolling(20).std()

delta = df["Close"].diff()
gain = delta.where(delta > 0, 0).rolling(14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
rs = gain / loss
df["RSI"] = 100 - (100 / (1 + rs))

ema12 = df["Close"].ewm(span=12).mean()
ema26 = df["Close"].ewm(span=26).mean()
df["MACD"] = ema12 - ema26
df["MACD_signal"] = df["MACD"].ewm(span=9).mean()
df["MACD_hist"] = df["MACD"] - df["MACD_signal"]

df["volumen_vs_media"] = df["Volume"] / df["Volume"].rolling(20).mean()
df["rango_diario"] = (df["High"] - df["Low"]) / df["Close"]
df["gap_apertura"] = (df["Open"] - df["Close"].shift(1)) / df["Close"].shift(1)
df["pos_rango_20d"] = (df["Close"] - df["Low"].rolling(20).min()) / \
                       (df["High"].rolling(20).max() - df["Low"].rolling(20).min())
df["dia_semana"] = df.index.dayofweek

# Target
df["target"] = (df["Close"].shift(-1) > df["Close"]).astype(int)

features = [
    "return_1d", "return_5d", "return_10d", "return_20d",
    "precio_vs_MA5", "precio_vs_MA10", "precio_vs_MA20", "precio_vs_MA50",
    "volatilidad_5d", "volatilidad_10d", "volatilidad_20d",
    "RSI", "MACD", "MACD_signal", "MACD_hist",
    "volumen_vs_media", "rango_diario", "gap_apertura",
    "pos_rango_20d", "dia_semana"
]

df_clean = df.dropna(subset=features + ["target"]).copy()
print(f"   ✅ {len(df_clean)} filas listas con {len(features)} features")


# ============================================================
# PARTE 2: PREPARAR DATOS PARA LSTM
# ============================================================

print("\n📦 Preparando datos para LSTM...")

VENTANA = 10  # Secuencia de 10 días

# Split temporal 80/20
split_index = int(len(df_clean) * 0.8)

# Normalizar features
scaler = StandardScaler()
df_features = df_clean[features].copy()
scaler.fit(df_features.iloc[:split_index])
df_scaled = pd.DataFrame(
    scaler.transform(df_features),
    index=df_features.index,
    columns=features
)

# Crear secuencias de 10 días
def crear_secuencias(datos_x, datos_y, ventana):
    X, y = [], []
    for i in range(ventana, len(datos_x)):
        X.append(datos_x[i - ventana:i])
        y.append(datos_y[i])
    return np.array(X), np.array(y)

datos_x = df_scaled.values
datos_y = df_clean["target"].values

X_all, y_all = crear_secuencias(datos_x, datos_y, VENTANA)

# Split
split_seq = split_index - VENTANA
X_train_np = X_all[:split_seq]
y_train_np = y_all[:split_seq]
X_test_np = X_all[split_seq:]
y_test_np = y_all[split_seq:]

# Convertir a tensores PyTorch
X_train_t = torch.FloatTensor(X_train_np).to(device)
y_train_t = torch.FloatTensor(y_train_np).to(device)
X_test_t = torch.FloatTensor(X_test_np).to(device)
y_test_t = torch.FloatTensor(y_test_np).to(device)

# DataLoader para entrenar en batches
train_dataset = TensorDataset(X_train_t, y_train_t)
train_loader = DataLoader(train_dataset, batch_size=32, shuffle=False)

print(f"   📐 Forma de datos LSTM: ({X_train_np.shape[0]}, {X_train_np.shape[1]}, {X_train_np.shape[2]})")
print(f"      → {X_train_np.shape[0]} muestras")
print(f"      → {X_train_np.shape[1]} días por secuencia")
print(f"      → {X_train_np.shape[2]} features por día")
print(f"   📚 Train: {len(X_train_np)} secuencias")
print(f"   🧪 Test:  {len(X_test_np)} secuencias")

# Datos planos para RF y XGBoost
train_flat = df_clean.iloc[:split_index]
test_flat = df_clean.iloc[split_index:]
X_train_flat = train_flat[features]
y_train_flat = train_flat["target"]
X_test_flat = test_flat[features]
y_test_flat = test_flat["target"]


# ============================================================
# PARTE 3: DEFINIR Y ENTRENAR LSTM
# ============================================================

print("\n🧠 Construyendo red neuronal LSTM...")


class LSTMModel(nn.Module):
    def __init__(self, input_size, hidden1=50, hidden2=30):
        super().__init__()
        self.lstm1 = nn.LSTM(input_size, hidden1, batch_first=True)
        self.dropout1 = nn.Dropout(0.2)
        self.lstm2 = nn.LSTM(hidden1, hidden2, batch_first=True)
        self.dropout2 = nn.Dropout(0.2)
        self.fc1 = nn.Linear(hidden2, 16)
        self.relu = nn.ReLU()
        self.dropout3 = nn.Dropout(0.1)
        self.fc2 = nn.Linear(16, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        out, _ = self.lstm1(x)
        out = self.dropout1(out)
        out, _ = self.lstm2(out)
        out = self.dropout2(out[:, -1, :])  # Solo último paso temporal
        out = self.relu(self.fc1(out))
        out = self.dropout3(out)
        out = self.sigmoid(self.fc2(out))
        return out.squeeze()


modelo_lstm = LSTMModel(input_size=len(features)).to(device)
criterion = nn.BCELoss()
optimizer = torch.optim.Adam(modelo_lstm.parameters(), lr=0.001)

# Arquitectura
total_params = sum(p.numel() for p in modelo_lstm.parameters())
print(f"   📋 Parámetros totales: {total_params:,}")
print(f"   📋 Capas: LSTM(50) → Dropout → LSTM(30) → Dropout → Dense(16) → Dense(1)")

# Entrenar
print("\n⏳ Entrenando LSTM...")

EPOCHS = 50
mejor_val_loss = float("inf")
paciencia = 5
contador_paciencia = 0
mejor_estado = None

# Separar validación (15% de train)
val_size = int(len(X_train_t) * 0.15)
X_val_t = X_train_t[-val_size:]
y_val_t = y_train_t[-val_size:]
X_train_real = X_train_t[:-val_size]
y_train_real = y_train_t[:-val_size]

train_real_dataset = TensorDataset(X_train_real, y_train_real)
train_real_loader = DataLoader(train_real_dataset, batch_size=32, shuffle=False)

for epoch in range(EPOCHS):
    # Entrenar
    modelo_lstm.train()
    train_loss = 0
    for batch_X, batch_y in train_real_loader:
        optimizer.zero_grad()
        pred = modelo_lstm(batch_X)
        loss = criterion(pred, batch_y)
        loss.backward()
        optimizer.step()
        train_loss += loss.item()

    train_loss /= len(train_real_loader)

    # Validar
    modelo_lstm.eval()
    with torch.no_grad():
        val_pred = modelo_lstm(X_val_t)
        val_loss = criterion(val_pred, y_val_t).item()

    # Early stopping
    if val_loss < mejor_val_loss:
        mejor_val_loss = val_loss
        contador_paciencia = 0
        mejor_estado = modelo_lstm.state_dict().copy()
    else:
        contador_paciencia += 1

    if (epoch + 1) % 5 == 0:
        print(f"   Epoch {epoch+1:>3}/{EPOCHS} — Train Loss: {train_loss:.4f} — Val Loss: {val_loss:.4f}")

    if contador_paciencia >= paciencia:
        print(f"\n   ⏹️ Early stopping en epoch {epoch+1}")
        break

# Cargar mejor modelo
if mejor_estado is not None:
    modelo_lstm.load_state_dict(mejor_estado)

print(f"   ✅ LSTM entrenado ({epoch+1} epochs)")


# ============================================================
# PARTE 4: EVALUAR LSTM
# ============================================================

print("\n📊 EVALUACIÓN DE LSTM")
print("=" * 50)

modelo_lstm.eval()
with torch.no_grad():
    lstm_prob_train = modelo_lstm(X_train_t).cpu().numpy()
    lstm_prob_test = modelo_lstm(X_test_t).cpu().numpy()

lstm_pred_train = (lstm_prob_train > 0.5).astype(int)
lstm_pred_test = (lstm_prob_test > 0.5).astype(int)

lstm_acc_train = accuracy_score(y_train_np, lstm_pred_train)
lstm_acc_test = accuracy_score(y_test_np, lstm_pred_test)
lstm_prec = precision_score(y_test_np, lstm_pred_test, zero_division=0)
lstm_rec = recall_score(y_test_np, lstm_pred_test, zero_division=0)
lstm_f1 = f1_score(y_test_np, lstm_pred_test, zero_division=0)

print(f"\n   🧠 LSTM:")
print(f"      Accuracy Train: {lstm_acc_train:.4f} ({lstm_acc_train*100:.2f}%)")
print(f"      Accuracy Test:  {lstm_acc_test:.4f} ({lstm_acc_test*100:.2f}%)")
print(f"      Overfitting:    {lstm_acc_train - lstm_acc_test:.4f}")
print(f"      Precision:      {lstm_prec:.4f}")
print(f"      Recall:         {lstm_rec:.4f}")
print(f"      F1 Score:       {lstm_f1:.4f}")


# ============================================================
# PARTE 5: ENTRENAR RF Y XGBOOST (referencia)
# ============================================================

print("\n🌲 Entrenando Random Forest...")
rf = RandomForestClassifier(
    n_estimators=200, max_depth=5, min_samples_split=20,
    min_samples_leaf=10, random_state=42, n_jobs=-1
)
rf.fit(X_train_flat, y_train_flat)
rf_pred_test = rf.predict(X_test_flat)

print("🚀 Entrenando XGBoost Optimizado...")
xgb = XGBClassifier(
    n_estimators=100, max_depth=2, learning_rate=0.05,
    subsample=0.7, colsample_bytree=0.7, reg_alpha=1.0,
    reg_lambda=2.0, min_child_weight=10, gamma=0.1,
    random_state=42, eval_metric="logloss", verbosity=0
)
xgb.fit(X_train_flat, y_train_flat)
xgb_pred_test = xgb.predict(X_test_flat)

rf_acc_test = accuracy_score(y_test_flat, rf_pred_test)
xgb_acc_test = accuracy_score(y_test_flat, xgb_pred_test)
rf_prec = precision_score(y_test_flat, rf_pred_test, zero_division=0)
xgb_prec = precision_score(y_test_flat, xgb_pred_test, zero_division=0)
rf_f1 = f1_score(y_test_flat, rf_pred_test, zero_division=0)
xgb_f1 = f1_score(y_test_flat, xgb_pred_test, zero_division=0)


# ============================================================
# PARTE 6: COMPARACIÓN — 3 MODELOS
# ============================================================

print("\n" + "=" * 60)
print("  📊 COMPARACIÓN: RF vs XGBOOST vs LSTM")
print("=" * 60)

baseline = y_test_flat.mean()

print(f"\n   {'Métrica':<22} {'RF':>10} {'XGBoost':>10} {'LSTM':>10}")
print(f"   {'------':<22} {'--':>10} {'-------':>10} {'----':>10}")
print(f"   {'Accuracy Test':<22} {rf_acc_test:>10.4f} {xgb_acc_test:>10.4f} {lstm_acc_test:>10.4f}")
print(f"   {'Precision':<22} {rf_prec:>10.4f} {xgb_prec:>10.4f} {lstm_prec:>10.4f}")
print(f"   {'F1 Score':<22} {rf_f1:>10.4f} {xgb_f1:>10.4f} {lstm_f1:>10.4f}")
print(f"   {'Baseline':<22} {baseline:>10.4f} {baseline:>10.4f} {baseline:>10.4f}")

modelos_acc = {"Random Forest": rf_acc_test, "XGBoost": xgb_acc_test, "LSTM": lstm_acc_test}
mejor_acc = max(modelos_acc, key=modelos_acc.get)
print(f"\n   🏆 Mejor por Accuracy: {mejor_acc} ({modelos_acc[mejor_acc]*100:.2f}%)")


# ============================================================
# PARTE 7: SIMULACIÓN DE TRADING — 3 MODELOS
# ============================================================

print("\n" + "=" * 60)
print("  💰 SIMULACIÓN DE TRADING — 3 MODELOS")
print("=" * 60)

n_lstm = len(lstm_pred_test)
n_flat = len(rf_pred_test)
offset = n_flat - n_lstm

sim = test_flat.iloc[offset:].copy()
sim["pred_rf"] = rf_pred_test[offset:]
sim["pred_xgb"] = xgb_pred_test[offset:]
sim["pred_lstm"] = lstm_pred_test

retorno_futuro = sim["return_1d"].shift(-1)

sim["ret_rf"] = retorno_futuro * sim["pred_rf"]
sim["ret_xgb"] = retorno_futuro * sim["pred_xgb"]
sim["ret_lstm"] = retorno_futuro * sim["pred_lstm"]
sim["ret_bh"] = retorno_futuro

sim["acum_rf"] = (1 + sim["ret_rf"]).cumprod()
sim["acum_xgb"] = (1 + sim["ret_xgb"]).cumprod()
sim["acum_lstm"] = (1 + sim["ret_lstm"]).cumprod()
sim["acum_bh"] = (1 + sim["ret_bh"]).cumprod()

ret_rf = (sim["acum_rf"].iloc[-2] - 1) * 100
ret_xgb = (sim["acum_xgb"].iloc[-2] - 1) * 100
ret_lstm = (sim["acum_lstm"].iloc[-2] - 1) * 100
ret_bh = (sim["acum_bh"].iloc[-2] - 1) * 100

print(f"\n   📊 Rendimiento en período de TEST:")
print(f"      🌲 Random Forest:      {ret_rf:>+8.2f}%")
print(f"      🚀 XGBoost Optimizado: {ret_xgb:>+8.2f}%")
print(f"      🧠 LSTM:               {ret_lstm:>+8.2f}%")
print(f"      📈 Buy & Hold:         {ret_bh:>+8.2f}%")

print(f"\n   📐 Sharpe Ratios:")
for nombre, col in [("RF", "ret_rf"), ("XGBoost", "ret_xgb"),
                     ("LSTM", "ret_lstm"), ("B&H", "ret_bh")]:
    rets = sim[col].dropna()
    if rets.std() > 0:
        sharpe = (rets.mean() / rets.std()) * np.sqrt(252)
        print(f"      {nombre:<12}: {sharpe:.4f}")

print(f"\n   📅 Días invertido:")
total = len(sim)
print(f"      🌲 RF:      {sim['pred_rf'].sum():.0f} de {total} ({sim['pred_rf'].mean()*100:.1f}%)")
print(f"      🚀 XGBoost: {sim['pred_xgb'].sum():.0f} de {total} ({sim['pred_xgb'].mean()*100:.1f}%)")
print(f"      🧠 LSTM:    {sim['pred_lstm'].sum():.0f} de {total} ({sim['pred_lstm'].mean()*100:.1f}%)")

resultados = {"Random Forest": ret_rf, "XGBoost": ret_xgb, "LSTM": ret_lstm}
mejor_ret = max(resultados, key=resultados.get)
print(f"\n   🏆 Mejor por retorno: {mejor_ret} ({resultados[mejor_ret]:+.2f}%)")

supera_bh = {k: v for k, v in resultados.items() if v > ret_bh}
if supera_bh:
    print(f"   ✅ Superan a Buy & Hold: {', '.join(supera_bh.keys())}")
else:
    print(f"   ⚠️ Ningún modelo superó a Buy & Hold ({ret_bh:+.2f}%)")


# ============================================================
# PARTE 8: PREDICCIÓN PARA MAÑANA — CONSENSO
# ============================================================

print("\n" + "=" * 60)
print("  🔮 PREDICCIÓN PARA MAÑANA — CONSENSO 3 MODELOS")
print("=" * 60)

fecha_ultimo = df_clean.index[-1].strftime("%Y-%m-%d")
print(f"\n   📅 Basado en datos del: {fecha_ultimo}\n")

# RF y XGBoost
ultimo_flat = df_clean[features].iloc[-1:]
rf_pred_hoy = rf.predict(ultimo_flat)[0]
rf_prob = rf.predict_proba(ultimo_flat)[0]
xgb_pred_hoy = xgb.predict(ultimo_flat)[0]
xgb_prob = xgb.predict_proba(ultimo_flat)[0]

# LSTM (secuencia de 10 días)
ultimos_10 = df_scaled.iloc[-VENTANA:].values
ultimo_seq = torch.FloatTensor(ultimos_10).unsqueeze(0).to(device)

modelo_lstm.eval()
with torch.no_grad():
    lstm_prob_single = modelo_lstm(ultimo_seq).cpu().item()

lstm_pred_hoy = 1 if lstm_prob_single > 0.5 else 0

votos_sube = 0
votos_baja = 0

# RF
dir_rf = "SUBE" if rf_pred_hoy == 1 else "BAJA"
emoji_rf = "📈" if rf_pred_hoy == 1 else "📉"
votos_sube += rf_pred_hoy
votos_baja += (1 - rf_pred_hoy)
print(f"   🌲 Random Forest:      {emoji_rf} {dir_rf} (confianza: {max(rf_prob)*100:.1f}%)")

# XGBoost
dir_xgb = "SUBE" if xgb_pred_hoy == 1 else "BAJA"
emoji_xgb = "📈" if xgb_pred_hoy == 1 else "📉"
votos_sube += xgb_pred_hoy
votos_baja += (1 - xgb_pred_hoy)
print(f"   🚀 XGBoost Optimizado: {emoji_xgb} {dir_xgb} (confianza: {max(xgb_prob)*100:.1f}%)")

# LSTM
dir_lstm = "SUBE" if lstm_pred_hoy == 1 else "BAJA"
emoji_lstm = "📈" if lstm_pred_hoy == 1 else "📉"
conf_lstm = lstm_prob_single if lstm_pred_hoy == 1 else (1 - lstm_prob_single)
votos_sube += lstm_pred_hoy
votos_baja += (1 - lstm_pred_hoy)
print(f"   🧠 LSTM:               {emoji_lstm} {dir_lstm} (confianza: {conf_lstm*100:.1f}%)")

# Consenso
print(f"\n   📊 CONSENSO:")
print(f"      Votos SUBE: {votos_sube}")
print(f"      Votos BAJA: {votos_baja}")

if votos_sube > votos_baja:
    print(f"      ✅ Señal: COMPRAR (mayoría predice subida)")
elif votos_baja > votos_sube:
    print(f"      🔴 Señal: NO COMPRAR (mayoría predice bajada)")
else:
    print(f"      ⏸️ Señal: EMPATE — mejor esperar")


# ============================================================
# PARTE 9: RESUMEN
# ============================================================

print("\n" + "=" * 60)
print("  ✅ DÍA 43 COMPLETADO")
print("=" * 60)
