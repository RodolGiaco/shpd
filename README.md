
---

# **SmartHealthyPostureDetector**  
### **Detector de Postura Inteligente utilizando Redes Neuronales y Visión Artificial**

Este proyecto se enfoca en la detección inteligente de posturas corporales mediante **redes neuronales** y **visión artificial**. Utilizando **Mediapipe** para detectar puntos clave del torso y las extremidades, se recolectan datos que luego son entrenados con un modelo de **TensorFlow** para clasificar posturas. El proyecto es adaptable a múltiples contextos, como ergonomía, corrección postural o seguimiento de ejercicios físicos.

---

## **Tabla de Contenidos**
- [Requisitos del Proyecto](#requisitos-del-proyecto)
- [Descripción de los Puntos Exportados](#descripción-de-los-puntos-exportados)
- [Guía de Uso](#guía-de-uso)
  - [Paso 1: Exportar Nuevos Puntos](#paso-1-exportar-nuevos-puntos)
  - [Paso 2: Entrenar el Modelo](#paso-2-entrenar-el-modelo)
  - [Paso 3: Realizar Pruebas del Modelo](#paso-3-realizar-pruebas-del-modelo)
- [Documentación](#documentación)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Licencia](#licencia)

---

## **Requisitos del Proyecto**

Asegúrate de tener las siguientes dependencias instaladas:

- **Python 3.8+**
- **TensorFlow 2.9+**
- **OpenCV**: `pip install opencv-python`
- **Mediapipe**: `pip install mediapipe`
- **NumPy**: `pip install numpy`
- **Jupyter Notebook**: `pip install notebook`
- **TensorBoard** (opcional): `pip install tensorboard`

Para instalar todas las dependencias de una vez, ejecuta:

```bash
pip install -r requirements.txt
```

---

## **Descripción de los Puntos Exportados**

El sistema captura **12 puntos clave** (X, Y, Z) del torso y las extremidades del cuerpo, excluyendo las manos, pies y rostro. Estos puntos se usan como entrada para entrenar el modelo.

- **Puntos exportados:**
  - **Hombros**: Izquierdo y derecho (11 y 12)
  - **Codos**: Izquierdo y derecho (13 y 14)
  - **Muñecas**: Izquierda y derecha (15 y 16)
  - **Caderas**: Izquierda y derecha (23 y 24)
  - **Rodillas**: Izquierda y derecha (25 y 26)
  - **Tobillos**: Izquierdo y derecho (27 y 28)

Cada entrada en el archivo **CSV** tiene la siguiente estructura:

```csv
[clase, X1, Y1, Z1, X2, Y2, Z2, ..., X12, Y12, Z12]
```

---

## **Guía de Uso**

### **Paso 1: Exportar Nuevos Puntos**

Para recolectar nuevos puntos y exportarlos a un archivo **CSV**, utiliza el archivo **`add_pose.py`**.

#### **Instrucciones:**
1. Asegúrate de que tu cámara esté conectada y funcionando.
2. Ejecuta el siguiente comando:

   ```bash
   python3 model/add_pose.py
   ```

3. **Controles dentro del script:**
   - **Espacio**: Guarda la postura actual en el CSV.
   - **n**: Avanza a la siguiente clase de postura.
   - **p**: Regresa a la clase anterior.
   - **q**: Sale del programa.

4. Los datos recolectados se guardan en **`model/new_pose_data.csv`**.

---

### **Paso 2: Entrenar el Modelo**

El entrenamiento del modelo se realiza utilizando el archivo **`Keypoint_model_training.ipynb`**.

#### **Instrucciones:**
1. Asegúrate de que **`new_pose_data.csv`** se encuentre en la carpeta `model/`.
2. Ejecuta el siguiente comando para abrir el notebook:

   ```bash
   jupyter notebook model/Keypoint_model_training.ipynb
   ```

3. Sigue las instrucciones en el notebook para:
   - Cargar los datos de entrenamiento.
   - Definir y entrenar el modelo.
   - Evaluar el desempeño del modelo.

4. **(Opcional)**: Para visualizar el progreso del entrenamiento, utiliza **TensorBoard**:

   ```bash
   tensorboard --logdir=logs/hparam_tuning
   ```

   Luego abre [http://localhost:6006](http://localhost:6006) en tu navegador.

---

### **Paso 3: Realizar Pruebas del Modelo**

Una vez entrenado, puedes probar el modelo utilizando **`main.py`**.

#### **Instrucciones:**
1. Asegúrate de que el modelo entrenado esté en **`model/keypoint_classifier.tflite`**.
2. Ejecuta el siguiente comando:

   ```bash
   python3 main.py
   ```

3. El script **`main.py`** cargará el modelo y realizará inferencias en tiempo real utilizando la cámara.

---

## **Documentación**

### **English Documentation / Documentación en Inglés**

For comprehensive documentation in English, please refer to:

- **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - Complete API reference with examples and usage instructions
- **[MODULE_REFERENCE.md](MODULE_REFERENCE.md)** - Detailed documentation for each module
- **[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)** - Architecture overview and guide for extending the system
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Quick reference guide with common code snippets

These documents include:
- Detailed API documentation for all public functions and classes
- Code examples and usage patterns
- Performance tuning guidelines
- Testing and debugging instructions
- Extension and customization guides

---

## **Estructura del Proyecto**

```plaintext
SmartHealthyPostureDetector/
│
├── gui/
│   ├── gui.py                 # Interfaz gráfica
│   ├── __init__.py
│
├── instructions/
│   ├── gesture_buffer.py      # Almacenamiento de gestos
│   ├── gesture_instructions.py
│   └── __init__.py
│
├── model/
│   ├── add_pose.py                       # Script para recolectar datos
│   ├── keypoint_classifier_label.csv     # Etiquetas de las clases
│   ├── keypoint_classifier.keras         # Modelo entrenado en formato Keras
│   ├── keypoint_classifier.tflite        # Modelo en formato TFLite para inferencia
│   ├── Keypoint_model_training.ipynb     # Notebook para entrenar el modelo
│   ├── new_pose_data.csv                 # Archivo CSV con datos recolectados
│   ├── old_gestures.csv                  # CSV con gestos anteriores
│   ├── pose_landmarker_full.task         # Modelo de Mediapipe para poses completas
│   ├── pose_landmarker_heavy.task        # Modelo pesado de Mediapipe
│
├── mp_utils/
│   ├── mp_pose.py                        # Utilidad para trabajar con Mediapipe
│   ├── pose_posture.py                   # Funciones relacionadas con posturas
│   └── __init__.py
│
├── neural_network/
│   ├── pose_recognition.py               # Red neuronal para reconocimiento de poses
│   └── __init__.py
│
├── config_pose.json                      # Configuración de parámetros de pose
├── main.py                               # Script principal para pruebas
├── README.md                             # Documentación del proyecto
└── requirements.txt                      # Lista de dependencias
```

---

## **Licencia**

Este proyecto está licenciado bajo la **MIT License**. Consulta el archivo `LICENSE` para más detalles.

---

## **Conclusiones**

Con **SmartHealthyPostureDetector**, puedes capturar, entrenar y probar modelos para detectar posturas corporales de manera inteligente y precisa. La herramienta permite adaptar el sistema a distintos escenarios, desde ergonomía hasta corrección postural en tiempo real.

---