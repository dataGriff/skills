"""Meeting room booking domain used by the BDD eval tasks. Do not modify."""


class BookingRefused(Exception):
    """Raised when a booking cannot be made."""

    def __init__(self, reason):
        super().__init__(reason)
        self.reason = reason


class RoomSchedule:
    def __init__(self):
        self.rooms = {}
        self.bookings = {}  # (room, time) -> booker

    def add_room(self, name, capacity):
        self.rooms[name] = int(capacity)

    def book(self, booker, room, time, attendees=1):
        if room not in self.rooms:
            raise BookingRefused("unknown room")
        if (room, time) in self.bookings:
            raise BookingRefused("slot taken")
        if attendees > self.rooms[room]:
            raise BookingRefused("over capacity")
        self.bookings[(room, time)] = booker

    def is_free(self, room, time):
        return (room, time) not in self.bookings
