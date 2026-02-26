class Room:
    def __init__(self, room = None, description = "Unknown", north = None, east = None, south = None, west = None, open = 0):
        self.room = room
        self.description = description
        self.north = north
        self.south = south
        self.east = east
        self.west = west
        self.open = open

if __name__ == '__main__':
    import json

    room_list = []

    with open("lab04-camel\\rooms.json", "r", encoding='utf-8') as file:
        room_information = json.load(file)

    #print(room_information)

    for room in room_information:
        room_list.append(Room(room["number"], room["description"], room["north"], room["east"], room["south"], room["west"], room["open"]))

    current_room = 0
    done = False
    next_room = None

    while not done:
        print("\n"+room_list[current_room].description)
        answer = input("\nWhat do you want to do? ")
        if answer[0].lower() == 'n':
            next_room = room_list[current_room].north
        elif answer[0].lower() == 'e':
            next_room = room_list[current_room].east
        elif answer[0].lower() == 's':
            next_room = room_list[current_room].south
        elif answer[0].lower() == 'w':
            next_room = room_list[current_room].west
        
        if(next_room["next_room"] != -1):
            if room_list[next_room["next_room"]].open == 1: current_room = next_room["next_room"]
            else: print("Esa puerta está bloqueada")
        else:
            if next_room["message"] != "": print(next_room["message"])
            else: print("No puedes ir por ahí")