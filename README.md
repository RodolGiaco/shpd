# SHPD — Posture Recognition ML Training 

![Python](https://img.shields.io/badge/Python-3.8%20%7C%203.12-3776AB?logo=python&logoColor=white)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.5-FF6F00?logo=tensorflow&logoColor=white)
![MediaPipe](https://img.shields.io/badge/MediaPipe-0097A7?logo=google&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-4.5-5C3EE8?logo=opencv&logoColor=white)
![Raspberry Pi](https://img.shields.io/badge/Raspberry_Pi_3-A22846?logo=raspberrypi&logoColor=white)

Entrenamiento y validación de un modelo de reconocimiento de posturas corporales en tiempo real. Usa **MediaPipe** para extraer puntos clave del cuerpo desde una cámara, una **red neuronal (TensorFlow/Keras)** para clasificar esos puntos en una postura conocida, y exporta el modelo entrenado a **TensorFlow Lite** para que corra en una **Raspberry Pi 3** con recursos limitados.

> Proyecto desarrollado en el marco de la carrera de Ingeniería en Electrónica (Universidad Tecnológica Nacional — Facultad Regional Mendoza).

Este documento explica, de punta a punta, **cómo se agregan posturas nuevas, cómo se entrena el modelo y cómo se exporta a la Raspberry Pi**, con los comandos exactos para repetir el proceso.

### Alcance de este repositorio

Este repositorio **no es el producto final**. Es el banco de pruebas para entrenar el modelo de reconocimiento de posturas y validarlo corriendo en la Raspberry Pi: la GUI que incluye (`gui/`, `main_pc.py`, `main_rpi.py`) muestra la cámara en vivo y la postura detectada únicamente para **confirmar manualmente, a ojo, que el modelo reconoce bien cada postura** — no está pensada como interfaz de usuario final.

Todo lo que forma el producto terminado — interfaz para el cliente, bot, frontend, sistema de alertas — vive en **otro repositorio**, que consume el `.tflite` que se entrena y valida acá.

---

## 1. El flujo completo, en una imagen

```
 ┌──────────────┐     ┌───────────────────┐     ┌────────────────────┐     ┌──────────────────┐
 │   Cámara PC  │ --> │  MediaPipe (PC)   │ --> │  new_pose_data.csv │ --> │  Entrenamiento    │
 │ add_pose.py  │     │  12 puntos x,y,z  │     │  (dataset)         │     │  (TensorFlow)     │
 └──────────────┘     └───────────────────┘     └────────────────────┘     └─────────┬─────────┘
                                                                                        │
                                                                                        v
 ┌──────────────────┐     ┌────────────────────────┐     ┌───────────────────────────────────┐
 │  Raspberry Pi 3   │ <-- │  keypoint_classifier   │ <-- │  Conversión a TensorFlow Lite      │
 │  main_rpi.py      │ scp │  .tflite + labels.csv  │     │  (quantization)                    │
 └──────────────────┘     └────────────────────────┘     └───────────────────────────────────┘
```

Cada postura queda representada por **12 puntos del torso y las extremidades** (hombros, codos, muñecas, caderas, rodillas, tobillos — índices 11-16 y 23-28 de MediaPipe Pose), normalizados a coordenadas relativas. El modelo nunca ve la imagen: sólo estos 36 números (12 puntos × x,y,z) por muestra.

---

## 2. Tecnologías usadas

| Etapa | Tecnología |
|---|---|
| Detección de pose (recolección de datos, PC) | MediaPipe Tasks API (`PoseLandmarker`) |
| Detección de pose (inferencia en tiempo real) | MediaPipe Solutions API clásica (`mp.solutions.pose`) — la única que compila para ARMv7 |
| Entrenamiento del clasificador | TensorFlow / Keras (red densa: 32 → 32 → 16 → N clases) |
| Modelo final embebido | TensorFlow Lite (cuantizado) |
| Inferencia en la Raspberry Pi | `tflite_runtime` (no TensorFlow completo — es demasiado pesado para ARMv7) |
| Captura de cámara / GUI | OpenCV |
| Hardware de destino | Raspberry Pi 3 Model B+ (ARMv7, 32-bit) |

**Por qué dos APIs de MediaPipe distintas:** la API nueva (`Tasks`, usada por `add_pose.py`) es más cómoda para recolectar datos en la PC, pero MediaPipe no la compila para ARMv7. Por eso la app que corre en la Raspberry Pi (`main_rpi.py`) usa la API clásica (`Solutions`), disponible en el MediaPipe 0.8.8 compilado a mano para la Pi. Esto no afecta al dataset: en ambos casos se extraen los mismos 12 puntos con el mismo significado.

---

## 3. Los entornos de Python — versiones exactas

Este proyecto usa **dos entornos en la PC** (uno para recolectar datos, otro para entrenar) y un **tercero en la Raspberry Pi** para correr el sistema. Cada uno tiene un propósito específico y no deben mezclarse.

### 3.1 `shpd` — recolección de datos (PC)

Corre `add_pose.py`: abre la cámara, detecta la pose con la Tasks API de MediaPipe y agrega filas a `model/new_pose_data.csv`.

```bash
python3 -m venv shpd
source shpd/bin/activate

pip install -r requirements-shpd.txt
```

- **Python:** 3.12
- **Paquetes que necesita este proyecto** — fijados en [`requirements-shpd.txt`](requirements-shpd.txt): únicamente `opencv-python`, `mediapipe` y `numpy`.

> ℹ️ `shpd` sólo alcanza para correr `add_pose.py` (recolección de datos). Si además querés probar `main_pc.py`, hace falta también `tensorflow` instalado en el mismo entorno — `neural_network/pose_recognition.py` intenta usar `tflite_runtime` primero (lo que corre en la Raspberry Pi) y si no está disponible cae automáticamente a `tensorflow.lite.Interpreter`, sin que haga falta tocar nada a mano.

### 3.2 `tf25env` — entrenamiento del modelo (PC)

Corre la notebook `model/Keypoint_model_training.ipynb`. Usa **TensorFlow 2.5.0** a propósito: es la misma versión que corre como `tflite_runtime 2.5.0` en la Raspberry Pi, así el `.tflite` que se genera es garantizado compatible.

```bash
python3.8 -m venv tf25env
source tf25env/bin/activate

pip install -r requirements-tf25env.txt
```

- **Python:** 3.8 (si tu sistema no lo tiene: `sudo apt install python3.8 python3.8-venv`)
- **No necesita** OpenCV ni MediaPipe — la notebook entrena solamente a partir del CSV de números, nunca toca la cámara.
- Versiones completas fijadas en [`requirements-tf25env.txt`](requirements-tf25env.txt) (pip freeze exacto del entorno usado para entrenar y verificar el modelo actual).

### 3.3 Entorno de la Raspberry Pi (en el dispositivo, no en este repo)

Corre `main_rpi.py`. Se arma compilando OpenCV y MediaPipe desde fuente para ARMv7 — procedimiento completo en [`docs/RASPBERRY_PI.md`](docs/RASPBERRY_PI.md) y automatizado en [`install_rpi.sh`](install_rpi.sh).

```
opencv-python == 4.5.5.64      (compilado desde fuente)
mediapipe == 0.8.8             (compilado desde fuente, API Solutions)
numpy == 1.22.0
tflite-runtime == 2.5.0        (wheel manual para ARMv7 — ver requirements-rpi.txt)
```

- **Python:** 3.7 (el que trae Raspberry Pi OS Buster de fábrica — ver `RASPBERRY_PI.md`)
- **Venv en la Pi:** `pose_env`

---

## 4. Procedimiento completo, paso a paso

### Paso 1 — Recolectar posturas nuevas

```bash
source shpd/bin/activate       # o la ruta completa a tu venv shpd
cd shpd-edge-vision # raíz del repo

python3 model/add_pose.py
```

Controles durante la captura:

| Tecla | Acción |
|---|---|
| `ESPACIO` | Guarda la pose actual con la clase activa |
| `n` | Pasa a la siguiente clase de postura |
| `p` | Vuelve a la clase anterior |
| `q` | Sale y valida el CSV generado |

Esto agrega filas a `model/new_pose_data.csv` con el formato `[clase, x1,y1,z1, ..., x12,y12,z12]` (37 columnas).

**Para agregar una postura completamente nueva:**
1. Sumá su nombre como una línea nueva en `model/keypoint_classifier_label.csv`, respetando el orden de los IDs de clase.
2. Actualizá `NUM_CLASSES` en la primera celda de configuración de la notebook (paso 2).

### Paso 2 — Entrenar el modelo

```bash
source tf25env/bin/activate
cd model

jupyter notebook Keypoint_model_training.ipynb
```

Corré las celdas en orden. En resumen, la notebook:

1. Lee `new_pose_data.csv` y separa 75% entrenamiento / 25% test.
2. Define una red densa: `Input(36) → Dense(32) → Dense(32) → Dense(16) → Dense(N_CLASES, softmax)`.
3. Entrena hasta 1000 épocas con `EarlyStopping(patience=50)` y guarda sólo el mejor checkpoint (`ModelCheckpoint`) en `model/keypoint_classifier.keras`.
4. Evalúa con matriz de confusión y `classification_report`.
5. Convierte el modelo a TFLite cuantizado y lo guarda en `model/keypoint_classifier.tflite`.
6. Verifica que la inferencia del `.tflite` coincida con la del modelo Keras original.

**Referencia de la última corrida verificada** (12 clases, 5.142 muestras): entrenamiento cortado por early stopping en la época 219, **accuracy de validación 99.92%**, un único error de clasificación entre "Rodillas elevadas o muy bajas" y "Elevación escapular" sobre 1.286 muestras de test. Sirve como referencia de qué tan bien debería comportarse un reentrenamiento con datos similares.

La sección final de la notebook ("Hyperparameters Tuning") es **opcional** — hace una búsqueda de arquitecturas con TensorBoard y no es necesaria para producir el modelo. La propia notebook borra sus logs al terminar (`!rm -rf logs`); no deberían commitearse si se vuelve a correr.

#### (Opcional) Guardar varias corridas para comparar antes de elegir una

Cada vez que se vuelve a correr la notebook, se pisa `model/keypoint_classifier.tflite` con el resultado nuevo — la notebook no versiona nada por su cuenta. Si vas a entrenar varias variantes (distintos datos, distintos hiperparámetros) antes de decidir cuál mandar a la Raspberry Pi, guardá una copia con un sufijo de versión **antes** de volver a correr el entrenamiento:

```bash
cd model
cp keypoint_classifier.tflite keypoint_classifierV2.tflite   # respaldo de esta corrida
# volvés al paso 2 y entrenás la siguiente variante...
cp keypoint_classifier.tflite keypoint_classifierV3.tflite
```

Así es como terminan existiendo variantes numeradas (`V1`, `V2`, `V3`...): son respaldos manuales de corridas anteriores, no algo generado automáticamente. No hace falta subirlas todas a git — alcanza con la que se termine usando.

#### (Opcional) Probar una variante puntual con el intérprete real de la Pi

`model/test/test.py` prueba que el *conversor* de TensorFlow funcione — arma un modelo descartable, lo convierte a TFLite con las mismas flags que exige TensorFlow 2.5.0, y se corre en `tf25env`, sobre la PC:

```bash
source tf25env/bin/activate
cd model
python3 test/test.py
# -> TF version: 2.5.0
# -> ✅ Modelo convertido correctamente
```

`model/test/interpreter.py` prueba algo distinto y complementario: que el `.tflite` actual cargue con `tflite_runtime`, el intérprete liviano que corre en la Raspberry Pi (no TensorFlow completo). Es la forma más rápida de descartar una variante antes de copiarla a la Pi.

```bash
# en un entorno con tflite_runtime instalado (la propia Raspberry Pi, entorno pose_env)
cd model
python3 test/interpreter.py
# -> Interpreter cargado correctamente ✅
```

> Apunta a `keypoint_classifier.tflite` con ruta relativa — por eso hay que correrlo con `model/` como directorio de trabajo (`cd model && python3 test/interpreter.py`), no parado adentro de `model/test/`.

#### (Opcional) `model/test/` — set de prueba para validar todo el pipeline sin tocar los datos reales

Además de los dos scripts de arriba, `model/test/` tiene un set chico y autocontenido para confirmar que **todo el mecanismo** (entrenar → convertir → cargar) funciona de punta a punta, sin arriesgar el dataset ni el modelo reales:

| Archivo | Qué es |
|---|---|
| `new_pose_data_test.csv` | Dataset de prueba — mismo formato que `model/new_pose_data.csv` (37 columnas), pero con 6 clases genéricas en vez de las 12 posturas reales del proyecto |
| `keypoint_classifier_label_test.csv` | Las 6 etiquetas correspondientes a ese dataset de prueba |
| `keypoint_classifier_test.tflite` | Un modelo ya entrenado y convertido a partir de ese dataset — el resultado esperado si corrés la notebook (Paso 2) apuntando a estos archivos |

Útil para probar la notebook o los dos scripts de arriba contra un dataset chico y conocido antes de tocar `model/new_pose_data.csv` con datos reales — por ejemplo, si estás en una máquina nueva confirmando que `tf25env` quedó bien armado.

### Paso 3 — Exportar el modelo a la Raspberry Pi

```bash
scp model/keypoint_classifier.tflite \
    model/keypoint_classifier_label.csv \
    pi@<ip-de-la-raspberry>:~/shpd-edge-vision/model/
```

### Paso 4 — Verificar que cargue en la Raspberry Pi

```bash
source ~/pose_env/bin/activate
cd ~/shpd-edge-vision

python3 -c "
from tflite_runtime.interpreter import Interpreter
i = Interpreter(model_path='model/keypoint_classifier.tflite')
i.allocate_tensors()
print('Interpreter cargado correctamente ✅')
"
```

### Paso 5 — Probar el reconocimiento con la GUI

Abre la cámara y muestra en una ventana la postura que el modelo va reconociendo en vivo, para confirmar a ojo que clasifica bien — es una herramienta de validación manual, no una interfaz de usuario final.

```bash
# En la Raspberry Pi (versión optimizada: frame-skipping, menor resolución)
python3 main_rpi.py

# En la PC, para pruebas rápidas del pipeline de detección
python3 main_pc.py
```

---

## 5. Estructura relevante del repositorio

```
model/
├── add_pose.py                    # Recolección de posturas (paso 1, entorno shpd)
├── Keypoint_model_training.ipynb  # Entrenamiento + conversión a TFLite (paso 2, entorno tf25env)
├── new_pose_data.csv              # Dataset acumulado de posturas
├── keypoint_classifier_label.csv  # Nombres de las clases, en el mismo orden que sus IDs
├── keypoint_classifier.keras      # Último modelo entrenado (formato Keras)
├── keypoint_classifier.tflite     # Modelo exportado, listo para la Raspberry Pi
├── pose_landmarker_full.task      # Modelo de MediaPipe usado por add_pose.py
└── test/                          # Fixture de prueba del pipeline (opcional, ver Paso 2)
    ├── test.py                    # Prueba del conversor TFLite
    ├── interpreter.py             # Prueba de carga con tflite_runtime
    ├── new_pose_data_test.csv     # Dataset de prueba (6 clases genéricas)
    ├── keypoint_classifier_label_test.csv
    └── keypoint_classifier_test.tflite

mp_utils/         # Detección de pose en inferencia (API Solutions, para main_pc.py / main_rpi.py)
neural_network/   # Carga el .tflite y clasifica la postura (tflite_runtime)
instructions/     # Buffer de gestos e instrucciones derivadas de la postura detectada
gui/              # Ventana de visualización (cámara + postura detectada)

main_pc.py        # Punto de entrada para pruebas en PC
main_rpi.py       # Punto de entrada optimizado para la Raspberry Pi 3
config_pose.json  # Umbrales de confianza, tamaño de ventana, etc.
docs/             # Guías de arquitectura e instalación en Raspberry Pi
```

---

## 6. Las 12 posturas actuales

Definidas en `model/keypoint_classifier_label.csv`, en este orden (clase 0 a 11):

1. Tronco flexionado
2. Tronco extendido
3. Tronco inclinado lateral izquierda
4. Tronco inclinado lateral derecho
5. Mentón en mano
6. Piernas cruzadas
7. Rodillas elevadas o muy bajas
8. Elevación escapular
9. Antebrazo sin apoyo
10. Cabeza adelantada
11. Cifosis torácica aumentada
12. Pelvis adelantada respecto respaldo

---

## 7. Problemas comunes

**`ModuleNotFoundError: No module named 'cv2'` al correr `add_pose.py`**
Estás usando un Python sin el entorno `shpd` activado (o `shpd` no tiene `opencv-python` instalado). Activá el entorno correcto — sección 3.1 — y volvé a intentar.

**El `.tflite` no carga en la Raspberry Pi / da error de versión de operadores**
Casi siempre significa que se entrenó y convirtió fuera de `tf25env` (con una versión de TensorFlow distinta a 2.5.0). Repetí el paso 2 dentro de `tf25env`.
