from tflite_runtime.interpreter import Interpreter

interpreter = Interpreter(model_path="keypoint_classifier.tflite")
interpreter.allocate_tensors()

print("Interpreter cargado correctamente ✅")

