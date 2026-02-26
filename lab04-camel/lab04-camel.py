class Room:
    def __init__(self, room = None, description = "Unknown", north = None, east = None, south = None, west = None):
        self.room = room
        self.description = description
        self.north = north
        self.east = east
        self.west = west

if __name__ == '__main__':
    import json

    room_list = []

    room_information = json.load(open("lab04-camel/rooms.json", 'r', encoding='utf-8'))
    print(room_information)
    """for room in room_information():
        room_list.append(Room(room["number"], room["description"], room["north"], room["east"], room["south"], room["west"]))"""

    current_room = 0
    print(room_list)