import tensorflow as tf
print("TF version:", tf.__version__)

model = tf.keras.Sequential([
    tf.keras.layers.Input((36,)),
    tf.keras.layers.Dense(16, activation='relu'),
    tf.keras.layers.Dense(5, activation='softmax')
])

converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS]
converter.experimental_new_converter = False
converter._experimental_lower_tensor_list_ops = False

tflite_model = converter.convert()
print("✅ Modelo convertido correctamente")
