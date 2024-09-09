"""
Export the Users class
"""

import aikido_zen.helpers.get_current_unixtime_ms as t


class Users:
    """
    Class that holds users for the background process
    """

    def __init__(self, max_entries=1000):
        self.max_entries = max_entries
        self.users = {}

    def add_user(self, user):
        """Store a user"""
        user_id = user["id"]
        current_time = t.get_unixtime_ms()

        existing = self.users.get(user_id)
        if existing:
            existing["name"] = user.get("name")
            existing["lastIpAddress"] = user.get("lastIpAddress")
            existing["lastSeenAt"] = current_time
            return

        if len(self.users) >= self.max_entries:
            # Remove the first added user (FIFO)
            first_added_key = next(iter(self.users))
            del self.users[first_added_key]

        self.users[user_id] = {
            "id": user_id,
            "name": user.get("name"),
            "lastIpAddress": user.get("lastIpAddress"),
            "firstSeenAt": current_time,
            "lastSeenAt": current_time,
        }

    def as_array(self):
        """
        Give all user entries back as an array
        """
        return [
            {
                "id": user["id"],
                "name": user["name"],
                "lastIpAddress": user["lastIpAddress"],
                "firstSeenAt": user["firstSeenAt"],
                "lastSeenAt": user["lastSeenAt"],
            }
            for user in self.users.values()
        ]

    def clear(self):
        """Clear out all users"""
        self.users.clear()
