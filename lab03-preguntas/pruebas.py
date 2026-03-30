#prueba
import random
lista = list(range(5))
print(lista)

lista_desordenada = random.sample(lista, len(lista))
print(lista_desordenada)

def opciones(longitud:int)->list:
    opciones = []
    for i in range(longitud):
        opciones += [chr(97 + i)]
    return opciones

print(opciones(4))

