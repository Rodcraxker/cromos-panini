import sys
print("Rutas de búsqueda de Python:")
for path in sys.path:
    print(path)

import mediapipe as mp
print("\nVersión de mediapipe:")
print(mp.__version__)
print("\nUbicación de mediapipe:")
print(mp.__file__)