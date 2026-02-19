from pathlib import Path
import random

def leer_opcion(mensaje)->int:
    """
    OBJ: Devuelve el entero correspondiente a la opción escogida
    """
    pass

def orden_aleatorio(longitud:int)->list:
    lista_ordenada = list(range(longitud))
    return random.sample(lista_ordenada, len(lista_ordenada))

def options(longitud:int)->list:
    opciones = []
    for i in range(longitud):
        opciones += [chr(97 + i)+") "]
    return opciones

def extraer_preguntas(pregunta:str)->dict:
    """
    OBJ: Extrae los datos del archivo y los organiza en una lista de diccionarios
    """
    estructura = []
    for line in (preguntas):
        datos = line.split('|')
        estructura += [{"pregunta": datos[0], "correcta": datos[1], "opciones": datos[1:]}]
    return estructura

def juego(preguntas: str)->None:
    puntos = 0
    list_preguntas = extraer_preguntas(preguntas)
    for i in orden_aleatorio(len(list_preguntas)):
        print(list_preguntas[i]["pregunta"])
        opciones = list_preguntas[i]["opciones"]
        letras = options(len(opciones))
        l = 0
        for j in orden_aleatorio(len(opciones)): 
            print(f"\t{letras[l]}{opciones[j].rstrip()}")
            l += 1
        
        
            


with open("preguntas.txt", 'r', encoding='utf-8') as preguntas:
    juego(preguntas)
